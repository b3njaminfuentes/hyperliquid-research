"""Downloads hourly price and funding rate for each coin from Hyperliquid and saves them to
data/<COIN>.csv (one row per hour; columns time, close, fundingRate).

Usage:  python scripts/download.py
"""
import time
from pathlib import Path

import pandas as pd
import requests

API = "https://api.hyperliquid.xyz/info"
COINS = ["HYPE", "BTC", "ETH", "SOL"]  # HYPE: Hyperliquid's own token
DAYS = 200  # the API returns up to 5000 one-hour candles (~208 days)
OUT = Path(__file__).resolve().parent.parent / "data"


def funding(coin: str, start_ms: int) -> pd.DataFrame:
    """Funding is paid every hour. The API returns 500 records per call: page through them
    up to the present."""
    rows = []
    while True:
        r = requests.post(API, json={"type": "fundingHistory", "coin": coin, "startTime": start_ms}, timeout=30).json()
        if not r:
            break
        rows += r
        start_ms = r[-1]["time"] + 1
        if len(r) < 500:
            break
        time.sleep(0.2)  # be gentle with the API
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], unit="ms").dt.floor("h")
    df["fundingRate"] = df["fundingRate"].astype(float)
    return df[["time", "fundingRate"]].drop_duplicates("time")


def candles(coin: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    """One-hour candles; keep the closing price."""
    req = {"coin": coin, "interval": "1h", "startTime": start_ms, "endTime": end_ms}
    r = requests.post(API, json={"type": "candleSnapshot", "req": req}, timeout=30).json()
    df = pd.DataFrame(r)
    df["time"] = pd.to_datetime(df["t"], unit="ms")
    df["close"] = df["c"].astype(float)
    return df[["time", "close"]]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    now = int(time.time() * 1000)
    start = now - DAYS * 24 * 3600 * 1000
    for coin in COINS:
        price = candles(coin, start, now)
        fund = funding(coin, start)
        df = price.merge(fund, on="time", how="left")  # one row per hour with both columns
        df.to_csv(OUT / f"{coin}.csv", index=False)
        print(f"{coin}: {len(df)} hours, from {df.time.min()} to {df.time.max()}")


if __name__ == "__main__":
    main()
