import pandas as pd
from types import SimpleNamespace
from app.fact_checker import check_insights

def df_fake():
    return pd.DataFrame({
        "order_id": ["A","B"],
        "order_date": pd.to_datetime(["2024-01-01","2024-01-02"]),
        "product": ["X","Y"],
        "category": ["Cat","Cat"],
        "store": ["East","East"],
        "quantity": [1,1],
        "unit_price": [10.0, 10.0],
        "revenue": [10.0, 10.0]
    })

class Period(SimpleNamespace): pass

def insight_ok():
    return SimpleNamespace(
        claim_id="1",
        statement="Revenue increased by 0.0% compared with the previous period.",
        metric="revenue",
        period=Period(start="2024-01-01", end="2024-01-02"),
        filter={"category":"Cat","store":"East"},
        value_reported=20.0,
        comparison={"vs":"previous_period","delta":0.0,"delta_pct":0.0}
    )

def test_fact_checker_verified():
    df = df_fake()
    res = check_insights([insight_ok()], df, tolerance_pct=0.5)
    assert res[0].status in ("✅ VERIFIED","⚠️ APPROX")
