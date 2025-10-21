from decimal import Decimal
from pathlib import Path

import pandas as pd

from src.core.models import AUD, Money, Trade, Transaction
from src.io.converters import CONVERTERS

BANK_FIELD_SPECS = {
    "anz": {
        "fields": ["date_raw", "amount", "description_raw"],
        "skiprows": 0,
    },
    "cba": {
        "fields": ["date_raw", "amount", "description_raw", "balance"],
        "skiprows": 0,
    },
    "beem": {
        "fields": [
            "datetime",
            "type",
            "reference",
            "amount_str",
            "payer",
            "recipient",
            "message",
        ],
        "skiprows": 1,
    },
    "wise": {
        "fields": [
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
        ],
        "skiprows": 1,
    },
}


def _convert_row(row: dict, bank: str, converter, beem_username: str | None) -> Transaction:
    """Convert row with bank-specific logic."""
    if bank == "beem":
        return converter(row, beem_username)
    return converter(row)


def ingest_file(
    path: str | Path, bank: str, person: str, beem_username: str | None = None
) -> list[Transaction]:
    """
    Load bank CSV file and convert to Transaction list.

    Args:
        path: CSV file path
        bank: Bank code (anz, cba, beem, wise)
        person: Person identifier (for source_person field)
        beem_username: Beem username (required if bank='beem')

    Returns:
        List of Transaction objects
    """
    if bank not in BANK_FIELD_SPECS:
        raise ValueError(f"Unknown bank: {bank}")

    if bank == "beem" and not beem_username:
        raise ValueError("beem_username required for Beem bank")

    spec = BANK_FIELD_SPECS[bank]
    df = pd.read_csv(
        path,
        names=spec["fields"],
        header=None,
        skiprows=spec["skiprows"],
    )

    df["source_person"] = person

    converter = CONVERTERS[bank]
    txns = []

    for _, row in df.iterrows():
        txn = _convert_row(row.to_dict(), bank, converter, beem_username)
        txns.append(txn)

    return txns


def ingest_dir(
    base_dir: str | Path,
    persons: list[str] | None = None,
    beem_usernames: dict[str, str] | None = None,
) -> list[Transaction]:
    """
    Load all bank CSVs from directory structure.

    Supports two modes:
    1. Flat structure (pipeline): {base_dir}/*.csv, auto-detect person from source_person column
    2. Nested structure (multi-person): {base_dir}/{person}/raw/*.csv

    Args:
        base_dir: Base directory
        persons: List of persons to load (if None, scan flat structure)
        beem_usernames: Map person -> beem username

    Returns:
        Combined list of all transactions
    """
    beem_usernames = beem_usernames or {}
    all_txns = []
    base = Path(base_dir)

    if persons is None:
        for csv_file in sorted(base.glob("*.csv")):
            bank = csv_file.stem
            if bank not in CONVERTERS:
                continue

            df = pd.read_csv(csv_file)
            if "source_person" not in df.columns:
                continue

            converter = CONVERTERS[bank]
            for _, row in df.iterrows():
                person = row["source_person"]
                beem_user = beem_usernames.get(person) if bank == "beem" else None
                txn = _convert_row(row.to_dict(), bank, converter, beem_user)
                all_txns.append(txn)
    else:
        for person in persons:
            person_dir = base / person / "raw"
            if not person_dir.exists():
                continue

            for csv_file in sorted(person_dir.glob("*.csv")):
                bank = csv_file.stem
                beem_user = beem_usernames.get(person) if bank == "beem" else None
                txns = ingest_file(csv_file, bank, person, beem_user)
                all_txns.extend(txns)

    all_txns.sort(key=lambda t: (t.date, t.source_person, t.source_bank))
    return all_txns


def ingest_trades(path: str | Path, person: str) -> list[Trade]:
    """
    Load equity trades from CSV.

    Format: date, code, action, units, price, fee, source_person
    """
    df = pd.read_csv(path)
    if df.empty:
        return []

    trades = []
    for _, row in df.iterrows():
        trade = Trade(
            date=pd.to_datetime(row["date"]).date(),
            code=row["code"],
            action=row["action"],
            units=Decimal(row["units"]),
            price=Money(Decimal(row["price"]), AUD),
            fee=Money(Decimal(row["fee"]), AUD),
            source_person=person,
        )
        trades.append(trade)

    return trades


def ingest_trades_dir(base_dir: str | Path, persons: list[str] | None = None) -> list[Trade]:
    """
    Load all equity trades from directory structure.

    Looks for {base_dir}/{person}/raw/equity.csv
    """
    all_trades = []
    base = Path(base_dir)

    if persons is None:
        persons = [p.name for p in base.iterdir() if p.is_dir()]

    for person in sorted(persons):
        person_dir = base / person / "raw"
        if not person_dir.exists():
            continue

        equity_file = person_dir / "equity.csv"
        if equity_file.exists():
            trades = ingest_trades(equity_file, person)
            all_trades.extend(trades)

    all_trades.sort(key=lambda t: (t.code, t.date))
    return all_trades


def ingest_year(
    base_dir: str | Path, year: int, persons: list[str] | None = None
) -> list[Transaction]:
    """
    Load all transactions for a fiscal year using standardized structure.

    Structure: {base_dir}/data/fy{year}/{person}/raw/*.csv

    Args:
        base_dir: Root directory
        year: Fiscal year (e.g., 25 for FY2025)
        persons: List of persons to load (if None, auto-detect)

    Returns:
        Combined list of all transactions for the year
    """
    base = Path(base_dir)
    fy_dir = base / "data" / f"fy{year}"

    if not fy_dir.exists():
        return []

    if persons is None:
        persons = [p.name for p in fy_dir.iterdir() if p.is_dir() and p.name != "data"]

    return ingest_dir(fy_dir, persons=sorted(persons))


def ingest_trades_year(
    base_dir: str | Path, year: int, persons: list[str] | None = None
) -> list[Trade]:
    """
    Load all trades for a fiscal year using standardized structure.

    Structure: {base_dir}/data/fy{year}/{person}/trades.csv

    Args:
        base_dir: Root directory
        year: Fiscal year (e.g., 25 for FY2025)
        persons: List of persons to load (if None, auto-detect)

    Returns:
        Combined list of all trades for the year
    """
    base = Path(base_dir)
    fy_dir = base / "data" / f"fy{year}"

    if not fy_dir.exists():
        return []

    if persons is None:
        persons = [p.name for p in fy_dir.iterdir() if p.is_dir() and p.name != "data"]

    all_trades = []
    for person in sorted(persons):
        trades_file = fy_dir / person / "trades.csv"
        if trades_file.exists():
            trades = ingest_trades(trades_file, person)
            all_trades.extend(trades)

    all_trades.sort(key=lambda t: (t.code, t.date))
    return all_trades
