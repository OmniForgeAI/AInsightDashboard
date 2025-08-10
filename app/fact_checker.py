from __future__ import annotations
from typing import List, Any, Dict
import pandas as pd
from dataclasses import dataclass
from .kpis import FilterCtx, revenue, orders, aov

@dataclass
class CheckedInsight:
    claim_id: str
    statement: str
    status: str
    reason: str
    value_reported: float
    value_computed: float
    comparison: Dict[str, float]
    metric: str

def _parse_filter(d: dict) -> FilterCtx:
    return FilterCtx(category=d.get("category"), store=d.get("store"))

def _compute_metric(df: pd.DataFrame, metric: str, start, end, f: FilterCtx) -> float:
    if metric == "revenue":
        return revenue(df, start, end, f)
    if metric == "orders":
        return float(orders(df, start, end, f))
    if metric == "aov":
        return aov(df, start, end, f)
    return 0.0

def _as_dict(comp) -> Dict[str, float]:
    if comp is None:
        return {}
    if isinstance(comp, dict):
        return comp
    # Pydantic v2 BaseModel
    try:
        return comp.model_dump()
    except Exception:
        out = {}
        for k in ("vs", "delta", "delta_pct"):
            if hasattr(comp, k):
                out[k] = getattr(comp, k)
        return out

def check_insights(insights: List[Any], df: pd.DataFrame, tolerance_pct: float = 0.5) -> List[CheckedInsight]:
    out: List[CheckedInsight] = []
    for ins in insights:
        try:
            start = pd.to_datetime(ins.period.start)
            end = pd.to_datetime(ins.period.end)
            fctx = _parse_filter(getattr(ins, "filter", {}) or {})
            computed = _compute_metric(df, ins.metric, start, end, fctx)
            reported = float(getattr(ins, "value_reported", 0.0))
            err_pct = 0.0 if computed == 0 else abs((reported - computed) / computed) * 100.0

            status = "✅ VERIFIED" if err_pct <= tolerance_pct else "❌ MISMATCH"
            reason = f"abs error {err_pct:.2f}% (≤ {tolerance_pct}?)"

            comp = _as_dict(getattr(ins, "comparison", None))
            if comp.get("vs") == "previous_period":
                period_len = (end - start).days + 1
                prev_start = start - pd.Timedelta(days=period_len)
                prev_end = start - pd.Timedelta(days=1)
                prev_val = _compute_metric(df, ins.metric, prev_start, prev_end, fctx)
                delta = computed - prev_val
                delta_pct = (delta / prev_val * 100.0) if prev_val != 0 else 0.0
                if status == "✅ VERIFIED":
                    d_err = abs(delta - float(comp.get("delta", 0.0)))
                    dp_err = abs(delta_pct - float(comp.get("delta_pct", 0.0)))
                    if d_err > max(0.01, 0.005 * abs(computed)) or dp_err > 0.5:
                        status = "⚠️ APPROX"
                        reason = f"delta/percent slightly off (Δ={d_err:.2f}, Δ%={dp_err:.2f})"

            out.append(CheckedInsight(
                claim_id=getattr(ins, "claim_id", "unknown"),
                statement=getattr(ins, "statement", ""),
                status=status,
                reason=reason,
                value_reported=reported,
                value_computed=float(computed),
                comparison=comp,
                metric=getattr(ins, "metric", "other"),
            ))
        except Exception as e:
            out.append(CheckedInsight(
                claim_id=getattr(ins, "claim_id", "unknown"),
                statement=getattr(ins, "statement", ""),
                status="❌ ERROR",
                reason=str(e),
                value_reported=float(getattr(ins, "value_reported", 0.0)),
                value_computed=0.0,
                comparison=_as_dict(getattr(ins, "comparison", None)),
                metric=getattr(ins, "metric", "other"),
            ))
    return out

