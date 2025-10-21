from pathlib import Path

import pandas as pd

from src.core.models import Transaction
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
        if bank == "beem":
            txn = converter(row.to_dict(), beem_username)
        else:
            txn = converter(row.to_dict())
        txns.append(txn)

    return txns


def ingest_dir(
    base_dir: str | Path,
    persons: list[str],
    beem_usernames: dict[str, str] | None = None,
) -> list[Transaction]:
    """
    Load all bank CSVs from directory structure.

    Structure: {base_dir}/{person}/raw/*.csv

    Args:
        base_dir: Base directory (e.g., 'fy25')
        persons: List of persons to load
        beem_usernames: Map person -> beem username

    Returns:
        Combined list of all transactions
    """
    beem_usernames = beem_usernames or {}
    all_txns = []

    for person in persons:
        person_dir = Path(base_dir) / person / "raw"
        if not person_dir.exists():
            continue

        for csv_file in sorted(person_dir.glob("*.csv")):
            bank = csv_file.stem
            beem_user = beem_usernames.get(person) if bank == "beem" else None
            txns = ingest_file(csv_file, bank, person, beem_user)
            all_txns.extend(txns)

    all_txns.sort(key=lambda t: (t.date, t.source_person, t.source_bank))
    return all_txns
