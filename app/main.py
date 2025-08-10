from __future__ import annotations

# --- Streamlit Cloud import fix ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -----------------------------------

import os
import streamlit as st
import pandas as pd
from app.kpis import revenue, orders, aov, top_products, FilterCtx
from app.insight_engine import generate_insights
from app.fact_checker import check_insights
from app.components import kpi_tiles, trend_chart, top_products_bar
from app.logger import save_run
from app.upload import upload_data_widget
from app.explainer import explain
from app.analytics import (
    apply_filters, daily_revenue, yoy_period, mix_table, price_volume_bridge, zscore_last_day
)

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed" / "orders.parquet"
SAMP = BASE / "data" / "samples" / "sample_orders.parquet"

@st.cache_data
def load_sample_or_processed() -> pd.DataFrame:
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

def fmt_pct(x):
    return f"{x*100:,.1f}%" if pd.notna(x) else "-"

def main():
    st.set_page_config(page_title="AI KPI Dashboard (with Fact Checker)", layout="wide")
    st.title("AI KPI Dashboard (with Fact Checker)")

    # Load data source
    with st.sidebar:
        st.header("Data source")
        src = st.radio("Choose data", ["Sample (built-in)", "Upload CSV/XLSX"], index=0)
    if src == "Upload CSV/XLSX":
        df = upload_data_widget()
        if df is None or df.empty:
            st.info("Upload a file and click **Use this data** in the sidebar to begin.")
            st.stop()
    else:
        df = load_sample_or_processed()

    # Filters & options
    min_d, max_d = date_bounds(df)
    with st.sidebar:
        st.header("Filters")
        sd, ed = st.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        category = st.selectbox("Category", ["(All)"] + sorted(df["category"].astype(str).unique().tolist()))
        store = st.selectbox("Store", ["(All)"] + sorted(df["store"].astype(str).unique().tolist()))
        compare_prev = st.checkbox("Compare with previous period", value=True)
        compare_yoy = st.checkbox("Compare YoY (same dates last year)", value=True)

        st.header("Analysis options")
        show_mix = st.checkbox("Show mix-shift tables", value=True)
        mix_dim = st.selectbox("Mix dimension", ["category","store"])
        show_bridge = st.checkbox("Show price vs volume bridge", value=True)
        show_outliers = st.checkbox("Show outlier badge (z-score)", value=True)

        st.header("LLM & Logging")
        model_name = st.text_input("Model name", os.getenv("MODEL_NAME", "offline-heuristic"))
        temperature = st.slider("Temperature", 0.0, 1.0, float(os.getenv("TEMPERATURE", "0.2")), 0.05)
        want_explain = st.checkbox("Explain insights (Executive summary)", value=True)
        log_run = st.checkbox("Log runs to artifacts/", value=True)

    # Prepare contexts
    start = pd.to_datetime(sd); end = pd.to_datetime(ed)
    fctx = FilterCtx(category=None if category == "(All)" else category,
                     store=None if store == "(All)" else store)

    # KPIs
    kpis = kpi_block(df, start, end, fctx)

    # Current and comparison slices
    filtered = apply_filters(df, start, end, fctx)

    prev_filtered = None
    if compare_prev:
        period_len = (end - start).days + 1
        prev_start = start - pd.Timedelta(days=period_len)
        prev_end = start - pd.Timedelta(days=1)
        prev_filtered = apply_filters(df, prev_start, prev_end, fctx)

    yoy_filtered = None
    if compare_yoy:
        y_start, y_end = yoy_period(start, end)
        yoy_filtered = apply_filters(df, y_start, y_end, fctx)

    # Base charts
    st.divider()
    trend_chart(filtered, freq="M")
    top_products_bar(filtered, n=10)
    st.divider()

    # Comparisons: prior period and YoY
    if compare_prev or compare_yoy:
        st.subheader("Comparisons")
    if compare_prev and prev_filtered is not None and not prev_filtered.empty:
        cur_rev, prev_rev = float(filtered["revenue"].sum()), float(prev_filtered["revenue"].sum())
        delta = cur_rev - prev_rev
        pct = (delta / prev_rev) if prev_rev else 0.0
        st.markdown(f"**Vs previous period:** Revenue Δ ${delta:,.0f}  ({pct*100:,.1f}%)")
    if compare_yoy and yoy_filtered is not None and not yoy_filtered.empty:
        cur_rev, yoy_rev = float(filtered["revenue"].sum()), float(yoy_filtered["revenue"].sum())
        delta = cur_rev - yoy_rev
        pct = (delta / yoy_rev) if yoy_rev else 0.0
        st.markdown(f"**YoY:** Revenue Δ ${delta:,.0f}  ({pct*100:,.1f}%)")

    # Mix-shift tables
    if show_mix:
        st.subheader("Mix shift")
        c1, c2 = st.columns(2)
        with c1:
            st.caption(f"Top {mix_dim} by share (current vs prior)")
            mt = mix_table(filtered, prev_filtered, by=mix_dim, top_n=10)
            if mt.empty:
                st.info("Not enough data for mix table.")
            else:
                mt_disp = mt.copy()
                for col in ["share_cur","share_prev","delta_share"]:
                    mt_disp[col] = mt_disp[col].apply(fmt_pct)
                st.dataframe(mt_disp, use_container_width=True, height=320)
        with c2:
            if mix_dim == "category":
                alt_dim = "store"
            else:
                alt_dim = "category"
            st.caption(f"Top {alt_dim} by share (current vs prior)")
            mt2 = mix_table(filtered, prev_filtered, by=alt_dim, top_n=10)
            if mt2.empty:
                st.info("Not enough data for mix table.")
            else:
                mt2_disp = mt2.copy()
                for col in ["share_cur","share_prev","delta_share"]:
                    mt2_disp[col] = mt2_disp[col].apply(fmt_pct)
                st.dataframe(mt2_disp, use_container_width=True, height=320)

    # Price vs volume bridge
    if show_bridge:
        st.subheader("Revenue bridge (price vs volume)")
        bridge = price_volume_bridge(filtered, prev_filtered)
        if bridge.empty:
            st.info("Need a previous period to compute the bridge.")
        else:
            st.dataframe(bridge, use_container_width=True, height=240)
            st.bar_chart(bridge.set_index("component")["value"])

    # Outlier badge (z-score on daily revenue)
    if show_outliers:
        s = daily_revenue(filtered)
        z = zscore_last_day(s)
        if z is not None and abs(z) >= 2:
            arrow = "↑" if z > 0 else "↓"
            st.warning(f"Outlier: last day is {arrow} {abs(z):.1f}σ from mean (daily revenue).")
        else:
            st.caption("No daily revenue outliers (|z| < 2).")

    # Insights + Executive summary
    payload = build_prompt_payload(df, start, end, fctx, compare_prev=compare_prev)
    insights, checked, rows = render_insights(df, payload)

    if want_explain:
        txt = explain(rows, kpis, df_current=filtered, df_prev=prev_filtered,
                      model=model_name, temperature=float(temperature))
        st.markdown(txt)

    if log_run:
        settings = {"model": model_name, "temperature": float(temperature),
                    "compare_prev": compare_prev, "compare_yoy": compare_yoy,
                    "mix_dim": mix_dim, "source": src}
        path = save_run(payload, insights, rows, settings)
        st.caption(f"Run logged to: {path}")

    st.caption("Offline by default; set USE_OPENAI=1 + OPENAI_API_KEY to enable a hosted model.")
    st.caption("Upload CSV/XLSX in the sidebar to analyze your own data.")
if __name__ == "__main__":
    main()
