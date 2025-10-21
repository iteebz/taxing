from decimal import Decimal
from pathlib import Path

from src.core.models import (
    CapitalWorks,
    Council,
    Interest,
    Property,
    Rent,
    Strata,
    Water,
)
from src.io.csv_loader import load_csv


def load_property(
    base_dir: Path,
    fy: int,
    address: str,
    owner: str,
    occupancy_pct: Decimal,
) -> Property:
    """Load complete property record from CSV files.
    
    Expected structure:
    archive/{fy}/{address}/
      ├── rent.csv (date, amount, tenant)
      ├── water.csv (date, amount)
      ├── council.csv (date, amount)
      ├── strata.csv (date, amount)
      ├── interest.csv (date, amount, loan_id)
      └── capital_works.csv (date, amount, description, life_years, asset_id)
    """
    prop_dir = base_dir / str(fy) / address

    return Property(
        address=address,
        owner=owner,
        fy=fy,
        occupancy_pct=occupancy_pct,
        rents=load_csv(prop_dir / "rent.csv", Rent, fy),
        waters=load_csv(prop_dir / "water.csv", Water, fy),
        councils=load_csv(prop_dir / "council.csv", Council, fy),
        stratas=load_csv(prop_dir / "strata.csv", Strata, fy),
        capital_works=load_csv(prop_dir / "capital_works.csv", CapitalWorks, fy),
        interests=load_csv(prop_dir / "interest.csv", Interest, fy),
    )
