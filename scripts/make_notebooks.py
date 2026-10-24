"""Generates the project notebooks (notebooks/*.ipynb). Run once; then edit them in Jupyter."""
from pathlib import Path

import nbformat as nbf

NB = Path(__file__).resolve().parent.parent / "notebooks"
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell


def save(name, cells):
    nb = nbf.v4.new_notebook()
    nb.cells = cells
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nbf.write(nb, NB / name)


LOAD = """import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams["figure.figsize"] = (11, 4)

COINS = ["HYPE", "BTC", "ETH", "SOL"]\nCOIN = "HYPE"   # Hyperliquid's own token; change to "BTC", "ETH" or "SOL" to look at another coin
df = pd.read_csv(f"../data/{COIN}.csv", parse_dates=["time"])"""

save("01_explorar.ipynb", [
    md("""# 01 · Explore the data

Before looking for patterns you need to **know the data** and check it is clean. If the data is wrong, everything after it is wrong too.

The data lives in `data/BTC.csv`: a **CSV**, a table saved as plain text (like a simple spreadsheet). Each row is one hour, with three columns:
- `time`: the hour.
- `close`: the price at the close of that hour.
- `fundingRate`: the **funding**, the payment made every hour between those betting on a rise (*longs*) and those betting on a fall (*shorts*). When it is **positive**, longs pay shorts: more people are betting on a rise than the market "needs"."""),
    md("## 1. Load the table\n`pd.read_csv` reads the file into a pandas table (a *DataFrame*). `head()` shows the first rows."),
    code(LOAD + "\ndf.head()"),
    md("## 2. Quick summary\n`describe()` gives, for each column, how many values there are, the mean, the min, the max, etc. Check that the numbers make sense."),
    code("df.describe()"),
    md("""## 3. Are there gaps?

A **gap** is an hour with no data. If many hours in a row are missing, the "next 8 hours" calculations go wrong.
- `isna().sum()`: how many empty values each column has.
- The second part looks for hours missing from the sequence (there should be one row every exact hour)."""),
    code("""print("Empty values per column:")
print(df.isna().sum())

gaps = df["time"].diff().dropna()
print("\\nGaps between rows other than 1 hour:", (gaps != pd.Timedelta("1h")).sum())"""),
    md("""## 4. Any odd values?

An **outlier** is a number far from normal: it can be a data error or a real event (a crash, a mass liquidation). Don't delete them blindly: look at them and decide.

Here we find the largest and smallest hourly return (how much the price changed from one hour to the next)."""),
    code("""df["ret_1h"] = df["close"].pct_change()
print("Largest 1-hour rises:")
print(df.nlargest(3, "ret_1h")[["time", "close", "ret_1h"]])
print("\\nLargest 1-hour drops:")
print(df.nsmallest(3, "ret_1h")[["time", "close", "ret_1h"]])"""),
    md("## 5. Plot the price\n`plot` draws one column against another. The horizontal axis is time, the vertical one is price."),
    code("""df.plot(x="time", y="close", title=f"{COIN}: hourly price", legend=False)
plt.ylabel("USD"); plt.show()"""),
    md("## 6. Plot the funding\nMultiplied by 100 to read it in %. Check whether it is usually positive, whether it spikes, and when."),
    code("""(df.set_index("time")["fundingRate"] * 100).plot(title=f"{COIN}: hourly funding rate (%)")
plt.axhline(0, color="black", lw=0.8); plt.ylabel("% per hour"); plt.show()

print(f"Hours with positive funding: {(df.fundingRate > 0).mean():.0%}")"""),
    md("""## Write down before moving on
- Are there gaps? How many?
- Any outlier? Was it a real event (look the date up on X or in the news)?
- Is funding usually positive or negative? Does it spike?

These answers go in the **Data** row of the README results."""),
])

save("02_funding.ipynb", [
    md("""# 02 · Does funding predict the price?

**The idea:** when funding is very high, a lot of people are betting on a rise and paying a lot to hold that bet. If the price doesn't follow, many close or get liquidated, and that pushes the price **down**. If true, very high funding would announce drops.

**The question:** does this hour's extreme funding predict how far the price moves over the **next 8 hours**?

Steps:
1. For each hour, compute how much the price moved over the **next** 8 hours.
2. Measure how **extreme** each hour's funding is compared with that week's normal.
3. Sort all hours from lowest to highest funding, split them into **5 equal groups** and look at the average price move in each group."""),
    code(LOAD),
    md("""## Step 1: the future return

`shift(-8)` takes the price 8 rows ahead (8 hours later). The future return is the % change from now until then.

**This is what we want to predict.** It is only used to measure; it can never be part of the rule, because in real life the future is unknown."""),
    code("""H = 8  # horizon in hours: try 4 and 24 too
df["fut_ret"] = df["close"].shift(-H) / df["close"] - 1
df[["time", "close", "fut_ret"]].head(10)"""),
    md("""## Step 2: how extreme is funding? (the *z-score*)

A funding of 0.001% can be high in a quiet week and normal in a wild one. So we compare it with **its own previous week** (168 hours):

`z = (funding now − last week's mean) / last week's standard deviation`

- `z = 0`: normal funding.
- `z = +2`: much higher than usual.
- `z = −2`: much lower than usual.

`rolling(168)` computes the mean and deviation using only the **previous** 168 hours, so no future information leaks in."""),
    code("""W = 168
mean = df["fundingRate"].rolling(W).mean()
std = df["fundingRate"].rolling(W).std()
df["z"] = (df["fundingRate"] - mean) / std

df = df.dropna(subset=["z", "fut_ret"])  # the first hours have no previous week
df["z"].hist(bins=60); plt.title(f"{COIN}: distribution of the funding z-score"); plt.show()"""),
    md("""## Step 3: the 5 groups

`pd.qcut(..., 5)` sorts the hours by z and splits them into 5 groups of equal size:
- Group 1: the 20% of hours with the **lowest** funding.
- Group 5: the 20% with the **highest** funding.

Then we compute the average future return of each group."""),
    code("""df["group"] = pd.qcut(df["z"], 5, labels=[1, 2, 3, 4, 5])
table = df.groupby("group", observed=True)["fut_ret"].agg(["mean", "count"])
table["mean %"] = table["mean"] * 100
print(table[["mean %", "count"]])

table["mean %"].plot.bar(title=f"{COIN}: average return over the next {H} h by funding group")
plt.xlabel("group (1 = lowest funding · 5 = highest)"); plt.ylabel("%"); plt.axhline(0, color="black", lw=0.8); plt.show()"""),
    md("""## How to read the chart

- **If the bars fall (or rise) in order from 1 to 5**, there is a **possible signal**: funding says something about the future price.
- **If the bars are jumbled or all similar**, there is **no signal**. That is a valid result and it gets published too.

**Careful:** with a few months of data, a small difference can be pure chance. That is what notebook 03 is for."""),
    md("## Extra: does it repeat in other coins?\nIf the pattern is real, it should show up in other coins too. If it appears in only one, suspect chance."),
    code("""for coin in COINS:
    d = pd.read_csv(f"../data/{coin}.csv", parse_dates=["time"])
    d["fut_ret"] = d["close"].shift(-H) / d["close"] - 1
    d["z"] = (d["fundingRate"] - d["fundingRate"].rolling(W).mean()) / d["fundingRate"].rolling(W).std()
    d = d.dropna(subset=["z", "fut_ret"])
    g = d.groupby(pd.qcut(d["z"], 5, labels=[1, 2, 3, 4, 5]), observed=True)["fut_ret"].mean() * 100
    print(coin.ljust(4), " · ".join(f"G{k}: {v:+.3f}%" for k, v in g.items()))"""),
])

save("03_backtest.ipynb", [
    md("""# 03 · An honest backtest

A **backtest** simulates what would have happened trading a rule in the past. It is easy to fool yourself, so there are three rules:

1. **Split in time.** Pick the rule looking only at the **first 2/3** of the data and test it on the **last 1/3**, never seen. Like studying with some exercises and sitting the exam with others.
2. **Pay fees** on every trade, and **funding** while the position is open.
3. **Try variations.** If it only works in one exact case, it was probably luck.

**The rule:** if the funding z-score goes above a threshold, bet on a **drop** for H hours (*short*). If it goes below minus the threshold, bet on a **rise** (*long*)."""),
    code(LOAD + """
H = 8
FEE = 0.00035  # 0.035% per trade (check Hyperliquid's current fee)
W = 168
df["z"] = (df["fundingRate"] - df["fundingRate"].rolling(W).mean()) / df["fundingRate"].rolling(W).std()
df = df.dropna(subset=["z"]).reset_index(drop=True)"""),
    md("""## The simulation

It walks the hours in order. With no open position, if z crosses the threshold, it opens one and holds it for H hours. Each trade's result is:

`result = direction × price return − 2 fees (in and out) − direction × funding paid`

(direction = +1 for long, −1 for short; a long pays positive funding and a short collects it)."""),
    code("""def backtest(d, threshold, H=H):
    trades, i = [], 0
    while i < len(d) - H:
        z = d.at[i, "z"]
        if abs(z) >= threshold:
            side = -1 if z > 0 else 1
            ret = d.at[i + H, "close"] / d.at[i, "close"] - 1
            fund = d["fundingRate"].iloc[i + 1:i + H + 1].fillna(0).sum()
            trades.append({"time": d.at[i, "time"], "side": side, "pnl": side * ret - 2 * FEE - side * fund})
            i += H  # no new trade until this one closes
        else:
            i += 1
    return pd.DataFrame(trades)


def measure(trades, name=""):
    if trades.empty:
        return {"name": name, "trades": 0}
    curve = trades["pnl"].cumsum()
    per_year = len(trades) / ((trades.time.max() - trades.time.min()).days / 365 + 1e-9)
    return {
        "name": name,
        "trades": len(trades),
        "total %": round(trades.pnl.sum() * 100, 2),
        "win rate %": round((trades.pnl > 0).mean() * 100, 1),
        "sharpe": round(trades.pnl.mean() / trades.pnl.std() * np.sqrt(per_year), 2) if trades.pnl.std() > 0 else None,
        "max drawdown %": round((curve - curve.cummax()).min() * 100, 2),
    }"""),
    md("""## Step 1: pick the threshold **using the training period only**

Try three thresholds on the first 2/3 and keep the best. The test period stays untouched."""),
    code("""cut = int(len(df) * 2 / 3)
train, test = df.iloc[:cut].reset_index(drop=True), df.iloc[cut:].reset_index(drop=True)
print("Train:", train.time.min().date(), "→", train.time.max().date())
print("Test: ", test.time.min().date(), "→", test.time.max().date())

res = pd.DataFrame([measure(backtest(train, t), f"threshold {t}") for t in [1.5, 2.0, 2.5]])
res"""),
    md("""## Step 2: the real test

Use the chosen threshold on the **test** period, never looked at. **This is the result that counts.**

- Wins in training but loses in test: it was chance (*overfitting*).
- Wins in both: possible signal, keep testing."""),
    code("""best = float(res.sort_values("total %", ascending=False).iloc[0]["name"].split()[-1])
trades = backtest(test, best)
print(measure(trades, f"TEST · threshold {best}"))

if not trades.empty:
    (trades.set_index("time")["pnl"].cumsum() * 100).plot(title=f"{COIN}: cumulative result in the test period (%)")
    plt.axhline(0, color="black", lw=0.8); plt.ylabel("%"); plt.show()"""),
    md("""## Step 3: robustness

Does it also work on other coins and other horizons? If the gain shows up in only one exact combination, it is most likely luck."""),
    code("""rows = []
for coin in COINS:
    d = pd.read_csv(f"../data/{coin}.csv", parse_dates=["time"])
    d["z"] = (d["fundingRate"] - d["fundingRate"].rolling(W).mean()) / d["fundingRate"].rolling(W).std()
    d = d.dropna(subset=["z"]).reset_index(drop=True)
    t = d.iloc[int(len(d) * 2 / 3):].reset_index(drop=True)
    for h in [4, 8, 24]:
        rows.append(measure(backtest(t, best, H=h), f"{coin} · {h} h"))
pd.DataFrame(rows)"""),
    md("""## Glossary
- **trades:** how many trades it made.
- **total %:** the sum of all trades, after fees and funding.
- **win rate %:** the share of winning trades.
- **sharpe:** return per unit of risk, annualized. Above 1 is good; above 2 is suspiciously good (check for a bug).
- **max drawdown %:** the most it lost from a peak. It measures how much pain you'd sit through.

## What goes in the README
- The **test period** result (not the training one).
- The robustness table.
- The limitations: a few months of data, one market regime, approximate fees, no slippage."""),
])
print("notebooks created")
