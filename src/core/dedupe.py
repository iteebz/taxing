import hashlib
import re
from dataclasses import replace

from src.core.models import Transaction
from src.core.transfers import extract_recipient


def _normalize_desc(desc: str) -> str:
    """Extract keywords from description for fingerprinting.

    Removes branch numbers, amounts, timestamps. Keeps merchant name + category.
    """
    normalized = re.sub(r"#\d+|#[A-Z0-9]+|\$[\d.]+|\d{1,2}:\d{2}|\s+", " ", desc.upper())
    return normalized.strip()


def _is_transfer_desc(desc: str) -> bool:
    """Check if description is transfer-like (before classification)."""
    desc_lower = desc.lower()
    return any(x in desc_lower for x in ["transfer", "direct credit", "swift"])


def fingerprint(txn: Transaction) -> str:
    """Generate fingerprint for transaction deduplication.

    Fingerprints same transfer event across ledgers:
    - Merchant: date + normalized_desc + amount + person
    - Same-person transfer: date + amount + person (CBA->ANZ both sides)
    - P2P transfer: date + amount + from_person + to_person (beemit both sides)
    """
    norm_desc = _normalize_desc(txn.description)

    if _is_transfer_desc(txn.description):
        recipient = extract_recipient(txn.description)
        if recipient:
            key = tuple(sorted([txn.individual, recipient]))
            raw = f"{txn.date}|{txn.amount}|{key[0]}|{key[1]}"
        else:
            raw = f"{txn.date}|{txn.amount}|{txn.individual}"
    else:
        raw = f"{txn.date}|{norm_desc}|{txn.amount}|{txn.individual}"

    return hashlib.sha256(raw.encode()).hexdigest()


def dedupe(txns: list[Transaction]) -> list[Transaction]:
    """Deduplicate transactions across ledgers.

    Groups by fingerprint and merges:
    - Consolidates sources set
    - Tracks source_txn_ids for audit
    - Uses first txn in group as base (preserves category, description)
    """
    if not txns:
        return []

    groups: dict[str, list[Transaction]] = {}
    for txn in txns:
        fp = fingerprint(txn)
        if fp not in groups:
            groups[fp] = []
        groups[fp].append(txn)

    result = []
    for group in groups.values():
        if len(group) == 1:
            result.append(group[0])
        else:
            base = group[0]
            sources = set()
            source_txn_ids = []
            cats = set()

            for txn in group:
                sources.update(txn.sources)
                source_txn_ids.extend(txn.source_txn_ids)
                if txn.category:
                    cats.update(txn.category)

            merged = replace(
                base,
                sources=frozenset(sources),
                source_txn_ids=tuple(source_txn_ids),
                category=cats if cats else None,
            )
            result.append(merged)

    return result
