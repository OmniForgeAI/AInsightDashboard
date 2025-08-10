from __future__ import annotations
import os, json
from typing import List, Dict

def explain(rows: List[Dict], kpis: Dict, model: str | None = None, temperature: float = 0.2) -> str:
    """
    rows: list of checked rows (what you pass to the audit CSV)
    kpis:  dict from kpi_block: {'revenue', 'orders', 'aov'}
    """
    # Use hosted model if enabled
    if os.getenv("USE_OPENAI") == "1" and os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            client = OpenAI()
            sys_msg = (
                "You are a senior data analyst. Explain KPI changes to a busy manager "
                "in clear, direct English. Be concise (5–7 bullets). Cite concrete numbers "
                "from the provided data. Avoid jargon."
            )
            user_msg = json.dumps({"kpis": kpis, "claims": rows}, ensure_ascii=False)
            mdl = model or os.getenv("MODEL_NAME", "gpt-4o-mini")
            resp = client.chat.completions.create(
                model=mdl,
                messages=[{"role": "system", "content": sys_msg},
                          {"role": "user", "content": user_msg}],
                temperature=temperature,
                max_tokens=300,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"_Explanation unavailable (model error: {e})._"

    # Offline fallback (no API key)
    bullets = []
    if kpis.get("aov") is not None:
        bullets.append(f"Average order value is ${kpis['aov']:.2f}.")
    inc = [r for r in rows if "increase" in (r.get("reason","") + r.get("statement","")).lower()]
    dec = [r for r in rows if "decrease" in (r.get("reason","") + r.get("statement","")).lower()]
    if inc: bullets.append(f"{len(inc)} metric(s) increased vs the prior period.")
    if dec: bullets.append(f"{len(dec)} metric(s) decreased vs the prior period.")
    tp = next((r for r in rows if "Top product" in r.get("statement","")), None)
    if tp: bullets.append(tp["statement"])
    return "• " + "\n• ".join(bullets) if bullets else "_No explanation available for this view._"
