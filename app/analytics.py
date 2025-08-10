from __future__ import annotations
from typing import Optional
import calendar
import pandas as pd
from app.kpis import FilterCtx

def apply_filters(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, fctx: FilterCtx) -> pd.DataFrame:
    m = (df["order_date"] >= start) & (df["order_date"] <= end)
    if fctx.category:
        m &= df["category"] == fctx.category
    if fctx.store:
        m &= df["store"] == fctx.store
    return df[m].copy()

def daily_revenue(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    return df.groupby(df["order_date"].dt.date)["revenue"].sum()

def yoy_period(start: pd.Timestamp, end: pd.Timestamp):
    return (start - pd.DateOffset(years=1), end - pd.DateOffset(years=1))

def mix_table(cur: pd.DataFrame, prev: Optional[pd.DataFrame], by: str = "category", top_n: int = 10) -> pd.DataFrame:
    if cur.empty or by not in cur.columns:
        return pd.DataFrame(columns=["segment","revenue_cur","share_cur","share_prev","delta_share"])
    cur_rev = cur.groupby(by, dropna=False)["revenue"].sum()
    total_cur = float(cur_rev.sum()) or 1.0
    df_cur = (cur_rev / total_cur).rename("share_cur").to_frame()
    df_cur["revenue_cur"] = cur_rev

    if prev is not None and not prev.empty and by in prev.columns:
        prev_rev = prev.groupby(by, dropna=False)["revenue"].sum()
        total_prev = float(prev_rev.sum()) or 1.0
        df_prev = (prev_rev / total_prev).rename("share_prev").to_frame()
        joined = df_cur.join(df_prev, how="outer").fillna(0.0)
        joined["delta_share"] = joined["share_cur"] - joined["share_prev"]
    else:
        joined = df_cur
        joined["share_prev"] = 0.0
        joined["delta_share"] = joined["share_cur"]

    out = joined.reset_index().rename(columns={by: "segment"})
    out["abs_delta_share"] = out["delta_share"].abs()
    out = out.sort_values(["abs_delta_share","revenue_cur"], ascending=[False, False]).head(top_n)
    return out[["segment","revenue_cur","share_cur","share_prev","delta_share"]]

def price_volume_bridge(cur: pd.DataFrame, prev: Optional[pd.DataFrame]) -> pd.DataFrame:
    if prev is None or cur.empty or prev.empty:
        return pd.DataFrame(columns=["component","value"])
    cur_qty  = float(cur["quantity"].sum())
    prev_qty = float(prev["quantity"].sum())
    cur_rev  = float(cur["revenue"].sum())
    prev_rev = float(prev["revenue"].sum())
    cur_price  = (cur_rev/cur_qty) if cur_qty  > 0 else 0.0
    prev_price = (prev_rev/prev_qty) if prev_qty > 0 else 0.0

    delta_rev    = cur_rev - prev_rev
    vol_effect   = (cur_qty  - prev_qty)  * prev_price
    price_effect = (cur_price - prev_price)* prev_qty
    interaction  = (cur_qty  - prev_qty)  * (cur_price - prev_price)

    return pd.DataFrame({
        "component": ["Previous revenue","Volume effect","Price effect","Interaction","Current revenue","Δ Revenue"],
        "value":     [prev_rev,            vol_effect,     price_effect,   interaction,   cur_rev,           delta_rev]
    })

def zscore_last_day(series: pd.Series) -> Optional[float]:
    if series is None or len(series) < 2:
        return None
    import numpy as np
    vals = series.values.astype(float)
    mu = vals.mean()
    sd = vals.std(ddof=0)
    if sd == 0:
        return 0.0
    return float((vals[-1] - mu) / sd)

# ---------- Quarterly report helpers ----------
def _quarter_str(p: pd.Period) -> str:
    # '2024Q3' -> '2024-Q3'
    s = str(p)
    return s.replace("Q", "-Q")

def _fiscal_alias_from_start(start_month: int) -> str:
    # start_month: 1..12 (Jan..Dec). Pandas uses quarter alias by *end* month.
    end_month = 12 if start_month == 1 else start_month - 1
    end_abbr = calendar.month_abbr[end_month].upper()
    return f"Q-{end_abbr}"

def quarterly_report(
    df: pd.DataFrame, fctx: FilterCtx, n_quarters: int = 8, fiscal_start_month: int = 1
) -> pd.DataFrame:
    """Quarterly revenue, orders (unique order_id), AOV, with QoQ% and YoY% (fiscal-aware)."""
    if df.empty:
        return pd.DataFrame(columns=["quarter","revenue","orders","aov","qoq_pct","yoy_pct"])

    # filter by category/store across full date span
    start, end = df["order_date"].min(), df["order_date"].max()
    dff = apply_filters(df, start, end, fctx)
    if dff.empty:
        return pd.DataFrame(columns=["quarter","revenue","orders","aov","qoq_pct","yoy_pct"])

    dff = dff.copy()
    # Fiscal quarter alias (e.g., 'Q-MAR' for FY starting April)
    alias = _fiscal_alias_from_start(int(fiscal_start_month))
    dff["qtr"] = dff["order_date"].dt.to_period(alias)

    # aggregates
    rev = dff.groupby("qtr")["revenue"].sum()
    ords = dff.groupby("qtr")["order_id"].nunique()
    aov = rev / ords.replace({0: pd.NA})

    out = pd.DataFrame({"revenue": rev, "orders": ords, "aov": aov})
    # changes
    out["qoq_pct"] = out["revenue"].pct_change()      # vs previous quarter (fiscal-aware)
    out["yoy_pct"] = out["revenue"].pct_change(4)     # vs same fiscal quarter last year

    out = out.reset_index().rename(columns={"qtr": "quarter"})
    out["quarter"] = out["quarter"].apply(_quarter_str)
    out = out.sort_values("quarter").tail(n_quarters).reset_index(drop=True)
    return out
