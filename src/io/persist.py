from decimal import Decimal
from pathlib import Path

import pandas as pd

from src.core.models import Money, Transaction


def txns_to_csv(txns: list[Transaction], path: str | Path) -> None:
    """Write transactions to CSV."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "date",
        "amount",
        "currency",
        "description",
        "source_bank",
        "source_person",
        "category",
        "is_transfer",
    ]

    data = [
        {
            "date": t.date.isoformat(),
            "amount": str(t.amount.amount),
            "currency": t.amount.currency,
            "description": t.description,
            "source_bank": t.source_bank,
            "source_person": t.source_person,
            "category": ",".join(sorted(t.category)) if t.category else "",
            "is_transfer": t.is_transfer,
        }
        for t in txns
    ]

    df = pd.DataFrame(data, columns=columns) if data else pd.DataFrame(columns=columns)
    df.to_csv(path, index=False)


def txns_from_csv(path: str | Path) -> list[Transaction]:
    """Read transactions from CSV."""
    df = pd.read_csv(path)
    if df.empty:
        return []

    txns = []

    for _, row in df.iterrows():
        cat_str = row["category"]
        category = None
        if isinstance(cat_str, str) and cat_str.strip():
            category = set(cat_str.split(","))

        txn = Transaction(
            date=pd.to_datetime(row["date"]).date(),
            amount=Money(Decimal(row["amount"]), row["currency"]),
            description=row["description"],
            source_bank=row["source_bank"],
            source_person=row["source_person"],
            category=category,
            is_transfer=bool(row["is_transfer"]),
        )
        txns.append(txn)

    return txns


def weights_to_csv(weights: dict[str, float], path: str | Path) -> None:
    """Write weights to CSV."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame([{"category": cat, "weight": w} for cat, w in weights.items()])
    df.to_csv(path, index=False)


def weights_from_csv(path: str | Path) -> dict[str, float]:
    """Read weights from CSV."""
    df = pd.read_csv(path)
    return {row["category"]: row["weight"] for _, row in df.iterrows()}


def deductions_to_csv(deductions: dict[str, Money], path: str | Path) -> None:
    """Write deductions to CSV."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    data = [
        {"category": cat, "amount": str(money.amount), "currency": money.currency}
        for cat, money in deductions.items()
    ]

    df = pd.DataFrame(data) if data else pd.DataFrame(columns=["category", "amount", "currency"])
    df.to_csv(path, index=False)


def deductions_from_csv(path: str | Path) -> dict[str, Money]:
    """Read deductions from CSV."""
    df = pd.read_csv(path)
    if df.empty:
        return {}

    return {
        row["category"]: Money(Decimal(row["amount"]), row["currency"])
        for _, row in df.iterrows()
    }


def summary_to_csv(summary: dict[str, Money], path: str | Path) -> None:
    """Write category spend summary to CSV."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    data = [
        {"category": cat, "total": str(money.amount), "currency": money.currency}
        for cat, money in summary.items()
    ]

    df = pd.DataFrame(data) if data else pd.DataFrame(columns=["category", "total", "currency"])
    df.to_csv(path, index=False)


def summary_from_csv(path: str | Path) -> dict[str, Money]:
    """Read category spend summary from CSV."""
    df = pd.read_csv(path)
    if df.empty:
        return {}

    return {
        row["category"]: Money(Decimal(row["total"]), row["currency"])
        for _, row in df.iterrows()
    }
