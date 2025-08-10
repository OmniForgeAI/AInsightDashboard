# --- Streamlit Cloud import fix ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]  # repo root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -----------------------------------

from __future__ import annotations
import os, json
import streamlit as st
import pandas as pd
from pathlib import Path
from app.kpis import revenue, orders, aov, top_products, FilterCtx
from app.insight_engine import generate_insights
from app.fact_checker import check_insights
from app.components import kpi_tiles, trend_chart, top_products_bar
from app.logger import save_run

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed" / "orders.parquet"
SAMP = BASE / "data" / "samples" / "sample_orders.parquet"

@st.cache_data
def load_data() -> pd.DataFrame:
    path = PROC if PROC.exists() else SAMP
    df = pd.read_parquet(path)
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df

def date_bounds(df: pd.DataFrame):
    return df["order_date"].min().date(), df["order_date"].max().date()

def kpi_block(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, fctx: FilterCtx):
    rev = revenue(df, start, end, fctx)
    ords = orders(df, start, end, fctx)
    avg = aov(df, start, end, fctx)
    kpi_tiles(rev, ords, avg)
    return {"revenue": rev, "orders": float(ords), "aov": avg}

def build_prompt_payload(df: pd.DataFrame, start, end, fctx: FilterCtx, compare_prev: bool):
    tp_df = top_products(df, start, end, fctx, n=1)
    tp = {"product": tp_df.iloc[0]["product"], "revenue": float(tp_df.iloc[0]["revenue"])} if len(tp_df) else None
    payload = {
        "period": {"start": str(start.date()), "end": str(end.date())},
        "filter": {"category": fctx.category, "store": fctx.store},
        "current": {
            "revenue": float(revenue(df, start, end, fctx)),
            "orders": float(orders(df, start, end, fctx)),
            "aov": float(aov(df, start, end, fctx)),
        },
        "top_product": tp
    }
    if compare_prev:
        period_len = (end - start).days + 1
        prev_start = start - pd.Timedelta(days=period_len)
        prev_end = start - pd.Timedelta(days=1)
        payload["previous"] = {
            "revenue": float(revenue(df, prev_start, prev_end, fctx)),
            "orders": float(orders(df, prev_start, prev_end, fctx)),
            "aov": float(aov(df, prev_start, prev_end, fctx)),
        }
    return payload

def render_insights(df: pd.DataFrame, payload: dict):
    insights = generate_insights(payload)
    checked = check_insights(insights, df, tolerance_pct=0.5)
    st.subheader("AI Insights (Fact-Checked)")
    rows = []
    for c in checked:
        st.markdown(f"- **{c.statement}** — {c.status}  \n _({c.reason})_")
        rows.append({
            "claim_id": c.claim_id, "statement": c.statement, "status": c.status,
            "reason": c.reason, "value_reported": c.value_reported,
            "value_computed": c.value_computed, "metric": c.metric
        })
    if rows:
        st.download_button("Download insight audit log (CSV)",
                           data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
                           file_name="insight_audit_log.csv", mime="text/csv")
    return insights, checked, rows

def main():
    st.set_page_config(page_title="AI KPI Dashboard (with Fact Checker)", layout="wide")
    st.title("AI KPI Dashboard (with Fact Checker)")

    df = load_data()
    min_d, max_d = date_bounds(df)

    with st.sidebar:
        st.header("Filters")
        sd, ed = st.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        category = st.selectbox("Category", ["(All)"] + sorted(df["category"].unique().tolist()))
        store = st.selectbox("Store", ["(All)"] + sorted(df["store"].unique().tolist()))
        compare_prev = st.checkbox("Compare with previous period", value=True)

        st.header("LLM & Logging")
        model_name = st.text_input("Model name", os.getenv("MODEL_NAME", "offline-heuristic"))
        temperature = st.slider("Temperature", 0.0, 1.0, float(os.getenv("TEMPERATURE", "0.2")), 0.05)
        log_run = st.checkbox("Log runs to artifacts/", value=True)

    start = pd.to_datetime(sd); end = pd.to_datetime(ed)
    fctx = FilterCtx(category=None if category == "(All)" else category,
                     store=None if store == "(All)" else store)

    kpis = kpi_block(df, start, end, fctx)

    st.divider()
    mask = (df["order_date"] >= start) & (df["order_date"] <= end)
    if fctx.category: mask &= df["category"] == fctx.category
    if fctx.store: mask &= df["store"] == fctx.store
    filtered = df[mask]
    trend_chart(filtered, freq="M")
    top_products_bar(filtered, n=10)
    st.divider()

    payload = build_prompt_payload(df, start, end, fctx, compare_prev=compare_prev)
    insights, checked, rows = render_insights(df, payload)

    if log_run:
        settings = {"model": model_name, "temperature": float(temperature), "compare_prev": compare_prev}
        path = save_run(payload, insights, rows, settings)
        st.caption(f"Run logged to: {path}")

    st.caption("Tip: set USE_OPENAI=1 and OPENAI_API_KEY to use a hosted model. The default runs offline.")
if __name__ == "__main__":
    main()
