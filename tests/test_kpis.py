import pandas as pd
from app.kpis import revenue, orders, aov, FilterCtx

def small_df():
    return pd.DataFrame({
        "order_id": ["A","B","C"],
        "order_date": pd.to_datetime(["2024-01-01","2024-01-02","2024-01-02"]),
        "product": ["X","Y","X"],
        "category": ["Cat","Cat","Dog"],
        "store": ["East","West","East"],
        "quantity": [1,2,1],
        "unit_price": [10.0, 5.0, 20.0],
        "revenue": [10.0,10.0,20.0]
    })

def test_kpis_basic():
    df = small_df()
    start = pd.Timestamp("2024-01-01")
    end = pd.Timestamp("2024-01-03")
    f = FilterCtx()
    assert revenue(df, start, end, f) == 40.0
    assert orders(df, start, end, f) == 3
    assert round(aov(df, start, end, f), 2) == 13.33
