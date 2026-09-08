# Meridian Commission Analytics Suite

FY26 sales commission calculation engine, data-prep pipeline, and analytics dashboards for a
fictional B2B SaaS company (Meridian Risk Technologies). Built as a portfolio project — see
`case_study.md` for the full write-up.

## What's in this folder

| File | What it is | How to open it |
|---|---|---|
| `Meridian_Commission_Model.xlsx` | 7-tab Excel FP&A model — commission calc engine, forecast, dashboard | Excel / LibreOffice Calc |
| `Meridian_Commission_Dashboard.html` | Interactive Tableau-style dashboard | Any web browser |
| `pipeline_workflow_diagram.png` | Visual of the data-prep pipeline | Any image viewer |
| `pipeline.py` | Python (pandas) data-prep pipeline | Terminal — see setup below |
| `generate_data.py` | Regenerates the synthetic source dataset | Terminal — see setup below |
| `data/*.csv` | Source data (already generated, ready to use) | — |
| `case_study.md` | Full project write-up | Any text editor / Markdown viewer |
| `requirements.txt` | Python dependencies for `pipeline.py` | Used by `pip install` |

## Quick start

**Excel model and dashboard need no setup** — just double-click them.

**Python pipeline:**
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 pipeline.py
```
Expected output ends with: `Commission calculated for 270 deals (total: $916,935)`

Full step-by-step instructions, including how to regenerate the source data, are in the chat
this project was built in — or just re-run `pipeline.py` after `generate_data.py`; both use
relative paths, so nothing needs to be edited.

## Data integrity note

The commission math in this project was built three independent ways — Excel formulas, the
Python pipeline, and the dashboard's JavaScript — and all three tie out to the same totals
(H1 FY26 bookings ARR: $14,074,500; commission expense: $916,935). That's intentional: it's
the same cross-check discipline a real FP&A review would apply before a number goes in front
of leadership.
