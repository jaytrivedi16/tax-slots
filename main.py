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

def input_files(path: Path):
    """
    tax_lot_holdings_file:
    ticker, no-shares-purchased, purchase-price, purchase-date
    """
    lots = []
    with path.open(newline=="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            lots.append((
                row['ticker'],
                Decimal(row['no-shares-purchased']),
                Decimal(row['purchase-price']),
                datetime.strptime(row['purchase-date'], '%Y-%m-%d').date()
            ))

def load_holdings