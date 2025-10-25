from decimal import Decimal

from src.core.models import Transaction


def coverage(txns: list[Transaction]) -> dict[str, float]:
    """Calculate transaction coverage metrics.

    Returns:
        {
            "pct_txns": float,      # % of txns categorized
            "count_labeled": int,
            "count_total": int,
            "pct_debit": float,     # % of outbound $ categorized
            "pct_credit": float,    # % of inbound $ categorized
            "debit_labeled": Decimal,
            "debit_total": Decimal,
            "credit_labeled": Decimal,
            "credit_total": Decimal,
        }
    """
    if not txns:
        return {
            "pct_txns": 0.0,
            "count_labeled": 0,
            "count_total": 0,
            "pct_debit": 0.0,
            "pct_credit": 0.0,
            "debit_labeled": Decimal("0"),
            "debit_total": Decimal("0"),
            "credit_labeled": Decimal("0"),
            "credit_total": Decimal("0"),
        }

    txns = [t for t in txns if t.amount is not None and not t.amount.is_nan()]

    labeled = [t for t in txns if t.cats is not None and t.cats]
    count_labeled = len(labeled)
    count_total = len(txns)
    pct_txns = 100 * count_labeled / count_total if count_total > 0 else 0.0

    debits = [t for t in txns if t.amount < 0]
    credits = [t for t in txns if t.amount > 0]

    debit_labeled = sum(
        (abs(t.amount) for t in labeled if t.amount < 0),
        Decimal("0"),
    )
    debit_total = sum((abs(t.amount) for t in debits), Decimal("0"))
    pct_debit = 100 * debit_labeled / debit_total if debit_total > 0 else 0.0

    credit_labeled = sum(
        (t.amount for t in labeled if t.amount > 0),
        Decimal("0"),
    )
    credit_total = sum((t.amount for t in credits), Decimal("0"))
    pct_credit = 100 * credit_labeled / credit_total if credit_total > 0 else 0.0

    return {
        "pct_txns": round(pct_txns, 2),
        "count_labeled": count_labeled,
        "count_total": count_total,
        "pct_debit": round(pct_debit, 2),
        "pct_credit": round(pct_credit, 2),
        "debit_labeled": round(debit_labeled, 2),
        "debit_total": round(debit_total, 2),
        "credit_labeled": round(credit_labeled, 2),
        "credit_total": round(credit_total, 2),
    }


def household_metrics(txns: list[Transaction]) -> dict[str, any]:
    """Calculate household-level metrics.

    Returns:
        {
            "spending_by_person": {person: $},
            "income_by_person": {person: $},
            "transfers_by_person": {person: $},
            "total_spending": $,
            "total_income": $,
            "total_transfers": $,
            "persons": list[str],
        }
    """
    spending_by_person = {}
    income_by_person = {}
    transfers_by_person = {}

    valid_txns = [t for t in txns if t.amount is not None and not t.amount.is_nan()]

    for txn in valid_txns:
        individual = txn.individual
        is_transfer = txn.is_transfer or (txn.cats is not None and "transfers" in txn.cats)

        if is_transfer:
            if individual not in transfers_by_person:
                transfers_by_person[individual] = Decimal("0")
            transfers_by_person[individual] += abs(txn.amount)
        elif txn.amount > 0:
            if individual not in income_by_person:
                income_by_person[individual] = Decimal("0")
            income_by_person[individual] += txn.amount
        else:
            if individual not in spending_by_person:
                spending_by_person[individual] = Decimal("0")
            spending_by_person[individual] += abs(txn.amount)

    total_spending = sum(spending_by_person.values(), Decimal("0"))
    total_income = sum(income_by_person.values(), Decimal("0"))
    total_transfers = sum(transfers_by_person.values(), Decimal("0"))

    persons = sorted(set(spending_by_person.keys()) | set(income_by_person.keys()))

    return {
        "spending_by_person": {p: float(spending_by_person.get(p, Decimal("0"))) for p in persons},
        "income_by_person": {p: float(income_by_person.get(p, Decimal("0"))) for p in persons},
        "transfers_by_person": {
            p: float(transfers_by_person.get(p, Decimal("0"))) for p in persons
        },
        "total_spending": float(total_spending),
        "total_income": float(total_income),
        "total_transfers": float(total_transfers),
        "persons": persons,
    }
