# Meridian Commission Analytics Suite

FY26 sales commission calculation engine, data-prep pipeline, and analytics dashboards for a
fictional B2B SaaS company (Meridian Risk Technologies). Built as a portfolio project — see
`case_study.md` for the full write-up.

## What's in this folder

| File | What it is | How to open it |
|---|---|---|
| `index.html` | Same file as below — lets GitHub Pages serve the dashboard at the repo's root URL | Any web browser |
| `Meridian_Commission_Model.xlsx` | 10-tab Excel FP&A model — commission calc engine, forecast, scenario planner, audit exceptions, budget vs actual, dashboard | Excel / LibreOffice Calc |
| `Meridian_Commission_Dashboard.html` | Interactive Tableau-style dashboard — 7 tabs including scenario planner, exceptions, budget vs actual | Any web browser |
| `Commission_Plan_Quick_Reference.pdf` | One-page, plain-language commission plan summary for Sales reps | Any PDF viewer |
| `Rep_Commission_Statements_H1_FY26.pdf` | Individual H1 commission statement per rep, one page each (15 total) | Any PDF viewer |
| `pipeline_workflow_diagram.png` | Visual of the data-prep pipeline | Any image viewer |
| `pipeline.py` | Python (pandas) data-prep pipeline | Terminal — see setup below |
| `generate_data.py` | Regenerates the synthetic source dataset | Terminal — see setup below |
| `data/*.csv` | Source data, including the hypothetical FY26 budget | — |
| `case_study.md` | Full project write-up | Any text editor / Markdown viewer |
| `requirements.txt` | Python dependencies for `pipeline.py` | Used by `pip install` |

## What's new in this version

Five additions beyond the original commission-calc-and-reporting build, each aimed at a specific
part of the job description this project targets:

1. **Scenario Planner** (Excel tab + dashboard tab with live sliders) — what-if modeling on plan
   rates and quota, holding actual bookings behavior constant. Verified to exactly reproduce the
   base plan ($916,935) at default settings, and to shift correctly in both directions when
   inputs change.
2. **Audit & Exceptions** (Excel tab + dashboard tab) — automated flags for rep-quarter attainment
   outliers (accelerator review, coaching flag, retention gap) and deal-level size outliers
   (2.5x+ a rep's typical deal for that type). The dashboard and Excel versions were built
   independently and flag the identical reps and deals.
3. **Budget vs. Actual** (Excel tab + dashboard tab) — a hypothetical FY26 budget compared
   month-by-month against actuals (Jan–Jun) and forecast (Jul–Sep), with honest basis labeling
   so a forecast month is never presented as if it were an actual.
4. **Commission Plan Quick Reference** (PDF) — a Sales-facing one-pager explaining the tiered
   plan in plain language with a worked example, aimed at the JD's "educate Sales on commission
   programs" requirement.
5. **Rep Commission Statements** (PDF) — an individual one-page H1 statement per rep (15 pages,
   one per rep), each showing their quarterly breakdown and full deal log.

## Live demo

Once pushed to GitHub with Pages enabled (Settings → Pages → Deploy from branch → `main` / root),
the dashboard is live at:

`https://YOUR-USERNAME.github.io/meridian-commission-analytics/`

## Quick start

**Excel model, dashboard, and PDFs need no setup** — just double-click them.

**Python pipeline:**
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 pipeline.py
```
Expected output ends with: `Commission calculated for 270 deals (total: $916,935)`

## Data integrity note

The commission math in this project was built three independent ways — Excel formulas, the
Python pipeline, and the dashboard's JavaScript — and all three tie out to the same totals
(H1 FY26 bookings ARR: $14,074,500; commission expense: $916,935). The Scenario Planner and
Exceptions logic were each cross-checked the same way between Excel and the dashboard. That's
intentional: it's the same cross-check discipline a real FP&A review would apply before a number
goes in front of leadership.
