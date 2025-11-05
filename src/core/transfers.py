from dataclasses import dataclass
from decimal import Decimal

from src.core.models import Transaction


@dataclass(frozen=True)
class Transfer:
    """Represents a detected transfer between parties."""

    from_person: str
    to_person: str
    amount: Decimal
    date_first: str
    date_last: str
    txn_count: int


def is_transfer(txn: Transaction) -> bool:
    """Check if transaction is a transfer (marked via classify or heuristics).

    Transfer: marked with 'transfers' category via rules/transfers.txt
    """
    return txn.cats is not None and "transfers" in txn.cats


def extract_recipient(description: str) -> str | None:
    """Extract recipient name from transfer description.

    Patterns:
    - "transfer to alice smith" -> "alice smith"
    - "transfer from alice smith cash" -> "alice smith"
    - "direct credit 141000 alice smith" -> "alice smith"
    - "transfer to xx7568 commbank app" -> "xx7568"
    """
    desc_lower = description.lower()
    noise_words = {
        "other",
        "bank",
        "savings",
        "cash",
        "app",
        "netbank",
        "value",
        "date",
        "commbank",
        "transfer",
        "payid",
        "phone",
        "from",
        "to",
    }

    if "transfer to" in desc_lower:
        after = desc_lower.split("transfer to", 1)[-1].strip()
        return _extract_name(after.split(), noise_words)

    if "transfer from" in desc_lower:
        after = desc_lower.split("transfer from", 1)[-1].strip()
        return _extract_name(after.split(), noise_words)

    if "direct credit" in desc_lower:
        after = desc_lower.split("direct credit", 1)[-1].strip()
        parts = after.split()
        if len(parts) >= 1:
            return _extract_name(parts, noise_words)

    return None


def _extract_name(words: list[str], noise_words: set[str]) -> str | None:
    """Extract name from words, filtering out noise and numeric sequences.

    Stops at first noise word or numeric-only word after collecting name words.
    """
    name_words = []

    for word in words:
        cleaned = word.replace(":", "").replace(",", "")
        if not cleaned:
            continue
        if cleaned in noise_words or cleaned.isdigit():
            if name_words:
                break
            continue
        name_words.append(cleaned)

    return " ".join(name_words).strip() if name_words else None


def reconcile_transfers(
    txns: list[Transaction],
) -> dict[tuple[str, str], Transfer]:
    """Match and reconcile transfers between persons.

    Groups transfers by (from_person, to_person) pair.
    Processes both inbound and outbound transfers, extracting recipient from description.
    Returns: dict of (from_person, to_person) -> Transfer (consolidated)
    """
    transfers = [t for t in txns if is_transfer(t)]

    if not transfers:
        return {}

    canonical_names = _build_canonical_names(txns)
    pairs: dict[tuple[str, str], list[Transaction]] = {}

    for txn in transfers:
        recipient = extract_recipient(txn.description)
        if not recipient:
            continue

        recipient_canonical = _normalize_person_name(recipient, canonical_names)

        if txn.amount < 0:
            key = (txn.individual, recipient_canonical)
        else:
            key = (recipient_canonical, txn.individual)

        if key not in pairs:
            pairs[key] = []
        pairs[key].append(txn)

    result = {}
    for key, group in pairs.items():
        if len(group) > 0:
            dates = sorted([t.date.isoformat() for t in group])
            total = sum(abs(t.amount) for t in group)
            from_person, to_person = key
            result[key] = Transfer(
                from_person=from_person,
                to_person=to_person,
                amount=total,
                date_first=dates[0],
                date_last=dates[-1],
                txn_count=len(group),
            )

    return result


def _build_canonical_names(txns: list[Transaction]) -> dict[str, str]:
    """Build map of first names to canonical person names in txns."""
    canonical = {}
    for txn in txns:
        first_name = txn.individual.split()[0].lower()
        canonical[first_name] = txn.individual
    return canonical


def _normalize_person_name(name: str, canonical: dict[str, str]) -> str:
    """Normalize extracted name to canonical person name."""
    parts = name.lower().split()
    if not parts:
        return name
    first = parts[0]
    return canonical.get(first, name)


def net_position(transfers: dict[tuple[str, str], Transfer], individual: str) -> Decimal:
    """Calculate net amount individual has transferred (positive = owes out, negative = owed in)."""
    balance = Decimal(0)

    for t in transfers.values():
        if individual == t.from_person:
            balance += t.amount
        elif individual == t.to_person:
            balance -= t.amount

    return balance
