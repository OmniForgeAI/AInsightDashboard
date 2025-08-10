from __future__ import annotations
import os, json
from typing import List, Dict, Optional

import pandas as pd

def _drivers(cur: pd.DataFrame, prev: Optional[pd.DataFrame] = None):
    """Return top contributors and top movers for a few dimensions."""
    def one_dim(by: str):
        if by not in cur.columns:
            return None
        cur_agg = cur.groupby(by, dropna=False)["revenue"].sum().sort_values(ascending=False)
        contrib = cur_agg.head(5).reset_index().rename(columns={"revenue": "revenue"})
        out = {"by": by, "top": contrib.to_dict(orient="records")}
        if prev is not None:
            prev_agg = prev.groupby(by, dropna=False)["revenue"].sum() if len(prev) else pd.Series(dtype=float)
            joined = pd.DataFrame({"cur": cur_agg, "prev": prev_agg}).fillna(0.0)
            joined["delta"] = joined["cur"] - joined["prev"]
            out["movers"] = (
                joined.sort_values("delta", ascending=False)
                .head(5)
                .reset_index()
                .to_dict(orient="records")
            )
        return out

    dims = []
    for by in ["category", "store", "product"]:
        d = one_dim(by)
        if d is not None:
            dims.append(d)
    return dims

def explain(
    rows: List[Dict],
    kpis: Dict,
    df_current: Optional[pd.DataFrame] = None,
    df_prev: Optional[pd.DataFrame] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
) -> str:
    """Return an executive summary. Uses OpenAI if enabled, else an offline fallback."""
    drivers = _drivers(df_current if df_current is not None else pd.DataFrame(), df_prev)

    # Hosted model path (optional)
    if os.getenv("USE_OPENAI") == "1" and os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            client = OpenAI()
            sys_msg = (
                "You are a senior BI analyst. Write a crisp executive summary with four sections:"
                " 1) Key movements, 2) Drivers, 3) Risks/Watchouts, 4) Next actions."
                " Use ONLY provided numbers (kpis, verified claims, drivers)."
                " Always cite concrete numbers and keep it under ~120 words total."
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

    # Offline fallback (numbers-only; no API calls)
    bullets = []
    if kpis.get("revenue") is not None and kpis.get("orders") is not None:
        aov = kpis.get("aov")
        bullets.append(
            f"Revenue: ${kpis['revenue']:,.0f}; Orders: {kpis['orders']:,.0f}; AOV: ${aov:,.2f}" if aov is not None
            else f"Revenue: ${kpis['revenue']:,.0f}; Orders: {kpis['orders']:,.0f}"
        )

    # Summarize verified claims
    verified = [r for r in rows if "VERIFIED" in (r.get("status") or "")]
    approx = [r for r in rows if "APPROX" in (r.get("status") or "")]
    mismatch = [r for r in rows if "MISMATCH" in (r.get("status") or "")]
    if verified:
        bullets.append(f"{len(verified)} claim(s) verified.")
    if approx:
        bullets.append(f"{len(approx)} approx claim(s).")
    if mismatch:
        bullets.append(f"{len(mismatch)} mismatch(es) to review.")

    # Drivers: top contributors & movers
    if drivers:
        for d in drivers:
            by = d["by"].title()
            if d.get("top"):
                top = d["top"][0]
                bullets.append(f"Top {by}: {top[by.lower()]} (${top['revenue']:,.0f}).")
            if d.get("movers"):
                m = d["movers"][0]
                bullets.append(f"Biggest mover in {by}: {m[by.lower()]} (Δ ${m['delta']:,.0f}).")

    # Next actions (simple heuristics)
    actions = []
    if mismatch:
        actions.append("Investigate mismatched claims in audit log.")
    if drivers and any(d.get("movers") for d in drivers):
        actions.append("Drill into top movers to confirm causes (promo, price, traffic).")
    if not actions:
        actions.append("Maintain current focus; monitor weekly for anomalies.")

    text = "### Executive summary\n"
    text += "• " + "\n• ".join(bullets) + "\n\n"
    text += "**Next actions:** " + "; ".join(actions)
    return text
