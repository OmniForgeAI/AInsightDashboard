from __future__ import annotations
import pandas as pd
from dataclasses import dataclass

@dataclass(frozen=True)
class FilterCtx:
    category: str | None = None
    store: str | None = None

def _apply_filters(df: pd.DataFrame, f: FilterCtx) -> pd.DataFrame:
    out = df
    if f.category:
        out = out[out["category"] == f.category]
    if f.store:
        out = out[out["store"] == f.store]
    return out

def revenue(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, f: FilterCtx) -> float:
    d = df[(df["order_date"] >= start) & (df["order_date"] <= end)]
    d = _apply_filters(d, f)
    return float(d["revenue"].sum())

def orders(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, f: FilterCtx) -> int:
    d = df[(df["order_date"] >= start) & (df["order_date"] <= end)]
    d = _apply_filters(d, f)
    return int(d["order_id"].nunique())

def aov(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, f: FilterCtx) -> float:
    o = orders(df, start, end, f)
    rev = revenue(df, start, end, f)
    return float(rev / o) if o > 0 else 0.0

def top_products(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, f: FilterCtx, n: int = 10) -> pd.DataFrame:
    d = df[(df["order_date"] >= start) & (df["order_date"] <= end)]
    d = _apply_filters(d, f)
    g = d.groupby("product", as_index=False).agg(revenue=("revenue","sum"), orders=("order_id","nunique"))
    g = g.sort_values(["revenue","orders"], ascending=[False, False]).head(n).reset_index(drop=True)
    return g
