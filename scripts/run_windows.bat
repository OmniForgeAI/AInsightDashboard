@echo off
REM Quick start for PowerShell/CMD on Windows
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m app.data_loader --generate-sample
streamlit run app/main.py
