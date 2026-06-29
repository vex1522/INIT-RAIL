"""Clean and normalize the synthetic ridership dataset."""

from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT_PATH = Path("outputs") / "cleaned_ridership.csv"


def run() -> pd.DataFrame:
    """Generate, clean, and persist the ridership dataset."""
    np.random.seed(42)
    n = 500
    rng = np.random.default_rng(42)

    passengers = np.random.randint(200, 5000, n).astype(object)
    delay_min = np.random.choice([np.nan, 0, 5, 10, 15, 30], n).astype(float)
    zone = list(np.random.choice(["Beach", "Egmore", "Tambaram", "Avadi", "Chengalpattu"], n))
    route_id = list(np.random.choice([f"R{i:02d}" for i in range(1, 51)], n))
    dates = list(pd.date_range("2022-01-01", periods=n, freq="D"))
    crossing_type = list(np.random.choice(["Manned", "Unmanned", "Semi-manned"], n))

    idx = rng.choice(n, size=40, replace=False)
    for i in idx[:15]:
        passengers[i] = np.nan
    for i in idx[15:25]:
        passengers[i] = str(passengers[i] or 0).split(".")[0] + " pax"
    for i in idx[25:32]:
        zone[i] = zone[i].lower()
    for i in idx[32:37]:
        route_id[i] = " " + route_id[i] + " "
    for i in idx[37:40]:
        delay_min[i] = -999.0
    for i in rng.choice(n, 8):
        passengers[i] = 99999

    df = pd.DataFrame(
        {
            "route_id": route_id,
            "date": dates,
            "passengers": passengers,
            "delay_min": delay_min,
            "zone": zone,
            "crossing_type": crossing_type,
        }
    )

    print("NULL COUNTS BEFORE:\n", df.isnull().sum())

    df["passengers"] = pd.to_numeric(df["passengers"], errors="coerce")
    passenger_median = df["passengers"].median()
    df["passengers"] = df["passengers"].fillna(passenger_median)
    passenger_cap = df["passengers"].mean() + 3 * df["passengers"].std()
    passenger_99 = df["passengers"].quantile(0.99)
    df.loc[df["passengers"] > passenger_cap, "passengers"] = passenger_99
    df["passengers"] = df["passengers"].round().astype("int64")

    df["delay_min"] = df["delay_min"].replace(-999, np.nan)
    df["delay_min"] = df.groupby("route_id")["delay_min"].transform(
        lambda x: x.fillna(x.median())
    )
    df["delay_min"] = df["delay_min"].fillna(df["delay_min"].median())
    df["delay_min"] = df["delay_min"].round(2)

    valid_zones = {"Beach", "Egmore", "Tambaram", "Avadi", "Chengalpattu"}
    df["zone"] = df["zone"].astype(str).str.strip().str.title()
    df.loc[~df["zone"].isin(valid_zones), "zone"] = "Unknown"

    df["route_id"] = df["route_id"].astype(str).str.strip()

    df["peak_load"] = np.select(
        [
            df["passengers"] > 3500,
            df["passengers"].between(1500, 3500, inclusive="both"),
        ],
        ["High", "Medium"],
        default="Low",
    )
    df["day_of_week"] = pd.to_datetime(df["date"]).dt.day_name()

    print("NULL COUNTS AFTER:\n", df.isnull().sum())

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    return df
