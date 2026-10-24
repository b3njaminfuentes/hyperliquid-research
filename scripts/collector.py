"""Records open interest, funding and price for each coin every minute into data/oi/<COIN>.csv.
Hyperliquid has no open interest history, so you have to record it yourself: the more weeks, the
better. Leave it running (Ctrl+C to stop; running it again keeps appending rows).

Usage:  python scripts/collector.py
"""
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://api.hyperliquid.xyz/info"
COINS = ["HYPE", "BTC", "ETH", "SOL"]
OUT = Path(__file__).resolve().parent.parent / "data" / "oi"
FIELDS = ["time", "markPx", "openInterest", "funding", "dayNtlVlm"]


def snapshot() -> None:
    meta, ctxs = requests.post(API, json={"type": "metaAndAssetCtxs"}, timeout=30).json()
    names = [a["name"] for a in meta["universe"]]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for coin in COINS:
        c = ctxs[names.index(coin)]
        f = OUT / f"{coin}.csv"
        new = not f.exists()
        with f.open("a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(FIELDS)
            w.writerow([now, c["markPx"], c["openInterest"], c["funding"], c["dayNtlVlm"]])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Recording every minute into", OUT, "(Ctrl+C to stop)")
    while True:
        try:
            snapshot()
        except Exception as e:  # a network error does not stop the recording
            print("error, retrying in a minute:", e)
        time.sleep(60 - time.time() % 60)  # at the start of every minute


if __name__ == "__main__":
    main()
