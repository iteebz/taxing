"""Load property expenses from CSV files."""

from decimal import Decimal
from pathlib import Path

from src.core.models import PropertyExpense


def load_property_expenses(base_dir: Path, fy: int, person: str) -> list[PropertyExpense]:
    """Load property expenses (rent, water, council, strata) for a person.

    Expected structure:
    - {base_dir}/archive/{fy}/{person}/property/rent.csv
    - {base_dir}/archive/{fy}/{person}/property/water.csv
    - {base_dir}/archive/{fy}/{person}/property/council.csv
    - {base_dir}/archive/{fy}/{person}/property/strata.csv

    Each CSV has simple format: amount (one value per row)
    """
    property_dir = base_dir / "archive" / str(fy) / person / "property"
    if not property_dir.exists():
        return []

    expenses = []
    for exp_type in ["rent", "water", "council", "strata"]:
        csv_file = property_dir / f"{exp_type}.csv"
        if not csv_file.exists():
            continue

        with open(csv_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    amount = Decimal(line)
                    expenses.append(PropertyExpense(exp_type, amount))
                except Exception:
                    pass

    return expenses
