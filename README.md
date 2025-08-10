# AI KPI Dashboard — Fact-Checked LLM Insights (Offline by default)

[![CI](https://github.com/OmniForgeAI/AInsightDashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/OmniForgeAI/AInsightDashboard/actions/workflows/ci.yml)

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

## Feature overview (current)

- **KPI tiles**: Revenue, Orders, AOV with filters for **date / category / store**.
- **Comparisons**: 
  - Vs **previous period** (Δ and %Δ)
  - **YoY** (same dates last year)
- **Quarterly report (last 8 quarters)**:
  - Revenue, Orders, AOV + **QoQ%** and **YoY%**
  - **Fiscal-aware**: choose fiscal year start month (e.g., April → Q-MAR)
  - **Download CSV**
- **Mix-shift analysis**:
  - Category & Store tables with **share_cur**, **share_prev**, **Δ share**
- **Revenue bridge (price vs volume)**:
  - Decomposes ΔRevenue into **Volume**, **Price**, and **Interaction**
- **Outlier badge**:
  - Daily revenue **z-score** flag (|z| ≥ 2)
- **Executive summary**:
  - Offline by default; includes **drivers** (top contributors & movers) and **next actions**
  - Optional hosted model (OpenAI) if env vars are set
- **Fact-checked insights**:
  - Every claim badged (**✅ VERIFIED / ⚠️ APPROX / ❌ MISMATCH**) with a downloadable **audit CSV**
- **Upload your own data**:
  - CSV/XLSX **column mapping** UI, light cleaning, no disk writes
- **Run logging**:
  - Saves payload, raw outputs, and checks to `artifacts/runs/`
- **Conventions**:
  - **Last updated** stamp, configurable **currency symbol**, **Data Dictionary** in README

> Live demo: (https://ainsightdashboard-wg34hlm7rzad4ndyytjgy9.streamlit.app/)

## How to enable hosted model (optional)

```bash
pip install openai
export USE_OPENAI=1
export OPENAI_API_KEY=sk-...     # your key
export MODEL_NAME=gpt-4o-mini


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

## Executive summary (offline by default)

This build runs the Executive summary using an offline heuristic (no external API calls).

**Enable a hosted model later (optional):**

1) Install the client:

## Data Dictionary & Conventions

**Orders**: count of unique `order_id` in the selected period/filters.  
**Revenue**: sum of `quantity * unit_price` (gross; returns with negative qty/price are filtered out by the loader).  
**AOV (Average Order Value)**: `Revenue / Orders`.

**Date & time**: based on the dataset’s `order_date` values (no timezone shifts applied).  
**Currency**: Display-only symbol chosen in the sidebar; data is not FX-converted.  
**Fiscal calendar**: Quarterly report can use a fiscal year that starts in any month (e.g., April → ‘Q-MAR’ year-end).

## Changelog
- **v1.1** — YoY, mix-shift, revenue bridge, outlier badge, quarterly (fiscal-aware), last-updated, data dictionary
- **v1.0** — Upload CSV/XLSX, fact-checked insights with audit CSV, offline executive summary


## What's new
- **Export**: Download current filtered view as CSV (+ copy-friendly preview).
- **Auto-open**: Streamlit opens your browser automatically (headless = false).
- **Quarterly (fiscal-aware)**: QoQ & YoY with custom fiscal year start month.
- **Last updated & currency**: Shown under KPIs.
- **Mix shift & revenue bridge**: Segment shares and price/volume decomposition.
- **Outlier badge**: Daily revenue z-score flag.
- **CI & sample CSV**: GitHub Actions + quick-upload sample.
