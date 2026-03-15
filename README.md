# AI Business Process Analyzer

Upload a process event log (CSV) or describe your process in plain text — get an AI-powered audit report with bottleneck analysis, inefficiency detection, and prioritized improvement recommendations.

> Built for operations teams, process consultants, and small businesses who want Celonis-level insights without the Celonis price tag.

---

## What It Does

- **CSV mode:** Upload an event log with `case_id`, `timestamp`, `activity`, `resource` columns. The app calculates cycle times, rework rates, resource workload, and bottlenecks — then sends the stats to Claude for a structured analysis.
- **Text mode:** No data? Just describe your process. Claude identifies likely bottlenecks, waste patterns, and quick wins.
- **Downloadable report:** Every analysis produces a Markdown report you can share with stakeholders.

---

## Demo

![Demo Screenshot](reports/demo.png)

*Sample analysis of an order fulfillment process showing bottleneck at Credit Check (avg 4.5h wait) and 33% rework rate at QC.*

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/aliwahab/ai-process-analyzer.git
cd ai-process-analyzer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Anthropic API key
cp .env.example .env
# Edit .env and add your key: ANTHROPIC_API_KEY=sk-ant-...

# 4. Run the app
streamlit run app.py
```

Get a free API key at [console.anthropic.com](https://console.anthropic.com).

---

## Sample Datasets

Three sample event logs are included in `sample_data/`:

| File | Process | Cases | Activities |
|---|---|---|---|
| `order_processing.csv` | E-commerce order fulfillment | 6 | 7 steps |
| `invoice_approval.csv` | Finance invoice approval | 6 | 6 steps |
| `customer_onboarding.csv` | B2B client onboarding | 6 | 6 steps |

Load any of them directly from the app sidebar — no file upload needed.

---

## CSV Format

Your event log must have these columns:

```
case_id,timestamp,activity,resource
CASE001,2024-01-15 08:00:00,Order Received,System
CASE001,2024-01-15 08:45:00,Credit Check,Finance Team
...
```

- `case_id` — unique identifier per process instance
- `timestamp` — format `YYYY-MM-DD HH:MM:SS`
- `activity` — name of the process step
- `resource` — person, team, or system performing the step (optional but recommended)

---

## Example Report Output

```markdown
## Executive Summary
The order fulfillment process has an average cycle time of 38 hours against a 2-day target,
driven primarily by a bottleneck at Credit Check (avg 4.5h wait) and a 33% rework rate at QC.

## Key Bottlenecks
1. Credit Check — avg 4.5h, max 25h. Likely single-reviewer dependency.
2. Quality Control rework — 2 of 6 cases required re-pack, adding 12-22h each.
3. Inventory stockouts — 1 case delayed 48h due to out-of-stock event.

## Top Recommendations
1. [High ROI] Add a second Finance reviewer or automate low-risk credit checks.
2. [Quick Win] Root-cause the QC failures — likely a pick-and-pack training gap.
...
```

---

## Tech Stack

- **Python** — core logic
- **Anthropic Claude API** — AI analysis (claude-opus-4-6)
- **Streamlit** — web UI
- **Pandas** — event log parsing and statistics

---

## Use Cases

- **SMB process audits** — upload your order, invoice, or HR data and get a consultant-quality report in minutes
- **Pre-Celonis assessment** — understand your process before investing in enterprise tooling
- **Interview demo** — shows applied AI + process mining skills to Celonis, Databricks, and Microsoft hiring teams

---

## About

Built by **Ali Wahab** — Data & AI Engineer with 12+ years of enterprise integration experience, Databricks and Microsoft Fabric certified.

[LinkedIn](https://www.linkedin.com/in/syed-wahab-ali) · [GitHub](https://github.com/wahabali)

---

*Want a custom process analysis for your business? [Get in touch.](https://www.linkedin.com/in/syed-wahab-ali)*
