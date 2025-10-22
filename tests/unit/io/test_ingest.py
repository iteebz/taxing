import csv
import tempfile
from pathlib import Path

import pytest

from src.io.ingest import ingest_dir, ingest_file


@pytest.fixture
def anz_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(["01/10/2024", "100.50", "WOOLWORTHS SUPERMARKET"])
        writer.writerow(["02/10/2024", "-25.00", "BUNNINGS"])
        return Path(f.name)


@pytest.fixture
def wise_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "id",
                "status",
                "direction",
                "created_on",
                "finished_on",
                "source_fee_amount",
                "source_fee_currency",
                "target_fee_amount",
                "target_fee_currency",
                "source_name",
                "source_amount_after_fees",
                "source_currency",
                "target_name",
                "target_amount_after_fees",
                "target_currency",
                "exchange_rate",
                "reference",
                "batch",
            ]
        )
        writer.writerow(
            [
                "tx1",
                "COMPLETED",
                "in",
                "2024-10-01T10:00:00",
                "2024-10-01T10:05:00",
                "5",
                "AUD",
                "2",
                "USD",
                "source",
                "500",
                "AUD",
                "target",
                "300",
                "USD",
                "0.6",
                "ref",
                "batch",
            ]
        )
        return Path(f.name)


def test_anz(anz_csv):
    txns = ingest_file(anz_csv, "anz", "tyson")

    assert len(txns) == 2
    assert txns[0].amount == 100.50
    assert txns[0].individual == "tyson"
    assert txns[1].amount == -25.00


def test_wise(wise_csv):
    txns = ingest_file(wise_csv, "wise", "tyson")

    assert len(txns) == 1
    assert txns[0].bank == "wise"
    assert "deposit" in txns[0].description


def test_unknown_bank(anz_csv):
    with pytest.raises(ValueError, match="Unknown bank"):
        ingest_file(anz_csv, "unknown", "tyson")


def test_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        tyson_dir = base / "tyson" / "raw"
        janice_dir = base / "janice" / "raw"
        tyson_dir.mkdir(parents=True)
        janice_dir.mkdir(parents=True)

        with open(tyson_dir / "anz.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["01/10/2024", "100.00", "TEST1"])

        with open(janice_dir / "cba.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["01/10/2024", "50.00", "TEST2", "5000.00"])

        txns = ingest_dir(base, ["tyson", "janice"])

        assert len(txns) == 2
        assert txns[0].individual == "janice"
        assert txns[1].individual == "tyson"


def test_dir_missing_person():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        txns = ingest_dir(base, ["nonexistent"])
        assert txns == []
