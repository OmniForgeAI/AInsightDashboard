import argparse
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed"
SAMP = BASE / "data" / "samples"

def generate_sample(seed: int = 7, n_orders: int = 2000) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2023-01-01")
    dates = start + pd.to_timedelta(rng.integers(0, 540, size=n_orders), unit="D")
    products = ["Phone Case","USB-C Cable","Wireless Mouse","Keyboard","HDMI Cable","Laptop Stand","Earbuds","Charger","Webcam","Monitor"]
    categories = {
        "Phone Case":"Accessories","USB-C Cable":"Accessories","Wireless Mouse":"Peripherals",
        "Keyboard":"Peripherals","HDMI Cable":"Accessories","Laptop Stand":"Accessories",
        "Earbuds":"Audio","Charger":"Accessories","Webcam":"Peripherals","Monitor":"Displays"
    }
    product = rng.choice(products, size=n_orders)
    category = [categories[p] for p in product]
    quantity = rng.integers(1, 5, size=n_orders)
    unit_price = rng.choice([9.99,14.99,19.99,24.99,29.99,49.99,79.99,149.99,199.99], size=n_orders)
    order_id = [f"O{100000+i}" for i in range(n_orders)]
    store = rng.choice(["East","West","Central"], size=n_orders, p=[0.4,0.35,0.25])
    df = pd.DataFrame({
        "order_id": order_id,
        "order_date": pd.to_datetime(dates),
        "product": product,
        "category": category,
        "store": store,
        "quantity": quantity,
        "unit_price": unit_price
    })
    df["revenue"] = df["quantity"] * df["unit_price"]
    return df

def write_parquet(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)

def main(generate_sample_flag: bool = False):
    if generate_sample_flag:
        df = generate_sample()
        write_parquet(df, SAMP / "sample_orders.parquet")
        write_parquet(df, PROC / "orders.parquet")
        print("✔ Sample data written.")
    else:
        raise SystemExit("Use --generate-sample for now.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate-sample", action="store_true")
    args = ap.parse_args()
    main(generate_sample_flag=args.generate_sample)
