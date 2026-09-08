"""
Commission Data Prep Pipeline
Meridian Risk Technologies | FP&A - Sales Compensation

Purpose
-------
Raw bookings data lands from Salesforce exports with the usual mess: sign
errors, whitespace, case mismatches, nulls, and duplicate rows. This pipeline
replicates an Alteryx-style workflow -- discrete, auditable steps chained
together -- built in Python/pandas so it can run anywhere without a
designer license, while keeping the same step-by-step structure a workflow
canvas would show:

    Input Data  ->  Data Cleanse  ->  Join (Roster)  ->  Formula (Commission)
               ->  Summarize  ->  Output (clean tables for reporting)

Each step is its own function with a single responsibility, logs what it
did, and can be unit-tested in isolation -- the same discipline an Alteryx
module enforces tool-by-tool.

Run:  python3 pipeline.py
"""
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
OUT_DIR = DATA_DIR / "clean"
OUT_DIR.mkdir(exist_ok=True)

LOG = []


def log(step, message):
    LOG.append(f"[{step}] {message}")
    print(f"[{step}] {message}")


# ---------------------------------------------------------------------------
# STEP 1 — INPUT DATA (three sources, mirrors three Input Data tools)
# ---------------------------------------------------------------------------
def load_inputs():
    deals = pd.read_csv(DATA_DIR / "deals_raw.csv")
    roster = pd.read_csv(DATA_DIR / "sales_roster.csv")
    plan = pd.read_csv(DATA_DIR / "commission_plan_rules.csv")
    log("INPUT", f"Loaded {len(deals)} deal records, {len(roster)} reps, {len(plan)} plan rules")
    return deals, roster, plan


# ---------------------------------------------------------------------------
# STEP 2 — DATA CLEANSE (equivalent to an Alteryx Data Cleansing + Filter tool)
# ---------------------------------------------------------------------------
def cleanse_deals(deals: pd.DataFrame) -> pd.DataFrame:
    start_count = len(deals)
    issues = {}

    # 2a. Normalize text fields: trim whitespace, standardize case
    deals["rep_id"] = deals["rep_id"].str.strip().str.upper()
    deals["deal_type"] = deals["deal_type"].str.strip().str.title()
    deals["customer_name"] = deals["customer_name"].str.strip()
    deals["deal_type"] = deals["deal_type"].replace({"Renewal": "Renewal"})  # normalize post-title-case

    # 2b. Flag and correct sign errors (ARR should never be negative)
    sign_errors = deals["arr_amount"] < 0
    issues["sign_errors_corrected"] = int(sign_errors.sum())
    deals.loc[sign_errors, "arr_amount"] = deals.loc[sign_errors, "arr_amount"].abs()

    # 2c. Handle missing ARR — drop, since a commission engine cannot estimate a
    #     missing dollar figure without risking overpayment or underpayment
    missing_arr = deals["arr_amount"].isna()
    issues["missing_arr_dropped"] = int(missing_arr.sum())
    deals = deals.loc[~missing_arr].copy()

    # 2d. Remove exact duplicate records (same deal captured twice on export)
    before = len(deals)
    deals = deals.drop_duplicates(subset=["rep_id", "close_date", "deal_type", "customer_name", "arr_amount"])
    issues["duplicates_removed"] = before - len(deals)

    # 2e. Type conversions
    deals["close_date"] = pd.to_datetime(deals["close_date"])
    deals["arr_amount"] = deals["arr_amount"].astype(float)
    deals["quarter"] = deals["close_date"].dt.quarter.map({1: "Q1", 2: "Q2"})
    deals["month"] = deals["close_date"].dt.strftime("%Y-%m")

    for k, v in issues.items():
        log("CLEANSE", f"{k}: {v}")
    log("CLEANSE", f"Record count {start_count} -> {len(deals)}")
    return deals.reset_index(drop=True)


# ---------------------------------------------------------------------------
# STEP 3 — JOIN (blend deal-level data with the sales roster, like an
#           Alteryx Join tool keyed on rep_id)
# ---------------------------------------------------------------------------
def join_roster(deals: pd.DataFrame, roster: pd.DataFrame) -> pd.DataFrame:
    merged = deals.merge(roster, on="rep_id", how="left", indicator=True)
    unmatched = merged["_merge"].eq("left_only").sum()
    if unmatched:
        log("JOIN", f"WARNING: {unmatched} deal(s) had no matching rep in roster")
    merged = merged.drop(columns="_merge")
    log("JOIN", f"Blended {len(merged)} deals with roster attributes (segment, quota, region)")
    return merged


# ---------------------------------------------------------------------------
# STEP 4 — FORMULA: tiered commission calculation (Alteryx Formula/Multi-Row
#           equivalent). Mirrors the same marginal-bracket logic built into
#           the Excel calc engine, so both artifacts agree.
# ---------------------------------------------------------------------------
def calculate_commission(merged: pd.DataFrame, plan: pd.DataFrame) -> pd.DataFrame:
    new_biz_rates = plan[plan.applies_to == "New Business"].sort_values("tier")
    upsell_rate = plan.loc[plan.applies_to == "Upsell", "rate"].iloc[0]
    renewal_rate = plan.loc[plan.applies_to == "Renewal", "rate"].iloc[0]

    # Aggregate New Business ARR per rep per quarter to determine attainment tier
    new_biz = merged[merged.deal_type == "New Business"]
    new_biz_by_rep_q = (new_biz.groupby(["rep_id", "quarter"])["arr_amount"]
                        .sum().rename("new_biz_arr_q").reset_index())

    roster_quota = merged[["rep_id", "quarterly_quota_new_arr"]].drop_duplicates()
    attainment = new_biz_by_rep_q.merge(roster_quota, on="rep_id", how="left")
    attainment["attainment_pct"] = attainment["new_biz_arr_q"] / attainment["quarterly_quota_new_arr"]

    def marginal_new_biz_commission(new_arr, quota):
        """Marginal tiered payout — dollars in each bracket earn that bracket's rate."""
        tier1_cap = quota * 1.00
        tier2_cap = quota * 1.25
        tier1_amt = min(new_arr, tier1_cap)
        tier2_amt = max(min(new_arr, tier2_cap) - tier1_cap, 0)
        tier3_amt = max(new_arr - tier2_cap, 0)
        r1 = new_biz_rates.iloc[0]["rate"]
        r2 = new_biz_rates.iloc[1]["rate"]
        r3 = new_biz_rates.iloc[2]["rate"]
        return tier1_amt * r1 + tier2_amt * r2 + tier3_amt * r3

    attainment["new_biz_commission_q"] = attainment.apply(
        lambda r: marginal_new_biz_commission(r["new_biz_arr_q"], r["quarterly_quota_new_arr"]), axis=1
    )

    # Deal-level commission: New Business gets its share of the quarter's blended
    # marginal payout (proportional to deal size); Upsell/Renewal are flat-rate per deal
    merged = merged.merge(
        attainment[["rep_id", "quarter", "new_biz_arr_q", "attainment_pct", "new_biz_commission_q"]],
        on=["rep_id", "quarter"], how="left"
    )

    def deal_commission(row):
        if row["deal_type"] == "New Business" and row["new_biz_arr_q"] > 0:
            share = row["arr_amount"] / row["new_biz_arr_q"]
            return round(share * row["new_biz_commission_q"], 2)
        elif row["deal_type"] == "Upsell":
            return round(row["arr_amount"] * upsell_rate, 2)
        elif row["deal_type"] == "Renewal":
            return round(row["arr_amount"] * renewal_rate, 2)
        return 0.0

    merged["commission_amount"] = merged.apply(deal_commission, axis=1)
    log("FORMULA", f"Commission calculated for {len(merged)} deals "
                    f"(total: ${merged['commission_amount'].sum():,.0f})")
    return merged, attainment


# ---------------------------------------------------------------------------
# STEP 5 — SUMMARIZE (rep-quarter and company-month rollups, like Alteryx
#           Summarize tools feeding a reporting layer)
# ---------------------------------------------------------------------------
def summarize(merged: pd.DataFrame, attainment: pd.DataFrame, roster: pd.DataFrame) -> dict:
    by_rep_q = (merged.groupby(["rep_id", "rep_name", "segment", "region", "quarter"])
                .agg(bookings_arr=("arr_amount", "sum"),
                     commission=("commission_amount", "sum"),
                     deal_count=("deal_id", "count"))
                .reset_index())
    by_rep_q = by_rep_q.merge(
        attainment[["rep_id", "quarter", "attainment_pct"]], on=["rep_id", "quarter"], how="left"
    )

    by_month = (merged.groupby("month")
                .agg(bookings_arr=("arr_amount", "sum"),
                     commission_expense=("commission_amount", "sum"),
                     deal_count=("deal_id", "count"))
                .reset_index())

    by_type = (merged.groupby(["quarter", "deal_type"])
               .agg(arr=("arr_amount", "sum"), commission=("commission_amount", "sum"))
               .reset_index())

    # Net Revenue Retention proxy: renewed ARR vs. the book it renewed against
    nrr_rows = []
    for _, rep in roster.iterrows():
        renewals = merged[(merged.rep_id == rep.rep_id) & (merged.deal_type == "Renewal")]
        renewed_arr = renewals["arr_amount"].sum()
        # book eligible to renew in the period ~ starting_book * 0.5 (two quarters at ~25%/qtr)
        eligible_book = rep["starting_book_arr"] * 0.5
        nrr = renewed_arr / eligible_book if eligible_book > 0 else np.nan
        nrr_rows.append({"rep_id": rep.rep_id, "rep_name": rep.rep_name, "segment": rep.segment,
                          "renewed_arr": renewed_arr, "eligible_book_arr": eligible_book, "nrr": nrr})
    nrr_df = pd.DataFrame(nrr_rows)

    log("SUMMARIZE", f"Built rep-quarter ({len(by_rep_q)} rows), monthly ({len(by_month)} rows), "
                      f"deal-type ({len(by_type)} rows), and NRR ({len(nrr_df)} rows) rollups")
    return {"by_rep_q": by_rep_q, "by_month": by_month, "by_type": by_type, "nrr": nrr_df}


# ---------------------------------------------------------------------------
# STEP 6 — OUTPUT DATA
# ---------------------------------------------------------------------------
def write_outputs(merged, summaries):
    merged.to_csv(OUT_DIR / "deals_clean_with_commission.csv", index=False)
    summaries["by_rep_q"].to_csv(OUT_DIR / "summary_by_rep_quarter.csv", index=False)
    summaries["by_month"].to_csv(OUT_DIR / "summary_by_month.csv", index=False)
    summaries["by_type"].to_csv(OUT_DIR / "summary_by_deal_type.csv", index=False)
    summaries["nrr"].to_csv(OUT_DIR / "summary_nrr.csv", index=False)
    with open(OUT_DIR / "pipeline_run_log.txt", "w") as f:
        f.write("\n".join(LOG))
    log("OUTPUT", f"Wrote 5 clean output files to {OUT_DIR}")


def run():
    deals, roster, plan = load_inputs()
    clean_deals = cleanse_deals(deals)
    merged = join_roster(clean_deals, roster)
    merged, attainment = calculate_commission(merged, plan)
    summaries = summarize(merged, attainment, roster)
    write_outputs(merged, summaries)
    log("DONE", "Pipeline complete.")


if __name__ == "__main__":
    run()
