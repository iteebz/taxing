from datetime import date
from decimal import Decimal

import pandas as pd

from src.core.models import Trade, Transaction
from src.lib.currency import to_aud


def _parse_date(date_str: str, dayfirst: bool = True) -> date:
    """Parse date string with format detection."""
    dt = pd.to_datetime(date_str, errors="coerce", dayfirst=dayfirst)
    if pd.isna(dt):
        raise ValueError(f"Invalid date: {date_str}")
    return dt.date()


def _sanitize_desc(desc: str) -> str:
    """Normalize description: lowercase, strip punctuation."""
    return desc.lower().strip().replace('"', "").replace("-", " ").replace("'", "")


def _std_txn(
    row: dict, bank: str, date_key: str = "date_raw", dayfirst: bool = True, account: str | None = None
) -> Transaction:
    """Convert standard bank CSV row to Transaction."""
    return Transaction(
        date=_parse_date(row[date_key], dayfirst=dayfirst),
        amount=Decimal(str(row["amount"])),
        description=_sanitize_desc(row["description_raw"]),
        bank=bank,
        individual=row["individual"],
        account=account,
    )


def anz(row: dict, account: str | None = None) -> Transaction:
    """Convert ANZ CSV row to Transaction."""
    return _std_txn(row, "anz", account=account)


def cba(row: dict, account: str | None = None) -> Transaction:
    """Convert CBA CSV row to Transaction."""
    return _std_txn(row, "cba", account=account)


def beem(row: dict, beem_username: str, account: str | None = None) -> Transaction:
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
        amount=amt,
        description=_sanitize_desc(desc),
        bank="beem",
        individual=row["individual"],
        account=account,
    )


def wise(row: dict, account: str | None = None) -> Transaction:
    """Convert Wise CSV row to Transaction, converting to AUD."""
    direction = row["direction"].lower()
    target_currency = row.get("target_currency", "").upper()
    source_currency = row.get("source_currency", "").upper()

    if direction in ["neutral", "cancelled"]:
        amt = Decimal("0")
        desc = f"wise {direction} conversion from {source_currency} to {target_currency}"
    else:
        target_fee_str = row.get("target_fee_amount", "0") or "0"
        try:
            target_fee = Decimal(str(target_fee_str))
        except (ValueError, TypeError):
            target_fee = Decimal("0")
        try:
            target_amt = Decimal(str(row["target_amount_after_fees"]))
        except (ValueError, TypeError):
            target_amt = Decimal("0")
        exchange_rate = Decimal(str(row.get("exchange_rate", "1")))

        if direction == "in":
            total_amt = target_amt + target_fee
            if target_currency != "AUD":
                amt = to_aud(total_amt, target_currency, exchange_rate)
            else:
                amt = total_amt
            desc = f"wise deposit from {source_currency} to {target_currency}"
        else:  # out
            total_amt = target_amt + target_fee
            if target_currency != "AUD":
                amt = -to_aud(total_amt, target_currency, exchange_rate)
            else:
                amt = -total_amt
            desc = f"wise payment in {target_currency} to {row.get('target_name', 'unknown')}"

    return Transaction(
        date=_parse_date(row["created_on"], dayfirst=False),
        amount=amt,
        description=_sanitize_desc(desc),
        bank="wise",
        individual=row["individual"],
        account=account,
    )


def stake_activity(row: dict) -> Trade:
    """Convert Stake activity (trade) row to Trade, converting to AUD."""
    currency = row.get("Currency", "AUD").upper()
    exchange_rate = Decimal(str(row.get("AUD/USD rate", "1").replace("$", "")))

    price_usd = Decimal(str(row["Avg. Price"]))
    fee_usd = Decimal(str(row.get("Fees", 0) or 0))

    if currency != "AUD":
        price = to_aud(price_usd, currency, exchange_rate)
        fee = to_aud(fee_usd, currency, exchange_rate)
    else:
        price = price_usd
        fee = fee_usd

    side = row["Side"].lower()
    action = "sell" if side == "sell" else "buy"

    return Trade(
        date=_parse_date(row["Trade Date"], dayfirst=False),
        code=row["Symbol"],
        action=action,
        units=Decimal(str(row["Units"])).copy_abs(),
        price=price,
        fee=fee,
        individual=row.get("individual", "tyson"),
    )


def stake_dividend(row: dict) -> Transaction:
    """Convert Stake dividend row to Transaction, converting to AUD."""
    currency = row.get("Currency", "AUD").upper()
    exchange_rate = Decimal(str(row.get("AUD/USD rate", "1")))

    net_amount = Decimal(str(row["Net Amount"]))

    if currency != "AUD":
        amount = to_aud(net_amount, currency, exchange_rate)
    else:
        amount = net_amount

    ticker = row["Symbol"]
    desc = f"dividend {ticker.lower()} usd"

    return Transaction(
        date=_parse_date(row["Payment Date"], dayfirst=False),
        amount=amount,
        description=_sanitize_desc(desc),
        bank="stake",
        individual=row.get("individual", "tyson"),
    )


BANK_REGISTRY = {
    "anz": {
        "converter": anz,
        "fields": ["date_raw", "amount", "description_raw"],
        "skiprows": 0,
        "requires_beem_user": False,
    },
    "cba": {
        "converter": cba,
        "fields": ["date_raw", "amount", "description_raw", "balance"],
        "skiprows": 0,
        "requires_beem_user": False,
    },
    "beem": {
        "converter": beem,
        "fields": ["datetime", "type", "reference", "amount_str", "payer", "recipient", "message"],
        "skiprows": 1,
        "requires_beem_user": True,
    },
    "wise": {
        "converter": wise,
        "fields": [
            "id", "status", "direction", "created_on", "finished_on",
            "source_fee_amount", "source_fee_currency",
            "target_fee_amount", "target_fee_currency", "source_name",
            "source_amount_after_fees", "source_currency", "target_name",
            "target_amount_after_fees", "target_currency", "exchange_rate",
            "reference", "batch",
        ],
        "skiprows": 1,
        "requires_beem_user": False,
    },
}

CONVERTERS = {
    code: cfg["converter"]
    for code, cfg in BANK_REGISTRY.items()
    if code in ["anz", "cba", "beem", "wise"]
}
