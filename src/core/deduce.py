from src.core.models import AUD, Deduction, Transaction
from src.core.rates import get_rate, get_rate_basis, validate_category


def deduce(
    txns: list[Transaction],
    weights: dict[str, float],
    fy: int,
    conservative: bool = False,
) -> list[Deduction]:
    """
    Calculate deductions by applying ATO-aligned rates to categorized transactions.

    Args:
        txns: List of categorized transactions
        weights: Dict mapping category -> deduction percentage (0.0-1.0), legacy support
        fy: Fiscal year for audit trail
        conservative: Use conservative (lower) rates if True

    Returns:
        List of Deduction records with audit trail (category, amount, rate, rate_basis)
    """
    deductions_by_category: dict[str, Deduction] = {}

    for txn in txns:
        if txn.category is None or not txn.category:
            continue

        if txn.amount.currency != AUD:
            continue

        for cat in txn.category:
            try:
                validate_category(cat)
            except ValueError:
                continue

            rate = get_rate(cat, conservative)
            if rate == 0:
                continue

            business_pct = 1 - txn.personal_pct
            deductible_amount = txn.amount * float(rate) * float(business_pct)

            rate_basis = get_rate_basis(cat)

            deduction = Deduction(
                category=cat,
                amount=deductible_amount,
                rate=rate,
                rate_basis=rate_basis,
                fy=fy,
            )

            if cat in deductions_by_category:
                existing = deductions_by_category[cat]
                deductions_by_category[cat] = Deduction(
                    category=cat,
                    amount=existing.amount + deductible_amount,
                    rate=rate,
                    rate_basis=rate_basis,
                    fy=fy,
                )
            else:
                deductions_by_category[cat] = deduction

    return list(deductions_by_category.values())
