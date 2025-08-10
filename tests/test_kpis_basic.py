import sys, pathlib, pandas as pd

# add repo root to import path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.kpis import revenue, orders, aov, FilterCtx

def load_sample():
    # use the CSV we added so pyarrow isn't required on CI
    fp = pathlib.Path("data/samples/sample_orders.csv")
    df = pd.read_csv(fp, parse_dates=["order_date"])
    return df

def test_revenue_orders_aov_consistency():
    df = load_sample()
    f = FilterCtx(category=None, store=None)
    # whole span
    start, end = df["order_date"].min(), df["order_date"].max()
    rev = revenue(df, start, end, f)
    ords = orders(df, start, end, f)
    avg  = aov(df, start, end, f)

    # sanity: revenue equals sum(quantity*unit_price)
    assert abs(rev - float((df["quantity"]*df["unit_price"]).sum())) < 1e-6
    # sanity: AOV ~ revenue/orders (guard against divide-by-zero)
    if ords > 0:
        assert abs(avg - (rev/ords)) < 1e-6
