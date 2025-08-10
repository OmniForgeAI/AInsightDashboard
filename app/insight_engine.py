from __future__ import annotations
import json
import os
import uuid
import pandas as pd
from pydantic import BaseModel, Field, ValidationError
from typing import List, Literal

class Comparison(BaseModel):
    vs: Literal["previous_period","previous_year","none"] = "none"
    delta: float = 0.0
    delta_pct: float = 0.0

class Period(BaseModel):
    start: str
    end: str

class Insight(BaseModel):
    claim_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metric: Literal["revenue","orders","aov","return_rate","other"]
    time_granularity: Literal["day","week","month","quarter"]
    period: Period
    filter: dict
    statement: str
    value_reported: float
    comparison: Comparison = Comparison()

def call_llm(prompt: str) -> str:
    """
    Offline-friendly heuristic 'LLM':
    Expects a JSON payload with summarized KPI values; returns a small JSON list of Insight objects.
    For real models, set USE_OPENAI=1 and provide OPENAI_API_KEY (adapter stub included).
    """
    if os.getenv("USE_OPENAI") == "1" and os.getenv("OPENAI_API_KEY"):
        # Stub for real API call (intentionally left unimplemented for offline demo)
        pass

    data = json.loads(prompt)
    current = data["current"]
    previous = data.get("previous", {})
    filt = data.get("filter", {})
    period = data["period"]

    insights = []
    # Revenue change
    if "revenue" in current and "revenue" in previous and previous["revenue"] > 0:
        delta = current["revenue"] - previous["revenue"]
        delta_pct = (delta / previous["revenue"]) * 100.0
        direction = "increased" if delta >= 0 else "decreased"
        insights.append({
            "metric": "revenue",
            "time_granularity": "month",
            "period": period,
            "filter": filt,
            "statement": f"Revenue {direction} by {abs(delta_pct):.1f}% compared with the previous period.",
            "value_reported": float(current["revenue"]),
            "comparison": {"vs":"previous_period","delta": float(delta), "delta_pct": float(delta_pct)}
        })
    # AOV highlight
    if "aov" in current:
        insights.append({
            "metric": "aov",
            "time_granularity": "month",
            "period": period,
            "filter": filt,
            "statement": f"Average order value is {current['aov']:.2f}.",
            "value_reported": float(current["aov"]),
            "comparison": {"vs":"none","delta": 0.0, "delta_pct": 0.0}
        })
    # Top product mention
    tp = data.get("top_product")
    if tp:
        insights.append({
            "metric": "other",
            "time_granularity": "month",
            "period": period,
            "filter": filt,
            "statement": f"Top product by revenue is {tp['product']} at {tp['revenue']:.2f}.",
            "value_reported": float(tp["revenue"]),
            "comparison": {"vs":"none","delta": 0.0, "delta_pct": 0.0}
        })

    return json.dumps(insights, ensure_ascii=False)

def generate_insights(kpi_summary: dict) -> List[Insight]:
    raw = call_llm(json.dumps(kpi_summary))
    try:
        items = json.loads(raw)
        return [Insight(**it) for it in items]
    except (json.JSONDecodeError, ValidationError):
        return []
