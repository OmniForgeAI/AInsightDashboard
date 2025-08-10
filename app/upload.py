from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np

REQUIRED = ["order_id","order_date","product","quantity","unit_price"]
OPTIONAL = ["store","category"]
ALIASES = {
    "order_id":["order_id","invoice","invoiceno","order","id"],
    "order_date":["order_date","invoicedate","date","orderdate"],
    "product":["product","description","item","sku","name"],
    "quantity":["quantity","qty","count","units"],
    "unit_price":["unit_price","price","unitprice","amount"],
    "store":["store","region","country","channel"],
    "category":["category","dept","department","class"]
}
def _guess(cols,target):
    low=[c.lower() for c in cols]
    for a in ALIASES.get(target,[]):
        if a in low: return cols[low.index(a)]
    return None
def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df=df.copy()
    df["order_date"]=pd.to_datetime(df["order_date"],errors="coerce",infer_datetime_format=True)
    df["quantity"]=pd.to_numeric(df["quantity"],errors="coerce")
    df["unit_price"]=pd.to_numeric(df["unit_price"],errors="coerce")
    df=df.dropna(subset=["order_id","order_date","product","quantity","unit_price"])
    df=df[(df["quantity"]>0)&(df["unit_price"]>0)]
    if "store" not in df.columns: df["store"]="All"
    if "category" not in df.columns:
        df["category"]=df["product"].astype(str).str.split().str[0].fillna("General")
    df["revenue"]=df["quantity"]*df["unit_price"]
    cols=["order_id","order_date","product","category","store","quantity","unit_price","revenue"]
    return df[cols].sort_values("order_date").reset_index(drop=True)
def upload_data_widget(key="uploader"):
    with st.sidebar.expander("Upload data (CSV or Excel)", expanded=False):
        f=st.file_uploader("Choose a CSV/XLSX", type=["csv","xlsx","xls"], key=key)
        if not f: return st.session_state.get("uploaded_df")
        raw = pd.read_csv(f) if f.name.lower().endswith(".csv") else pd.read_excel(f)
        st.caption(f"Loaded shape: {raw.shape[0]:,} × {raw.shape[1]}")
        cols=list(raw.columns)
        st.write("Map your columns:")
        sel={}
        for tgt in REQUIRED+OPTIONAL:
            default=_guess(cols,tgt)
            sel[tgt]=st.selectbox(tgt, ["(none)"]+cols, index=(cols.index(default)+1) if default in cols else 0)
        if st.button("Use this data", use_container_width=True):
            missing=[t for t in REQUIRED if sel.get(t) in [None,"(none)"]]
            if missing: st.error("Missing: "+", ".join(missing))
            else:
                out={}
                for tgt in REQUIRED+OPTIONAL:
                    s=sel.get(tgt)
                    if s and s!="(none)": out[tgt]=raw[s]
                df=pd.DataFrame(out)
                df=_clean(df)
                st.session_state["uploaded_df"]=df
                st.success(f"Data ready: {len(df):,} rows")
        prev=st.session_state.get("uploaded_df")
        if prev is not None: st.dataframe(prev.head(10), use_container_width=True, height=200)
    return st.session_state.get("uploaded_df")
