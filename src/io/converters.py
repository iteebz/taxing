from datetime import date
from decimal import Decimal

import pandas as pd

from src.core.models import AUD, Currency, Money, Transaction


def _parse_date(date_str: str, dayfirst: bool = True) -> date:
    """Parse date string with format detection."""
    dt = pd.to_datetime(date_str, errors="coerce", dayfirst=dayfirst)
    if pd.isna(dt):
        raise ValueError(f"Invalid date: {date_str}")
    return dt.date()


def _sanitize_desc(desc: str) -> str:
    """Normalize description: lowercase, strip punctuation."""
    return desc.lower().strip().replace('"', "").replace("-", " ").replace("'", "")


def _std_bank(row: dict, bank: str) -> Transaction:
    """Convert standard bank CSV row (ANZ, CBA) to Transaction."""
    return Transaction(
        date=_parse_date(row["date_raw"], dayfirst=True),
        amount=Money(Decimal(str(row["amount"])), AUD),
        description=_sanitize_desc(row["description_raw"]),
        source_bank=bank,
        source_person=row["source_person"],
    )


def anz(row: dict) -> Transaction:
    """Convert ANZ CSV row to Transaction."""
    return _std_bank(row, "anz")


def cba(row: dict) -> Transaction:
    """Convert CBA CSV row to Transaction."""
    return _std_bank(row, "cba")


def beem(row: dict, beem_username: str) -> Transaction:
    """Convert Beem CSV row to Transaction."""
    abs_amt = Decimal(str(row["amount_str"]).replace("$", "").replace(",", ""))
    if row["payer"] == beem_username:
        amt = -abs_amt
    else:
        amt = abs_amt

    direction = "from" if row["recipient"] == beem_username else "to"
    target = row["payer"] if row["recipient"] == beem_username else row["recipient"]
    desc = f"beem {row['type'].lower()} {direction} {target} for {row['message']}"

    return Transaction(
        date=_parse_date(row["datetime"], dayfirst=False),
        amount=Money(amt, AUD),
        description=_sanitize_desc(desc),
        source_bank="beem",
        source_person=row["source_person"],
    )


def wise(row: dict) -> Transaction:
    """Convert Wise CSV row to Transaction."""
    direction = row["direction"].lower()
    target_fee = Decimal(str(row.get("target_fee_amount", 0) or 0))
    target_amt = Decimal(str(row["target_amount_after_fees"]))
    total = target_amt + target_fee

    if direction == "in":
        amt = total
    elif direction in ["neutral", "cancelled"]:
        amt = Decimal("0")
    else:  # out
        amt = -total

    currency_code = row["target_currency"].upper()

    if direction == "in":
        desc = f"wise deposit in {currency_code}"
    elif direction == "neutral":
        desc = f"wise conversion from {row['source_currency']} to {currency_code}"
    elif direction == "cancelled":
        desc = f"wise cancelled payment to {row['target_name']}"
    else:
        desc = f"wise payment in {currency_code} to {row['target_name']}"

    cur: Currency = Currency(currency_code) if currency_code != "AUD" else AUD

    return Transaction(
        date=_parse_date(row["created_on"], dayfirst=False),
        amount=Money(amt, cur),
        description=_sanitize_desc(desc),
        source_bank="wise",
        source_person=row["source_person"],
    )


CONVERTERS = {
    "anz": anz,
    "cba": cba,
    "beem": beem,
    "wise": wise,
}
