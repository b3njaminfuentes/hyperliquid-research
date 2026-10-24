"""Descarga de Hyperliquid el precio por hora y el funding rate de cada moneda, y los guarda
en data/<MONEDA>.csv (una tabla: una fila por hora, columnas time, close, fundingRate).

Uso:  python scripts/download.py
"""
import time
from pathlib import Path

import pandas as pd
import requests

API = "https://api.hyperliquid.xyz/info"
COINS = ["BTC", "ETH", "SOL"]
DAYS = 200  # la API da hasta 5000 velas de 1 hora (~208 días)
OUT = Path(__file__).resolve().parent.parent / "data"


def funding(coin: str, start_ms: int) -> pd.DataFrame:
    """El funding se paga cada hora. La API devuelve 500 registros por consulta: pedimos tandas
    hasta llegar al presente."""
    rows = []
    while True:
        r = requests.post(API, json={"type": "fundingHistory", "coin": coin, "startTime": start_ms}, timeout=30).json()
        if not r:
            break
        rows += r
        start_ms = r[-1]["time"] + 1
        if len(r) < 500:
            break
        time.sleep(0.2)  # no saturar la API
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], unit="ms").dt.floor("h")
    df["fundingRate"] = df["fundingRate"].astype(float)
    return df[["time", "fundingRate"]].drop_duplicates("time")


def candles(coin: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    """Velas de 1 hora; nos quedamos con el precio de cierre."""
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
        df = price.merge(fund, on="time", how="left")  # una fila por hora con las dos columnas
        df.to_csv(OUT / f"{coin}.csv", index=False)
        print(f"{coin}: {len(df)} horas, desde {df.time.min()} hasta {df.time.max()}")


if __name__ == "__main__":
    main()
