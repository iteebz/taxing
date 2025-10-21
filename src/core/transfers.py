from dataclasses import dataclass
from decimal import Decimal

from src.core.models import Money, Transaction


@dataclass(frozen=True)
class Transfer:
    """Represents a detected transfer between parties."""

    from_person: str
    to_person: str
    amount: Money
    date_first: str
    date_last: str
    txn_count: int


def is_transfer(txn: Transaction) -> bool:
    """Check if transaction is a transfer (marked via classify or heuristics).

    Transfer: marked with 'transfers' category via rules/transfers.txt
    """
    return txn.category is not None and "transfers" in txn.category


def extract_recipient(description: str) -> str | None:
    """Extract recipient name from transfer description.

    Patterns:
    - "transfer to janice quach" -> "janice quach"
    - "transfer to janice" -> "janice"
    - "direct credit 141000 janice quach" -> "janice quach"
    """
    desc_lower = description.lower()

    if "transfer to" in desc_lower:
        after = desc_lower.split("transfer to")[-1].strip()
        if after and not any(x in after for x in ["other bank", "savings", "cash"]):
            return after.replace("app", "").replace("netbank", "").strip()

    if "direct credit" in desc_lower:
        after = desc_lower.split("direct credit")[-1].strip()
        parts = after.split()
        if len(parts) >= 2:
            return " ".join(parts[1:]).strip()

    return None


def reconcile_transfers(
    txns: list[Transaction],
) -> dict[tuple[str, str], Transfer]:
    """Match and reconcile transfers between persons.

    Groups transfers by (from_person, to_person) pair.
    Returns: dict of (from_person, to_person) -> Transfer (consolidated)
    """
    transfers = [t for t in txns if is_transfer(t)]

    if not transfers:
        return {}

    pairs: dict[tuple[str, str], list[Transaction]] = {}

    for txn in transfers:
        if txn.amount.amount < 0:
            continue

        recipient = extract_recipient(txn.description)
        if not recipient:
            continue

        key = (txn.source_person, recipient)
        if key not in pairs:
            pairs[key] = []
        pairs[key].append(txn)

    result = {}
    for key, group in pairs.items():
        if len(group) > 0:
            dates = sorted([t.date.isoformat() for t in group])
            total = sum(t.amount.amount for t in group)
            from_person, to_person = key
            result[key] = Transfer(
                from_person=from_person,
                to_person=to_person,
                amount=Money(total, group[0].amount.currency),
                date_first=dates[0],
                date_last=dates[-1],
                txn_count=len(group),
            )

    return result


def net_position(transfers: dict[tuple[str, str], Transfer], person: str) -> Money:
    """Calculate net amount person has transferred (positive = owes out, negative = owed in)."""
    balance = Decimal(0)
    currency = None

    for t in transfers.values():
        if person == t.from_person:
            balance += t.amount.amount
        elif person == t.to_person:
            balance -= t.amount.amount

        if currency is None:
            currency = t.amount.currency

    return Money(balance, currency or "AUD")
