"""Load holdings from CSV files."""

from decimal import Decimal
from pathlib import Path

from src.core.models import AUD, Holding, Money
from src.io.persist import dicts_from_csv


def load_holdings(base_dir: Path, person: str) -> list[Holding]:
    """Load holdings for a person from CSV file.

    Expected file: holdings.csv with columns:
    - ticker (str): e.g., "ASX:VAS"
    - units (Decimal): quantity held
    - cost_basis (Decimal): total purchase price
    - current_price (Decimal): current per-unit price

    Example:
        ticker,units,cost_basis,current_price
        ASX:SYI,100,5000,60
        ASX:VAS,50,2500,100
    """
    holdings_file = base_dir / "holdings.csv"
    if not holdings_file.exists():
        return []

    holdings = []
    for row in dicts_from_csv(holdings_file):
        try:
            ticker = row.get("ticker")
            units = row.get("units")
            cost_basis = row.get("cost_basis")
            current_price = row.get("current_price")

            if not all(
                [ticker, units is not None, cost_basis is not None, current_price is not None]
            ):
                continue

            holding = Holding(
                ticker=str(ticker),
                units=Decimal(str(units)),
                cost_basis=Money(Decimal(str(cost_basis)), AUD),
                current_price=Money(Decimal(str(current_price)), AUD),
            )
            holdings.append(holding)
        except Exception:
            pass

    return holdings
