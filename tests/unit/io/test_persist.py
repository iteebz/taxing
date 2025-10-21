import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.core.models import AUD, Money, Transaction
from src.io.persist import (
    summary_from_csv,
    summary_to_csv,
    txns_from_csv,
    txns_to_csv,
    weights_from_csv,
    weights_to_csv,
)


def test_txns_roundtrip(sample_txn, sample_txn_with_category):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "txns.csv"

        txns = [sample_txn, sample_txn_with_category]
        txns_to_csv(txns, path)

        loaded = txns_from_csv(path)

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

        txns_to_csv([txn], path)
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
        txns_to_csv([], path)
        loaded = txns_from_csv(path)
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

        txns_to_csv([txn], path)
        loaded = txns_from_csv(path)

        assert loaded[0].category is None


def test_summary_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "summary.csv"
        summary = {
            "groceries": Money(Decimal("250.50"), AUD),
            "transport": Money(Decimal("75.25"), AUD),
        }

        summary_to_csv(summary, path)
        loaded = summary_from_csv(path)

        assert loaded == summary


def test_summary_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "summary.csv"
        summary_to_csv({}, path)
        loaded = summary_from_csv(path)
        assert loaded == {}
