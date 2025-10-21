"""Load positions from CSV files."""

from decimal import Decimal
from pathlib import Path

from src.core.models import Position
from src.io.persist import dicts_from_csv


def load_positions(base_dir: Path, person: str) -> list[Position]:
    """Load positions for a person from CSV file.

    Expected file: positions.csv with columns:
    - ticker (str): e.g., "ASX:VAS"
    - units (Decimal): quantity held
    - total_cost_basis (Decimal): total purchase price

    Example:
        ticker,units,total_cost_basis
        ASX:SYI,100,5000
        ASX:VAS,50,2500
    """
    positions_file = base_dir / "positions.csv"
    if not positions_file.exists():
        return []

    positions = []
    for row in dicts_from_csv(positions_file):
        try:
            ticker = row.get("ticker")
            units = row.get("units")
            total_cost_basis = row.get("total_cost_basis")

            if not all([ticker, units is not None, total_cost_basis is not None]):
                continue

            position = Position(
                ticker=str(ticker),
                units=Decimal(str(units)),
                total_cost_basis=Decimal(str(total_cost_basis)),
            )
            positions.append(position)
        except Exception:
            pass

    return positions
