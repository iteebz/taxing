from collections import Counter
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pandas as pd

from src.core.models import Trade, Transaction
from src.io.converters import BANK_REGISTRY, CONVERTERS
from src.lib.paths import data_raw, data_raw_fy


def _parse_bank_and_account(filename: str) -> tuple[str, str | None]:
    """Parse bank code and account from filename.

    Examples:
        "anz.csv" → ("anz", None)
        "anz_hl.csv" → ("anz", "hl")
    """
    stem = Path(filename).stem
    parts = stem.split("_", 1)
    bank = parts[0]
    account = parts[1] if len(parts) > 1 else None
    return bank, account


def _convert_row(
    row: dict, bank: str, converter, beem_username: str | None, account: str | None = None
) -> Transaction:
    """Convert row with bank-specific logic."""
    if bank == "beem":
        return converter(row, beem_username, account=account)
    return converter(row, account=account)


def _infer_beem_user(path: str | Path) -> str:
    """Infer beem account owner from payer/recipient frequency."""
    df = pd.read_csv(path)
    users = Counter()
    for payer in df.get("Payer", []):
        if pd.notna(payer):
            users[payer] += 1
    for recipient in df.get("Recipient", []):
        if pd.notna(recipient):
            users[recipient] += 1
    return users.most_common(1)[0][0]


def ingest_file(
    path: str | Path, bank: str, individual: str, beem_username: str | None = None
) -> list[Transaction]:
    """
    Load bank CSV file and convert to Transaction list.

    Args:
        path: CSV file path
        bank: Bank code (anz, cba, beem, wise)
        individual: Individual identifier (for individual field)
        beem_username: Beem username (inferred from data if not provided for beem)

    Returns:
        List of Transaction objects
    """
    if bank not in BANK_REGISTRY:
        raise ValueError(f"Unknown bank: {bank}")

    cfg = BANK_REGISTRY[bank]

    if cfg["requires_beem_user"]:
        beem_username = beem_username or _infer_beem_user(path)

    df = pd.read_csv(
        path,
        names=cfg["fields"],
        header=None,
        skiprows=cfg["skiprows"],
    )

    df["individual"] = individual

    converter = cfg["converter"]
    txns = []

    for _, row in df.iterrows():
        txn = _convert_row(row.to_dict(), bank, converter, beem_username, account=None)
        txns.append(txn)

    return txns


def ingest_dir(
    base_dir: str | Path,
    persons: list[str] | None = None,
) -> list[Transaction]:
    """
    Load all bank CSVs from directory structure.

    Supports two modes:
    1. Flat structure (pipeline): {base_dir}/*.csv, auto-detect person from individual column
    2. Nested structure (multi-person): {base_dir}/{person}/raw/*.csv

    Args:
        base_dir: Base directory
        persons: List of persons to load (if None, scan flat structure)

    Returns:
        Combined list of all transactions
    """
    all_txns = []
    base = Path(base_dir)

    if persons is None:
        for csv_file in sorted(base.glob("*.csv")):
            bank = csv_file.stem
            if bank not in CONVERTERS:
                continue

            df = pd.read_csv(csv_file)
            if "individual" not in df.columns:
                continue

            converter = CONVERTERS[bank]
            for _, row in df.iterrows():
                individual = row["individual"]
                txn = _convert_row(row.to_dict(), bank, converter, None)
                all_txns.append(txn)
    else:
        for individual in persons:
            individual_dir = base / individual / "raw"
            if not individual_dir.exists():
                continue

            for csv_file in sorted(individual_dir.glob("*.csv")):
                bank, account = _parse_bank_and_account(csv_file.name)
                if bank not in BANK_REGISTRY:
                    continue
                txns = ingest_file(csv_file, bank, individual)
                if account:
                    txns = [replace(t, account=account) for t in txns]
                all_txns.extend(txns)

    all_txns.sort(key=lambda t: (t.date, t.individual, t.bank))
    return all_txns


def ingest_trades(path: str | Path, individual: str) -> list[Trade]:
    """
    Load equity trades from CSV.

    Format: date, code, action, units, price, fee, individual
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
            price=Decimal(row["price"]),
            fee=Decimal(row["fee"]),
            individual=individual,
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

    for individual in sorted(persons):
        individual_dir = base / individual / "raw"
        if not individual_dir.exists():
            continue

        equity_file = individual_dir / "equity.csv"
        if equity_file.exists():
            trades = ingest_trades(equity_file, individual)
            all_trades.extend(trades)

    all_trades.sort(key=lambda t: (t.code, t.date))
    return all_trades


def ingest_year(
    base_dir: str | Path,
    year: int,
    persons: list[str] | None = None,
) -> list[Transaction]:
    """
    Load all transactions for a fiscal year.

    Structure: {base_dir}/data/raw/fy{year}/{person}/*.csv

    Args:
        base_dir: Root directory
        year: Fiscal year (e.g., 25 for FY2025)
        persons: List of persons to load (if None, auto-detect)

    Returns:
        Combined list of all transactions for the year
    """
    fy_dir = data_raw_fy(base_dir, year)

    if not fy_dir.exists():
        return []

    if persons is None:
        persons = [p.name for p in fy_dir.iterdir() if p.is_dir()]

    return ingest_dir(fy_dir, persons=sorted(persons))


def ingest_all_years(
    base_dir: str | Path,
    persons: list[str] | None = None,
) -> list[Transaction]:
    """
    Load all transactions across all fiscal years.

    Structure: {base_dir}/data/raw/fy*/{person}/*.csv

    Args:
        base_dir: Root directory
        persons: List of persons to load (if None, auto-detect from all years)

    Returns:
        Combined list of all transactions from all years
    """
    raw_dir = data_raw(base_dir)

    if not raw_dir.exists():
        return []

    all_txns = []
    for fy_dir in sorted(raw_dir.glob("fy*")):
        if not fy_dir.is_dir():
            continue
        try:
            year = int(fy_dir.name[2:])
        except ValueError:
            continue

        txns = ingest_year(base_dir, year, persons=persons)
        all_txns.extend(txns)

    return all_txns


def ingest_trades_year(
    base_dir: str | Path, year: int, persons: list[str] | None = None
) -> list[Trade]:
    """
    Load all trades for a fiscal year using standardized structure.

    Structure: {base_dir}/data/raw/fy{year}/{person}/trades.csv

    Args:
        base_dir: Root directory
        year: Fiscal year (e.g., 25 for FY2025)
        persons: List of persons to load (if None, auto-detect)

    Returns:
        Combined list of all trades for the year
    """
    fy_dir = data_raw_fy(base_dir, year)

    if not fy_dir.exists():
        return []

    if persons is None:
        persons = [p.name for p in fy_dir.iterdir() if p.is_dir()]

    all_trades = []
    for individual in sorted(persons):
        trades_file = fy_dir / individual / "trades.csv"
        if trades_file.exists():
            trades = ingest_trades(trades_file, individual)
            all_trades.extend(trades)

    all_trades.sort(key=lambda t: (t.code, t.date))
    return all_trades


def ingest_all_trades(
    base_dir: str | Path,
    persons: list[str] | None = None,
) -> list[Trade]:
    """
    Load all trades across all fiscal years.

    Structure: {base_dir}/data/fy*/person/trades.csv

    Args:
        base_dir: Root directory
        persons: List of persons to load (if None, auto-detect)

    Returns:
        Combined list of all trades from all years
    """
    base = Path(base_dir)
    data_dir = base / "data"

    if not data_dir.exists():
        return []

    all_trades = []
    for fy_dir in sorted(data_dir.glob("fy*")):
        if not fy_dir.is_dir():
            continue
        try:
            year = int(fy_dir.name[2:])
        except ValueError:
            continue

        trades = ingest_trades_year(base, year, persons=persons)
        all_trades.extend(trades)

    return all_trades
