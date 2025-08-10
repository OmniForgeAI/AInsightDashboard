# AI KPI Dashboard — Fact-Checked LLM Insights (Offline by default)

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

> A manager-friendly KPI dashboard that explains performance with **LLM-generated insights** and **automatic fact-checking**.  
> **Privacy-safe by default**: runs fully offline. Optionally enable a hosted model (OpenAI) with env vars.

<!-- Screenshot -->
<p align="center">
  <img src="artifacts/dashboard_realdata.png" alt="Dashboard screenshot" width="900"/>
</p>

## Why this project
- **Real analytics**: revenue, orders, AOV, top products, filters (date/category/store).
- **Trust**: every insight is auto-checked against the data (✅/⚠️/❌) with an audit CSV.
- **Upload your own data**: CSV/XLSX mapping UI in the sidebar.
- **Portable**: one-command local run; Streamlit Cloud-ready with a small sample dataset.

## Quickstart (local)
```bash
# 1) clone & enter
git clone https://github.com/OmniForgeAI/AInsightDashboard.git
cd AInsightDashboard

# 2) (Windows) create venv & install
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt

# 3) run
./.venv/Scripts/python.exe -m streamlit run app/main.py


Small, Streamlit app that analyzes a retail-style dataset, shows KPIs, and generates **AI insights** that are **fact-checked** against the data.

## Quick Start

```bash
make setup
make data
make run
```

This launches Streamlit on a local URL. The default dataset is a small synthetic sample generated locally (no internet required).

## Notes
- The default LLM adapter ships with an offline heuristic so the app works without keys.
- To use a hosted model, set env `USE_OPENAI=1` and `OPENAI_API_KEY` (adapter stub included).

## Data
This app uses the **Online Retail II** dataset (UCI ML Repository, CC BY 4.0).  
Raw file is kept locally (`data/raw/`); processed Parquet lives in `data/processed/`.

## Evaluation
We log each run (payload, model settings, raw JSON output, and checks) and summarize results.
See **artifacts/eval_summary.csv** for VERIFIED% across runs.

## Screenshot
![Dashboard](artifacts/dashboard_realdata.png)

## Executive summary (offline by default)

This build runs the Executive summary using an offline heuristic (no external API calls).

**Enable a hosted model later (optional):**

1) Install the client:
