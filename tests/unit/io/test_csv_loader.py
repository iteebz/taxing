from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from src.core.models import Council, Rent, Water
from src.io.csv_loader import load_csv


def test_load_csv_water():
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "water.csv"
        path.write_text("date,amount\n2025-07-01,100\n2025-08-01,100\n")

        items = load_csv(path, Water, 25)

        assert len(items) == 2
        assert items[0].date == date(2025, 7, 1)
        assert items[0].amount == Decimal("100")
        assert items[0].fy == 25


def test_load_csv_rent_with_tenant():
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "rent.csv"
        path.write_text("date,amount,tenant\n2025-07-01,1000,janice\n2025-08-01,1000,janice\n")

        items = load_csv(path, Rent, 25)

        assert len(items) == 2
        assert items[0].tenant == "janice"
        assert items[0].amount == Decimal("1000")


def test_load_csv_skip_comments():
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "council.csv"
        path.write_text("# Comment\ndate,amount\n2025-07-01,200\n# Another\n2025-08-01,200\n")

        items = load_csv(path, Council, 25)

        assert len(items) == 2


def test_load_csv_missing_file():
    path = Path("/nonexistent/water.csv")
    items = load_csv(path, Water, 25)
    assert items == []


def test_load_csv_empty_file():
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "water.csv"
        path.write_text("")

        items = load_csv(path, Water, 25)
        assert items == []


def test_load_csv_invalid_amount_skipped():
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "water.csv"
        path.write_text("date,amount\n2025-07-01,100\n2025-08-01,invalid\n2025-09-01,100\n")

        items = load_csv(path, Water, 25)

        assert len(items) == 1
        assert items[0].date == date(2025, 7, 1)
        assert items[0].amount == Decimal("100")


def test_load_csv_injects_fy():
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "water.csv"
        path.write_text("date,amount\n2025-07-01,100\n")

        items = load_csv(path, Water, 26)

        assert items[0].fy == 26
