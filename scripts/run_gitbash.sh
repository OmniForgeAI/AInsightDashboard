#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
source .venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m app.data_loader --generate-sample
streamlit run app/main.py
