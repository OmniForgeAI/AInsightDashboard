from __future__ import annotations
import os, json
from typing import List, Dict, Optional
import pandas as pd

_METRIC_KEYS = {"cur", "prev", "delta", "revenue"}

def _drivers(cur: pd.DataFrame, prev: Optional[pd.DataFrame] = None):
    """Return top contributors and top movers for category/store/product."""
    def one_dim(by: str):
        if by not in cur.columns:
            return None
        # Current aggregates
        cur_agg = cur.groupby(by, dropna=False)["revenue"].sum()
        cur_agg.index.name = by
        cur_agg = cur_agg.sort_values(ascending=False)

        out = {"by": by}

        contrib = cur_agg.head(5).reset_index().rename(columns={"revenue": "revenue"})
        out["top"] = contrib.to_dict(orient="records")

        # Previous aggregates (if provided)
        movers = None
        if prev is not None and len(prev) and by in prev.columns:
            prev_agg = prev.groupby(by, dropna=False)["revenue"].sum()
            prev_agg.index.name = by
            joined = pd.DataFrame({"cur": cur_agg, "prev": prev_agg}).fillna(0.0)
            joined.index.name = by
            joined["delta"] = joined["cur"] - joined["prev"]
            movers = (
                joined.sort_values("delta", ascending=False)
                .head(5)
                .reset_index()
                .to_dict(orient="records")
            )
        out["movers"] = movers or []
        return out

    dims = []
    for by in ["category", "store", "product"]:
        d = one_dim(by)
        if d is not None:
            dims.append(d)
    return dims

def _pick_label(row: Dict, dim_key: str) -> str:
    """Safely get the label value for this dimension from a dict row."""
    # Try exact, Title, UPPER, and common fallback 'index'
    for k in (dim_key, dim_key.title(), dim_key.upper(), "index"):
        if k in row:
            return str(row[k])
    # As last resort, first non-metric field
    for k, v in row.items():
        if k not in _METRIC_KEYS:
            return str(v)
    return "N/A"

def explain(
    rows: List[Dict],
    kpis: Dict,
    df_current: Optional[pd.DataFrame] = None,
    df_prev: Optional[pd.DataFrame] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
) -> str:
    """Return an executive summary. Uses OpenAI if enabled, else an offline fallback."""
    cur_df = df_current if df_current is not None else pd.DataFrame(columns=["revenue"])
    prev_df = df_prev if df_prev is not None else None
    drivers = _drivers(cur_df, prev_df)

    # Hosted model (optional)
    if os.getenv("USE_OPENAI") == "1" and os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            client = OpenAI()
            sys_msg = (
                "You are a senior BI analyst. Write a crisp executive summary with four sections: "
                "1) Key movements, 2) Drivers, 3) Risks/Watchouts, 4) Next actions. "
                "Use ONLY provided numbers (kpis, verified claims, drivers). Keep under ~120 words."
            )
            payload = {"kpis": kpis, "claims": rows, "drivers": drivers}
            mdl = model or os.getenv("MODEL_NAME", "gpt-4o-mini")
            resp = client.chat.completions.create(
                model=mdl,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                temperature=temperature,
                max_tokens=350,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"_Explanation unavailable (model error: {e})._"

    # Offline summary
    bullets = []
    if kpis.get("revenue") is not None and kpis.get("orders") is not None:
        aov = kpis.get("aov")
        bullets.append(
            f"Revenue: ${kpis['revenue']:,.0f}; Orders: {kpis['orders']:,.0f}; AOV: ${aov:,.2f}"
            if aov is not None else
            f"Revenue: ${kpis['revenue']:,.0f}; Orders: {kpis['orders']:,.0f}"
        )

    verified = [r for r in rows if "VERIFIED" in (r.get("status") or "")]
    approx = [r for r in rows if "APPROX" in (r.get("status") or "")]
    mismatch = [r for r in rows if "MISMATCH" in (r.get("status") or "")]
    if verified: bullets.append(f"{len(verified)} claim(s) verified.")
    if approx:   bullets.append(f"{len(approx)} approx claim(s).")
    if mismatch: bullets.append(f"{len(mismatch)} mismatch(es) to review.")

    # Drivers
    for d in drivers:
        dim_key = d["by"]
        label = None
        if d.get("top"):
            t = d["top"][0]
            label = _pick_label(t, dim_key)
            try:
                bullets.append(f"Top {dim_key.title()}: {label} (${float(t.get('revenue', 0)):,.0f}).")
            except Exception:
                bullets.append(f"Top {dim_key.title()}: {label}.")
        if d.get("movers"):
            m = d["movers"][0]
            label_m = _pick_label(m, dim_key)
            try:
                bullets.append(f"Biggest mover in {dim_key.title()}: {label_m} (Δ ${float(m.get('delta', 0)):,.0f}).")
            except Exception:
                bullets.append(f"Biggest mover in {dim_key.title()}: {label_m}.")

    actions = []
    if mismatch: actions.append("Investigate mismatched claims in audit log.")
    if drivers and any(d.get("movers") for d in drivers):
        actions.append("Drill into top movers to confirm causes (promo, price, traffic).")
    if not actions: actions.append("Maintain current focus; monitor weekly for anomalies.")

    text = "### Executive summary\n"
    text += "• " + "\n• ".join(bullets) + "\n\n"
    text += "**Next actions:** " + "; ".join(actions)
    return text
