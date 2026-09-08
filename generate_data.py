"""
Synthetic data generator — Meridian Risk Technologies commission dataset.

Meridian Risk Technologies is a fictional B2B SaaS company selling cloud-based
policy management software to insurance agencies and brokers (same market
space as the target JD, built as an original company so the project stands
on its own).

This script is the single source of truth. The Excel model, the Python ETL
pipeline, and the dashboard all consume its output, so every number in every
deliverable traces back to the same rows.
"""
import numpy as np
import pandas as pd
from datetime import date, timedelta

rng = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# 1. Sales roster & quota
# ---------------------------------------------------------------------------
FIRST_NAMES = ["Maria","James","Priya","David","Sofia","Marcus","Elena","Tyler",
               "Aisha","Ryan","Natalie","Omar","Grace","Kevin","Lucia"]
LAST_NAMES = ["Chen","Okafor","Patel","Nguyen","Rossi","Bennett","Kowalski",
              "Alvarez","Kim","Sullivan","Reyes","Fischer","Adeyemi","Novak","Larsen"]

segments = (["SMB"] * 6) + (["Mid-Market"] * 6) + (["Enterprise"] * 3)
base_quota = {"SMB": 150_000, "Mid-Market": 300_000, "Enterprise": 600_000}
regions = ["Central", "East", "West"]

reps = []
for i, seg in enumerate(segments):
    rep_id = f"R{i+1:03d}"
    name = f"{FIRST_NAMES[i]} {LAST_NAMES[i]}"
    # quota variance +/-12% to reflect territory differences
    q_variance = rng.uniform(0.88, 1.12)
    quarterly_quota = round(base_quota[seg] * q_variance / 1000) * 1000
    hire_year = rng.choice([2022, 2023, 2024, 2025], p=[0.35, 0.30, 0.20, 0.15])
    hire_month = rng.integers(1, 13)
    hire_date = date(int(hire_year), int(hire_month), 1)
    # existing book of business (drives renewal base / NRR)
    tenure_years = max((date(2026,1,1) - hire_date).days / 365, 0.1)
    book_multiplier = {"SMB": 220_000, "Mid-Market": 480_000, "Enterprise": 950_000}[seg]
    starting_book = round(book_multiplier * min(tenure_years / 2.0, 1.4) * rng.uniform(0.85, 1.15) / 1000) * 1000
    reps.append({
        "rep_id": rep_id,
        "rep_name": name,
        "segment": seg,
        "region": rng.choice(regions),
        "hire_date": hire_date.isoformat(),
        "quarterly_quota_new_arr": quarterly_quota,
        "starting_book_arr": starting_book,
    })

reps_df = pd.DataFrame(reps)

# ---------------------------------------------------------------------------
# 2. Deal-level bookings, Jan–Jun 2026 (two full quarters -> Q3 forecast base)
# ---------------------------------------------------------------------------
CUSTOMER_PREFIXES = ["Harborview","Summit","Coastal","Redwood","Granite","Beacon",
    "Anchor","Meadowbrook","Pinnacle","Sterling","Lakeside","Fieldstone","Ironwood",
    "Bridgeway","Northgate","Cedarline","Windham","Prairie","Highmark","Cobalt",
    "Vantage","Millbrook","Wrenfield","Ashford","Clearwater","Brookhaven","Stonebridge",
    "Hillcrest","Overlook","Riverbend"]
CUSTOMER_SUFFIXES = ["Insurance Group","Agency Partners","Underwriters","Risk Advisors",
    "Insurance Brokers","Mutual Agency","Coverage Partners","Insurance Solutions"]

product_lines = ["Policy Admin Core", "Claims Module", "Analytics Add-On", "Client Portal"]

months = pd.date_range("2026-01-01", "2026-06-30", freq="MS")
deal_rows = []
deal_counter = 1

for _, rep in reps_df.iterrows():
    seg = rep["segment"]
    q1_quota = rep["quarterly_quota_new_arr"]
    # per-rep skill/performance factor -> creates realistic spread of over/under performers
    perf_factor = rng.normal(1.0, 0.22)
    perf_factor = max(perf_factor, 0.45)

    for q_num, q_months in enumerate([months[0:3], months[3:6]]):
        # New business: 2-5 deals per quarter depending on segment
        n_new_deals = {"SMB": rng.integers(3, 7), "Mid-Market": rng.integers(2, 5),
                       "Enterprise": rng.integers(1, 3)}[seg]
        target_new_arr = q1_quota * perf_factor * rng.uniform(0.85, 1.15)
        if n_new_deals > 0:
            weights = rng.dirichlet(np.ones(n_new_deals))
            for w in weights:
                close_month = rng.choice(q_months)
                close_day = rng.integers(1, 28)
                close_date = pd.Timestamp(close_month) + pd.Timedelta(days=int(close_day))
                arr_amt = max(round(target_new_arr * w / 500) * 500, 3000)
                deal_rows.append({
                    "deal_id": f"D{deal_counter:05d}", "rep_id": rep["rep_id"],
                    "close_date": close_date.date().isoformat(), "deal_type": "New Business",
                    "customer_name": f"{rng.choice(CUSTOMER_PREFIXES)} {rng.choice(CUSTOMER_SUFFIXES)}",
                    "arr_amount": int(arr_amt),
                    "product_line": rng.choice(product_lines, p=[0.55,0.20,0.15,0.10]),
                })
                deal_counter += 1

        # Upsell/expansion: 0-3 deals per quarter, smaller ARR, tied to existing book
        n_upsell = rng.integers(0, 4)
        for _ in range(n_upsell):
            close_month = rng.choice(q_months)
            close_day = rng.integers(1, 28)
            close_date = pd.Timestamp(close_month) + pd.Timedelta(days=int(close_day))
            arr_amt = max(round(rep["starting_book_arr"] * rng.uniform(0.03, 0.12) / 500) * 500, 2000)
            deal_rows.append({
                "deal_id": f"D{deal_counter:05d}", "rep_id": rep["rep_id"],
                "close_date": close_date.date().isoformat(), "deal_type": "Upsell",
                "customer_name": f"{rng.choice(CUSTOMER_PREFIXES)} {rng.choice(CUSTOMER_SUFFIXES)}",
                "arr_amount": int(arr_amt),
                "product_line": rng.choice(product_lines, p=[0.30,0.30,0.30,0.10]),
            })
            deal_counter += 1

        # Renewals: book of business renews roughly 1/4 per quarter, with realistic churn
        renewal_base = rep["starting_book_arr"] * rng.uniform(0.22, 0.28)
        n_renewals = rng.integers(2, 6)
        if n_renewals > 0 and renewal_base > 0:
            weights = rng.dirichlet(np.ones(n_renewals))
            for w in weights:
                close_month = rng.choice(q_months)
                close_day = rng.integers(1, 28)
                close_date = pd.Timestamp(close_month) + pd.Timedelta(days=int(close_day))
                # net retention rate per renewal: mostly flat/slight growth, occasional shrink
                nrr_factor = rng.choice([0.80, 0.92, 1.00, 1.05, 1.10, 1.18],
                                         p=[0.08, 0.14, 0.30, 0.25, 0.15, 0.08])
                arr_amt = max(round(renewal_base * w * nrr_factor / 500) * 500, 1500)
                deal_rows.append({
                    "deal_id": f"D{deal_counter:05d}", "rep_id": rep["rep_id"],
                    "close_date": close_date.date().isoformat(), "deal_type": "Renewal",
                    "customer_name": f"{rng.choice(CUSTOMER_PREFIXES)} {rng.choice(CUSTOMER_SUFFIXES)}",
                    "arr_amount": int(arr_amt),
                    "product_line": rng.choice(product_lines, p=[0.55,0.20,0.15,0.10]),
                })
                deal_counter += 1

deals_df = pd.DataFrame(deal_rows).sort_values("close_date").reset_index(drop=True)

# Inject a small number of realistic data-quality issues for the ETL step to clean
# (this is what makes the Alteryx-style pipeline meaningful rather than decorative)
dirty_idx = rng.choice(deals_df.index, size=6, replace=False)
deals_df.loc[dirty_idx[0], "arr_amount"] = -deals_df.loc[dirty_idx[0], "arr_amount"]  # sign error
deals_df.loc[dirty_idx[1], "customer_name"] = deals_df.loc[dirty_idx[1], "customer_name"] + "   "  # trailing space
deals_df.loc[dirty_idx[2], "rep_id"] = deals_df.loc[dirty_idx[2], "rep_id"].lower()  # case mismatch
deals_df.loc[dirty_idx[3], "arr_amount"] = np.nan  # missing value
dupe_row = deals_df.loc[dirty_idx[4]].copy()
deals_df = pd.concat([deals_df, pd.DataFrame([dupe_row])], ignore_index=True)  # duplicate record
deals_df.loc[dirty_idx[5], "deal_type"] = "renewal "  # inconsistent casing/whitespace

# ---------------------------------------------------------------------------
# 3. Commission plan rules (the policy the calc engine implements)
# ---------------------------------------------------------------------------
plan_rules = pd.DataFrame([
    {"tier": 1, "attainment_floor": 0.00, "attainment_ceiling": 1.00, "rate": 0.08,
     "applies_to": "New Business", "note": "Base rate up to 100% of quarterly quota"},
    {"tier": 2, "attainment_floor": 1.00, "attainment_ceiling": 1.25, "rate": 0.10,
     "applies_to": "New Business", "note": "Accelerator: 100%-125% of quota"},
    {"tier": 3, "attainment_floor": 1.25, "attainment_ceiling": 999, "rate": 0.12,
     "applies_to": "New Business", "note": "Accelerator: above 125% of quota"},
    {"tier": 0, "attainment_floor": 0, "attainment_ceiling": 999, "rate": 0.06,
     "applies_to": "Upsell", "note": "Flat rate on expansion ARR"},
    {"tier": 0, "attainment_floor": 0, "attainment_ceiling": 999, "rate": 0.03,
     "applies_to": "Renewal", "note": "Retention SPIF on renewed ARR"},
])

from pathlib import Path
OUT_DIR = Path(__file__).resolve().parent / "data"
OUT_DIR.mkdir(exist_ok=True)
reps_df.to_csv(OUT_DIR / "sales_roster.csv", index=False)
deals_df.to_csv(OUT_DIR / "deals_raw.csv", index=False)
plan_rules.to_csv(OUT_DIR / "commission_plan_rules.csv", index=False)

print("Reps:", len(reps_df))
print("Deals (incl. 6 dirty + 1 dupe):", len(deals_df))
print(deals_df["deal_type"].value_counts())
print("Total gross New Business ARR (dirty):", deals_df.loc[deals_df.deal_type=="New Business","arr_amount"].sum())
