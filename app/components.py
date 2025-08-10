from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px

def kpi_tiles(revenue_val: float, orders_val: int, aov_val: float):
    c1, c2, c3 = st.columns(3)
    c1.metric("Revenue", f"${revenue_val:,.2f}")
    c2.metric("Orders", f"{orders_val:,}")
    c3.metric("Avg Order Value", f"${aov_val:,.2f}")

def trend_chart(df: pd.DataFrame, freq: str = "M"):
    d = df.copy()
    d["period"] = d["order_date"].dt.to_period(freq).dt.to_timestamp()
    g = d.groupby("period", as_index=False).agg(revenue=("revenue","sum"))
    fig = px.line(g, x="period", y="revenue", title="Revenue Trend")
    st.plotly_chart(fig, use_container_width=True)

def top_products_bar(df: pd.DataFrame, n: int = 10):
    g = df.groupby("product", as_index=False).agg(revenue=("revenue","sum"))
    g = g.sort_values("revenue", ascending=False).head(n)
    fig = px.bar(g, x="product", y="revenue", title=f"Top {n} Products by Revenue")
    st.plotly_chart(fig, use_container_width=True)
