# FY26 Sales Commission & FP&A Analytics — Project Case Study

**Independent portfolio project** | Built to demonstrate the technical scope of a Sr. Financial Analyst, FP&A role (sales compensation focus)

---

## The problem

A mid-size B2B SaaS company (modeled here as "Meridian Risk Technologies," a fictional insurtech vendor) is scaling its sales org past 15 reps across three segments. Commission is calculated by hand each month in a spreadsheet that wasn't built for it: tier lookups are entered manually per rep, there's no single source of truth for attainment, and finance can't answer "what will Q3 commission expense be?" without a multi-day reconciliation.

This project rebuilds that process end to end: a real (synthetic) dataset, a documented commission plan, an auditable calculation engine, a data-prep pipeline, and two reporting layers — one for finance to work in, one for leadership to read.

## What's in it

**1. Excel FP&A model** (`Meridian_Commission_Model.xlsx`)
Seven tabs: Cover, Commission Plan Rules, Sales Roster & Quotas, a 270-row deal-level Bookings Detail tab where commission is calculated line-by-line with live formulas (marginal tiered accelerator: 8% / 10% / 12% by attainment bracket, plus flat rates for upsell and renewal), a Rep-Quarter management-review summary, a Monthly Accrual & Q3 Forecast tab (linear trend), and an Executive Dashboard with KPI cards and four charts. Every number is a formula, not a hardcoded value — change a rate on the Plan Rules tab and the whole workbook recalculates. Verified with zero formula errors.

**2. Python data-prep pipeline** (`pipeline.py`)
A pandas-based pipeline structured the way an Alteryx workflow would be: Input Data → Data Cleanse → Join → Formula → Summarize → Output. It intentionally processes messy source data — sign errors, a null ARR value, a duplicate record, inconsistent casing — and logs exactly what it fixed at each step. A workflow diagram (`pipeline_workflow_diagram.svg/png`) visualizes the canvas.

**3. Interactive dashboard** (`Meridian_Commission_Dashboard.html`)
A Tableau-style analytics view built in HTML/JavaScript/Plotly: four tabs (Overview, Rep Performance, Deal Trends, Forecast), live Quarter and Segment filters, a sortable rep table, and the same Q3 forecast logic as the Excel model. Opens in any browser — no server or license required.

**4. This case study**, for walking someone through the "why," not just the "what."

## Why the numbers can be trusted

The commission logic was built **twice, independently** — once as Excel formulas, once as a Python pipeline — using the same marginal-tiered-bracket math but written by hand in two different tools. Both land on exactly the same totals:

- Total H1 FY26 bookings ARR: **$14,074,500**
- Total H1 FY26 commission expense: **$916,935**
- Commission as % of bookings ARR: **6.5%**, in line with plan target
- Company-wide average quota attainment: **96.7%**

The HTML dashboard's JavaScript aggregation logic was then checked against both of those independently — filtering, summing, and NRR calculations were run in Node against the same underlying dataset and produced matching figures under every filter combination tested (by quarter, by segment). Three build methods, one dataset, one set of numbers. That's the same tie-out discipline a real FP&A review would demand before a number goes in front of leadership.

## What the analysis actually found

Real (synthetic) findings a manager would act on, not just decoration:

- One Mid-Market rep closed the quarter at **178% of quota** — worth checking whether the territory quota was set too conservatively before assuming it's pure overperformance.
- Two reps have been under **60% attainment for two straight quarters** — candidates for a coaching conversation ahead of the next comp cycle.
- SMB segment NRR reads as **125%**, but it's concentrated in a handful of large expansion renewals rather than broad-based retention — a good example of a metric that needs a second look before it goes in a board deck.
- Commission expense held steady at **6.1%–7.2% of bookings ARR** every month of H1, which is what let the Q3 forecast use a trailing-average rate with reasonable confidence.

## How this maps to the job

| What the role asks for | Where it shows up here |
|---|---|
| Lead company-wide commission calculations | Bookings Detail calc engine (Excel) |
| Commission analytics & financial modeling | Executive Dashboard + interactive dashboard |
| Enhance commission processes/logic/reporting | Commission Plan Rules tab + rep-level views |
| Forecasting/budgeting through commission accruals | Monthly Accrual & Q3 Forecast tab |
| Advanced Excel, complex model development | Full workbook, live formulas, zero errors |
| SaaS metrics fluency | NRR, ARR mix, attainment tracked throughout |
| Alteryx-style data prep | Python ETL pipeline + workflow diagram |
| Tableau-style dashboards | Interactive HTML/Plotly dashboard |
| AI tools (Claude) | Built with Claude — a real, honest data point for that conversation |

## What this project is — and isn't

This is a demonstration of technical range: building a commission engine, a data pipeline, and two reporting layers that all agree with each other, from scratch, using a realistic (if synthetic) business scenario. It's meant to be a concrete thing to open and walk through in an interview.

It isn't a substitute for years of FP&A experience or actual cross-functional work with a real Sales org — those aren't things a solo project can manufacture, and this is presented as an independent project, not prior employment.
