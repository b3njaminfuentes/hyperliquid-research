# Hyperliquid Research

Open quantitative research on **Hyperliquid** perpetual futures.

**Main question:** does an extreme *funding rate* predict where the price moves over the next hours?

**Next question:** do jumps in *open interest* and *liquidations* anticipate strong moves (volatility)?

> Status: 🟡 in progress. Everything gets published, including what doesn't work. "No signal" is a result too.
>
> 🇪🇸 Guía en español: [docs/GUIA_ES.md](docs/GUIA_ES.md)

---

## 1. What this is about

**Hyperliquid** is an exchange where people trade **perpetual futures** ("perps"): leveraged bets that a coin goes up (**long**) or down (**short**), with no expiry date.

**Funding rate.** A perp never expires, so something has to keep its price tied to the coin's real price. That something is *funding*: a payment between longs and shorts **every hour**.
- **Positive** funding: longs pay shorts. More people than usual are betting on a rise.
- **Negative** funding: shorts pay longs. More people than usual are betting on a fall.

**Open interest.** How many contracts are open at a given moment. Rising: new money is coming in. Falling: people are closing positions.

**Liquidation.** When a leveraged trader loses too much, the exchange closes the position by force. Many liquidations at once push the price further the same way (a cascade).

### The idea being tested

When funding is **very high**, too many people are betting on a rise and paying a lot to hold it. If the price doesn't follow, they close or get liquidated, and that **pushes the price down**. The reverse with very negative funding.

Does it actually happen, or is it a myth? That is what this project measures. Plenty of "obvious" ideas don't hold up in the data, which is why they get measured.

---

## 2. What's in the project

```
hyperliquid-research/
├── README.md              ← this file: the project, the method and (at the end) the results
├── requirements.txt       ← Python libraries used
├── data/
│   ├── BTC.csv, ETH.csv, SOL.csv   ← hourly price and funding (~200 days)
│   └── oi/                ← open interest recorded by collector.py
├── scripts/
│   ├── download.py        ← pulls hourly price and funding from the Hyperliquid API
│   ├── collector.py       ← records open interest every minute (keep it running)
│   └── make_notebooks.py  ← generates the notebooks (already done)
├── notebooks/
│   ├── 01_explorar.ipynb  ← look at the data: is it clean? charts
│   ├── 02_funding.ipynb   ← the question: does funding predict the price?
│   └── 03_backtest.ipynb  ← the honest test: could you make money with it?
└── docs/
    └── GUIA_ES.md         ← the full guide in Spanish
```

**Data:** the last ~200 days (about 4,800 hours). For each hour: the coin's closing price and that hour's funding rate.

---

## 3. How to run it

```bash
cd ~/hyperliquid-research
source .venv/bin/activate     # activate the project's environment
```

| To… | Command |
|---|---|
| Update the data | `python scripts/download.py` |
| Record open interest (leave it running in another terminal) | `python scripts/collector.py` |
| Open the notebooks | `jupyter notebook` → browser opens → `notebooks` folder |

In a notebook, click a cell and press **Shift + Enter** to run it. Run them in order, top to bottom.

Fresh install: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

---

## 4. The research, step by step

### Step 1 · Know the data (`01_explorar`)
- [ ] Are there missing hours (gaps)? How many?
- [ ] Any odd moves (huge rises or drops in one hour)? Look those dates up: was it a real event?
- [ ] Is funding usually positive or negative? When did it spike?

### Step 2 · The question (`02_funding`)
The notebook sorts every hour from lowest to highest funding, splits them into 5 equal groups and computes, for each group, how far the price moved over the next 8 hours.
- [ ] Look at the 5-bar chart. **Do the bars fall or rise in order from group 1 to 5?** → possible signal. **Jumbled or similar?** → no signal.
- [ ] Repeat with `H = 4` and `H = 24`.
- [ ] Check ETH and SOL at the end: **does the pattern repeat?** If it shows up in only one coin, suspect chance.

### Step 3 · The honest test (`03_backtest`)
Simulates a simple rule: *if funding is very high, short for 8 hours; if very low, go long*.
- The threshold is picked using only the **first 2/3** of the data and tested on the **last 1/3**, never seen before. **Only that test result counts.**
- Costs: fees (0.035% per trade) and funding paid.
- [ ] Does it make money in the test period, after costs?
- [ ] Does it also work on ETH and SOL and at other horizons (robustness table)?
- [ ] A very high Sharpe (above 2 or 3) almost always means a bug.

### Step 4 · Open interest and liquidations (next)
- `collector.py` must run for **4 to 6 weeks** first.
- Question: does a big jump in open interest anticipate a strong move in the next hour?
- Benchmark: "the next hour moves as much as the last one". A model that can't beat that is useless.
- To do: find out how to get liquidations (Hyperliquid's trades websocket).

### Step 5 · Write up the results (section 6)

---

## 5. Rules

1. **Never use the future.** Every rule uses only data available at that moment; future returns are only for measuring.
2. **Split in time:** decide on one part of the data, test on another you never looked at.
3. **Always after costs.**
4. **Publish what fails.**
5. **No real money.** This is research, not trading.

**Classic mistakes:** leaking future data without noticing; trying 50 variants and showing only the winner; forgetting costs; drawing conclusions from a handful of trades.

---

## 6. Results

*(Filled in as each step is done.)*

| Step | Result | Date |
|---|---|---|
| Data | | |
| Does funding predict the price? | | |
| Backtest (test period) | | |
| Robustness | | |

**What didn't work and limitations:**

**Conclusion:**

---

## Data source

Hyperliquid public API (`https://api.hyperliquid.xyz/info`): `fundingHistory`, `candleSnapshot` (1-hour candles) and `metaAndAssetCtxs` (current open interest).
