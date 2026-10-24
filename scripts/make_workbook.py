"""Generates notebooks/01_workbook.ipynb: practice tasks to do by hand. Notebook 01 is the solved
example; this one has empty cells for you to fill. Running this script again overwrites your work,
so run it only once."""
from pathlib import Path

import nbformat as nbf

OUT = Path(__file__).resolve().parent.parent / "notebooks" / "01_workbook.ipynb"
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell

if OUT.exists():
    raise SystemExit(f"{OUT.name} already exists: not overwriting your work")


def task(n, title, what, hint, start=""):
    return [md(f"## Task {n} · {title}\n\n{what}\n\n> 💡 **Hint:** {hint}"), code(start or "# your code here\n")]


cells = [
    md("""# 01 · Workbook: explore the data yourself

**How this works:** notebook `01_explorar` is the *solved example*. Here **you** write the code.

For each task:
1. Read what to do and the hint.
2. Write the code in the empty cell below and run it with **Shift + Enter**.
3. If you get stuck for more than 10 minutes, look at how `01_explorar` does it, then come back and write it yourself.
4. Errors are normal: read the last line of the red message, it usually says what went wrong.

At the end, answer the questions in the last cell. Those answers go into the README."""),
    md("## Setup\nRun this cell first: it loads the libraries. You don't need to change it."),
    code("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams["figure.figsize"] = (11, 4)
COINS = ["HYPE", "BTC", "ETH", "SOL"]"""),
    *task(1, "Load the data",
          "Load `../data/HYPE.csv` into a variable called `df` and show the **first 5** rows and the **last 5** rows.",
          "`pd.read_csv(path, parse_dates=[\"time\"])` loads the file. `df.head()` shows the first rows and `df.tail()` the last ones."),
    *task(2, "How big is it?",
          "How many rows (hours) does the table have? How many days is that?",
          "`len(df)` gives the number of rows. A day has 24 hours."),
    *task(3, "Missing values",
          "How many empty values does each column have?",
          "`df.isna().sum()`."),
    *task(4, "The craziest funding hour",
          "Find the hour with the **highest** funding and the hour with the **lowest**. Print the date and the value of each.\n\nThen look those dates up on X: what was happening with HYPE?",
          "`df.loc[df[\"fundingRate\"].idxmax()]` gives the full row with the highest value. `idxmin()` for the lowest."),
    *task(5, "The biggest 1-hour move",
          "Create a column `ret_1h` with the % change of the price from one hour to the next, and find the **biggest drop** in a single hour. When was it?",
          "`df[\"close\"].pct_change()` computes the change from the previous row. Then `nsmallest(1, \"ret_1h\")`."),
    *task(6, "Plot another coin",
          "Load ETH and plot its price over time, with a title.",
          "Same as task 1 with `ETH.csv`, then `df_eth.plot(x=\"time\", y=\"close\", title=\"...\")` and `plt.show()`."),
    *task(7, "Is funding usually positive?",
          "For **each coin** in `COINS`, print the % of hours with positive funding.",
          "A `for coin in COINS:` loop. Inside: load the CSV and compute `(d[\"fundingRate\"] > 0).mean()`. Format it with `f\"{value:.0%}\"`.",
          "for coin in COINS:\n    # load the coin's CSV and print its % of hours with positive funding\n    pass\n"),
    *task(8, "What does funding cost per year?",
          "For each coin, compute the **average hourly funding** and turn it into a **yearly %**. That's roughly what a long would pay (or a short would earn) holding the position for a year.\n\nWhich coin has the most expensive funding?",
          "Yearly ≈ hourly average × 24 × 365. Multiply by 100 to read it in %."),
    md("""## Your answers (write them here, double-click to edit)

1. **Gaps:** are there missing values? How many, and where?
2. **Outliers:** the biggest 1-hour move was on ___. Was it a real event? What happened?
3. **Funding:** is it usually positive or negative? Which coin pays the most per year?
4. **Something that surprised me:**
"""),
]

nb = nbf.v4.new_notebook()
nb.cells = cells
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, OUT)
print("created", OUT.name)
