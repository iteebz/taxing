import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.core.models import AUD, Money, Summary, Transaction
from src.io import from_csv, to_csv, weights_from_csv, weights_to_csv


def test_txns_roundtrip(sample_txn, sample_txn_with_category):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "txns.csv"

        txns = [sample_txn, sample_txn_with_category]
        to_csv(txns, path)

        loaded = from_csv(path, Transaction)

        assert len(loaded) == 2
        assert loaded[0].date == sample_txn.date
        assert loaded[0].amount.amount == sample_txn.amount.amount
        assert loaded[1].category == {"groceries", "supermarkets"}


def test_txns_csv_creates_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "subdir" / "txns.csv"

        txn = Transaction(
            date=date(2024, 10, 1),
            amount=Money(Decimal("100.00"), AUD),
            description="test",
            source_bank="anz",
            source_person="tyson",
        )

        to_csv([txn], path)
        assert path.exists()


def test_weights_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "weights.csv"
        weights = {
            "home_office": 0.5,
            "mobile": 0.1,
            "therapy": 1.0,
        }

        weights_to_csv(weights, path)
        loaded = weights_from_csv(path)

        assert loaded == weights


def test_txns_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "txns.csv"
        to_csv([], path, Transaction)
        loaded = from_csv(path, Transaction)
        assert loaded == []


def test_txns_no_cat():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "txns.csv"

        txn = Transaction(
            date=date(2024, 10, 1),
            amount=Money(Decimal("50.00"), AUD),
            description="uncategorized",
            source_bank="wise",
            source_person="tyson",
            category=None,
        )

        to_csv([txn], path)
        loaded = from_csv(path, Transaction)

        assert loaded[0].category is None


def test_summary_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "summary.csv"
        summary = [
            Summary("groceries", Decimal("250.50"), Decimal("0")),
            Summary("transport", Decimal("75.25"), Decimal("0")),
        ]

        to_csv(summary, path)
        loaded = from_csv(path, Summary)

        assert len(loaded) == 2
        assert loaded[0].category == "groceries"
        assert loaded[0].credit_amount == Decimal("250.50")


def test_summary_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "summary.csv"
        to_csv([], path, Summary)
        loaded = from_csv(path, Summary)
        assert loaded == []
