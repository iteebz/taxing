from src.core.models import Money, Transaction


def deduce(
    txns: list[Transaction],
    weights: dict[str, float],
) -> dict[str, Money]:
    """
    Calculate deductions by applying weights to categorized transactions.

    Args:
        txns: List of categorized transactions
        weights: Dict mapping category -> deduction percentage (0.0-1.0)

    Returns:
        Dict mapping category -> total deduction amount (AUD only)
    """
    from src.core.models import AUD
    
    deductions: dict[str, Money] = {}

    for txn in txns:
        if txn.category is None or not txn.category:
            continue
        
        if txn.amount.currency != AUD:
            continue

        for cat in txn.category:
            weight = weights.get(cat, 0.0)
            deduction = txn.amount * weight

            if cat in deductions:
                deductions[cat] = deductions[cat] + deduction
            else:
                deductions[cat] = deduction

    return deductions
