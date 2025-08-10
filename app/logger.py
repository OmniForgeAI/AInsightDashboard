from __future__ import annotations
import json, time, hashlib
from pathlib import Path
import pandas as pd

ART = Path(__file__).resolve().parent.parent / "artifacts" / "runs"

def _run_id(payload, settings) -> str:
    key = json.dumps({"payload": payload, "settings": settings}, sort_keys=True).encode()
    h = hashlib.sha1(key).hexdigest()[:8]
    return time.strftime("%Y%m%d_%H%M%S") + "_" + h

def save_run(payload: dict, insights, checked_rows: list[dict], settings: dict) -> str:
    rid = _run_id(payload, settings)
    out = ART / rid
    out.mkdir(parents=True, exist_ok=True)
    (out / "meta.json").write_text(json.dumps(settings, indent=2))
    (out / "payload.json").write_text(json.dumps(payload, indent=2))
    try:
        serial = [i.model_dump() if hasattr(i, "model_dump") else i for i in insights]
    except Exception:
        serial = [getattr(i, "__dict__", str(i)) for i in insights]
    (out / "insights_raw.json").write_text(json.dumps(serial, indent=2))
    pd.DataFrame(checked_rows).to_csv(out / "checked.csv", index=False)
    return str(out)
