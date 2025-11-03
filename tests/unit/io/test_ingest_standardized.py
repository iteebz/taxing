"""Tests for standardized I/O structure: data/raw/fy{year}/{person}/*.csv"""

import csv
import tempfile
from pathlib import Path

import pytest

from src.io.ingest import ingest_trades_year, ingest_year
from src.lib.paths import data_raw_fy_person


@pytest.fixture
def standard_structure():
    """Create standard data directory: data/raw/fy25/person/raw/"""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        you_dir = data_raw_fy_person(base, 25, "you")
        janice_dir = data_raw_fy_person(base, 25, "janice")

        you_txns = you_dir / "raw"
        janice_txns = janice_dir / "raw"

        you_txns.mkdir(parents=True)
        janice_txns.mkdir(parents=True)

        with open(you_txns / "anz.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["01/10/2024", "100.00", "WOOLWORTHS"])

        with open(janice_txns / "cba.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["02/10/2024", "50.00", "BUNNINGS", "5000.00"])

        with open(you_dir / "trades.csv", "w") as f:
            f.write("date,code,action,units,price,fee\n")
            f.write("2024-10-01,ASX:BHP,buy,100,50.00,10.00\n")

        with open(janice_dir / "trades.csv", "w") as f:
            f.write("date,code,action,units,price,fee\n")
            f.write("2024-10-01,ASX:CBA,buy,50,150.00,5.00\n")

        yield base


def test_year_loads_all(standard_structure):
    """ingest_year loads all persons for fiscal year"""
    txns = ingest_year(standard_structure, 25)

    assert len(txns) == 2  # 1 from you (anz), 1 from janice (cba)
    assert all(t.individual in ["you", "janice"] for t in txns)
    assert all(t.bank in ["anz", "cba"] for t in txns)


def test_year_missing():
    """ingest_year returns empty list for missing year"""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        txns = ingest_year(base, 99)
        assert txns == []


def test_trades_year_loads_all(standard_structure):
    """ingest_trades_year loads trades for all persons"""
    trades = ingest_trades_year(standard_structure, 25)

    assert len(trades) == 2
    assert trades[0].code in ["ASX:BHP", "ASX:CBA"]
    assert trades[0].individual in ["you", "janice"]


def test_year_filters_person(standard_structure):
    """ingest_year filters by person list"""
    txns = ingest_year(standard_structure, 25, persons=["you"])

    assert len(txns) == 1
    assert txns[0].individual == "you"


def test_trades_year_filters_person(standard_structure):
    """ingest_trades_year filters by person list"""
    trades = ingest_trades_year(standard_structure, 25, persons=["janice"])

    assert len(trades) == 1
    assert trades[0].individual == "janice"
