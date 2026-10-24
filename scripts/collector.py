"""Graba cada minuto el interés abierto (open interest), el funding y el precio de cada moneda en
data/oi/<MONEDA>.csv. Hyperliquid no da historial de interés abierto: hay que grabarlo uno mismo,
y cuantas más semanas grabe, mejor. Dejalo corriendo (Ctrl+C para cortar; al volver a correrlo sigue
agregando filas).

Uso:  python scripts/collector.py
"""
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://api.hyperliquid.xyz/info"
COINS = ["BTC", "ETH", "SOL"]
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
    print("Grabando cada minuto en", OUT, "(Ctrl+C para cortar)")
    while True:
        try:
            snapshot()
        except Exception as e:  # un error de red no corta la grabación
            print("error, reintento en un minuto:", e)
        time.sleep(60 - time.time() % 60)  # al inicio de cada minuto


if __name__ == "__main__":
    main()
