import typer
import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Tuple
from __future__ import annotations


app = typer.Typer(help="Tax-lot relief CLI with FIFO/LIFO/HIFO selection via Typer.")  #I have used Typer to create a CLI application.

class Algo (str, Enum): # Defined a class called Algo that will hold the different algorithms for tax-lot relief.
    FIFO = "FIFO"
    LIFO = "LIFO"
    HIFO = "HIFO"

def f_qty(x: Decimal) -> str:
    return format(x, '.1f')
def f_price(x: Decimal) -> str:
    return format(x, '.2f')

#Creating the classes and functions to handle input files and tax-lot selection algorithms.
def input_files(path: Path):
    """
    tax_lot_holdings_file:
    ticker, no-shares-purchased, purchase-price, purchase-date
    """
    lots = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            lots.append({
                "ticker": r["ticker"].strip().upper(),
                "qty_remaining": Decimal(r["no-shares-purchased"].strip()),
                "purchase_price": Decimal(r["purchase-price"].strip()),
                "purchase_date": datetime.fromisoformat(r["purchase-date"].strip()),
            })
    lots.sort(key=lambda x: (x["ticker"], x["purchase_date"]))
    return lots

def load_sells(path: Path) -> List[Tuple[str, Decimal]]:
    """
    sell_list_file:
    ticker, no-shares-to-sell
    """
    sells: List[Tuple[str, Decimal]] = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            sells.append((r["ticker"].strip().upper(), Decimal(r["no-shares-to-sell"].strip())))
    return sells

#Algorithm to select tax lots based on the chosen method (FIFO, LIFO, HIFO)
def select_fifo(ticker, lots):
    cands = [l for l in lots if l["ticker"] == ticker and l["qty_remaining"] > 0]
    return sorted(cands, key=lambda l: l["purchase_date"])

def select_lifo(ticker, lots):
    cands = [l for l in lots if l["ticker"] == ticker and l["qty_remaining"] > 0]
    return sorted(cands, key=lambda l: l["purchase_date"], reverse=True)

def select_hifo(ticker, lots):
    cands = [l for l in lots if l["ticker"] == ticker and l["qty_remaining"] > 0]
    return sorted(cands, key=lambda l: l["purchase_price"], reverse=True)

ALGOS = {
    Algo.fifo: select_fifo,
    Algo.lifo: select_lifo,
    Algo.hifo: select_hifo,
}

def relieve(lots, sells, algo: Algo):
    select_fn = ALGOS[algo]
    out_rows = []  # [ticker, orig_hold, purch_price, purch_date, relvd_hold, amt_relvd]
    for ticker, sell_qty in sells:
        remaining = sell_qty
        while remaining > 0:
            cands = select_fn(ticker, lots)
            if not cands:
                raise ValueError(
                    f"Sell exceeds available quantity for {ticker}: requested {sell_qty}, short by {remaining}"
                )
            lot = cands[0]
            take = min(remaining, lot["qty_remaining"])
            orig_hold = lot["qty_remaining"]
            lot["qty_remaining"] = orig_hold - take
            remaining -= take
            out_rows.append([
                ticker,
                orig_hold,
                lot["purchase_price"],
                lot["purchase_date"].date().isoformat(),
                lot["qty_remaining"],
                take,
            ])
    return out_rows

#Final output table
def print_table(rows):
    headers = ["Tick", "Orig Hold", "Purch Price", "Purch Date", "Relvd Hold", "Amt Relvd"]
    srows = []
    for t, orig, price, pdate, relvd, amt in rows:
        srows.append([
            t,
            f_qty(orig),
            f_price(price),
            pdate,
            f_qty(relvd),
            f_qty(amt),
        ])

    widths = [len(h) for h in headers]
    for r in srows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(vals):
        return "  ".join([
            vals[0].ljust(widths[0]),  # text left
            vals[1].rjust(widths[1]),  # numbers right
            vals[2].rjust(widths[2]),
            vals[3].rjust(widths[3]),
            vals[4].rjust(widths[4]),
            vals[5].rjust(widths[5]),
        ])

    print(fmt_row(headers))
    for r in srows:
        print(fmt_row(r))

# ----- Typer CLI -----
@app.command()
def run(
    holdings: Path = typer.Option(..., exists=True, readable=True, help="Path to tax_lot_holdings_file CSV"),
    sells: Path = typer.Option(..., exists=True, readable=True, help="Path to sell_list_file CSV"),
    algo: Algo = typer.Option(None, help="Algorithm: fifo | lifo | hifo", prompt=True),
):
    """
    Apply lot relief per algorithm and print the aligned table.
    """
    lots = load_holdings(holdings)
    sell_list = load_sells(sells)
    rows = relieve(lots, sell_list, algo)
    print_table(rows)

if __name__ == "__main__":
    app()