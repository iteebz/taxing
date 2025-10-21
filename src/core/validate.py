from datetime import date

from src.core.models import Transaction


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_fy_boundary(txns: list[Transaction], fy: int) -> None:
    """Validate all transactions fall within fiscal year boundary.

    FY boundary: July 1 (previous year) to June 30 (current year).
    E.g., FY25 = 2024-07-01 to 2025-06-30

    Args:
        txns: Transaction list
        fy: Fiscal year (short form: 25 for FY2025)
    """
    if not txns:
        return

    fy_full = 2000 + fy if fy < 100 else fy
    fy_start = date(fy_full - 1, 7, 1)
    fy_end = date(fy_full, 6, 30)

    for txn in txns:
        if not (fy_start <= txn.date <= fy_end):
            raise ValidationError(
                f"Transaction on {txn.date} outside FY{fy} boundary "
                f"({fy_start} to {fy_end}): {txn.description}"
            )


def validate_no_duplicates(txns: list[Transaction]) -> None:
    """Validate no exact duplicate transactions exist.

    Duplicates: same date + amount + description.
    """
    seen = set()
    for txn in txns:
        key = (txn.date, txn.amount, txn.description)
        if key in seen:
            raise ValidationError(
                f"Duplicate transaction found: {txn.date} {txn.amount} {txn.description}"
            )
        seen.add(key)


def validate_unlabeled(txns: list[Transaction]) -> None:
    """Validate all transactions are categorized.

    Raises if any transaction has None category.
    """
    unlabeled = [t for t in txns if t.category is None]
    if unlabeled:
        raise ValidationError(
            f"{len(unlabeled)} unlabeled transactions found: "
            f"{[t.description for t in unlabeled[:3]]}..."
        )


def validate_transactions(txns: list[Transaction], fy: int) -> None:
    """Run full transaction validation suite.

    Args:
        txns: Transaction list
        fy: Fiscal year (e.g., 25 for FY2025)

    Raises:
        ValidationError if any check fails
    """
    validate_fy_boundary(txns, fy)
    validate_no_duplicates(txns)
    validate_unlabeled(txns)
