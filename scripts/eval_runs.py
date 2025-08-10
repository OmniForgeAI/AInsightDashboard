import pandas as pd
from pathlib import Path

def main():
    base = Path("artifacts/runs")
    rows = []
    for fp in sorted(base.glob("*/checked.csv")):
        df = pd.read_csv(fp)
        total = len(df)
        status = df["status"].fillna("")
        rows.append({
            "run": fp.parent.name,
            "total": total,
            "verified": int(status.str.contains("VERIFIED").sum()),
            "approx": int(status.str.contains("APPROX").sum()),
            "mismatch": int(status.str.contains("MISMATCH").sum()),
            "error": int(status.str.contains("ERROR").sum())
        })
    if not rows:
        print("No runs found in artifacts/runs")
        return
    out = pd.DataFrame(rows)
    out["verified_pct"] = (100 * out["verified"] / out["total"]).round(1)
    print(out.sort_values("run").to_string(index=False))
    out.to_csv("artifacts/eval_summary.csv", index=False)
    print("\nSaved artifacts/eval_summary.csv")
if __name__ == "__main__":
    main()
