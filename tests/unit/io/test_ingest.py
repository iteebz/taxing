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
        writer.writerow(["header"])
        writer.writerow(
            [
                "tx1",
                "COMPLETED",
                "in",
                "2024-10-01T10:00:00",
                "2024-10-01T10:05:00",
                "0",
                "AUD",
                "0",
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


def test_ingest_anz_file(anz_csv):
    txns = ingest_file(anz_csv, "anz", "tyson")

    assert len(txns) == 2
    assert txns[0].amount.amount == 100.50
    assert txns[0].source_person == "tyson"
    assert txns[1].amount.amount == -25.00


def test_ingest_wise_file(wise_csv):
    txns = ingest_file(wise_csv, "wise", "tyson")

    assert len(txns) == 1
    assert txns[0].source_bank == "wise"
    assert "deposit" in txns[0].description


def test_ingest_unknown_bank(anz_csv):
    with pytest.raises(ValueError, match="Unknown bank"):
        ingest_file(anz_csv, "unknown", "tyson")


def test_ingest_beem_requires_username(anz_csv):
    with pytest.raises(ValueError, match="beem_username required"):
        ingest_file(anz_csv, "beem", "tyson")


def test_ingest_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        tyson_dir = base / "tyson" / "raw"
        jaynice_dir = base / "jaynice" / "raw"
        tyson_dir.mkdir(parents=True)
        jaynice_dir.mkdir(parents=True)

        with open(tyson_dir / "anz.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["01/10/2024", "100.00", "TEST1"])

        with open(jaynice_dir / "cba.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["01/10/2024", "50.00", "TEST2", "5000.00"])

        txns = ingest_dir(base, ["tyson", "jaynice"])

        assert len(txns) == 2
        assert txns[0].source_person == "jaynice"
        assert txns[1].source_person == "tyson"


def test_ingest_dir_missing_person():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        txns = ingest_dir(base, ["nonexistent"])
        assert txns == []
