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
