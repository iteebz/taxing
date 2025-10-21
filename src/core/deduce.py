from decimal import Decimal

from src.core.models import AUD, Car, Deduction, Money, Transaction
from src.core.rates import get_rate, get_rate_basis, validate_category


def deduce(
    txns: list[Transaction],
    fy: int,
    conservative: bool = False,
    min_confidence: float = 0.5,
    weights: dict[str, float] | None = None,
) -> list[Deduction]:
    """
    Calculate deductions by applying ATO-aligned rates to categorized transactions.

    Args:
        txns: List of categorized transactions (must have classification confidence ≥ min_confidence)
        fy: Fiscal year for audit trail
        conservative: Use conservative (lower) rates if True
        min_confidence: Minimum classification confidence to process (0.0-1.0, default 0.5)
        weights: Override rates by category (e.g., {"electronics": 1.0}). Takes precedence over conservative flag.

    Returns:
        List of Deduction records with audit trail (category, amount, rate, rate_basis)
    """
    if weights is None:
        weights = {}
    deductions_by_category: dict[str, Deduction] = {}

    for txn in txns:
        if txn.category is None or not txn.category:
            continue

        if txn.amount.currency != AUD:
            continue

        if txn.confidence < min_confidence:
            continue

        for cat in txn.category:
            try:
                validate_category(cat)
            except ValueError:
                continue

            if cat in weights:
                rate = Decimal(str(weights[cat]))
            else:
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


def deduce_car(
    txns: list[Transaction],
    deductible_pct: Decimal,
    fy: int,
    min_confidence: float = 0.5,
) -> tuple[Car, Deduction]:
    """
    Calculate car deduction via implied km method.

    Args:
        txns: List of vehicle category transactions
        deductible_pct: Claimed deductible % of total spend (0.0-1.0)
        fy: Fiscal year
        min_confidence: Minimum classification confidence to process

    Returns:
        Tuple of (Car model with implied_km, corresponding Deduction record)
    """
    vehicle_total = Money(Decimal("0"), AUD)

    for txn in txns:
        if txn.category is None or "vehicle" not in txn.category:
            continue
        if txn.amount.currency != AUD:
            continue
        if txn.confidence < min_confidence:
            continue

        business_pct = 1 - txn.personal_pct
        vehicle_total = vehicle_total + (txn.amount * float(business_pct))

    car = Car(total_spend=vehicle_total, deductible_pct=deductible_pct)

    deduction = Deduction(
        category="vehicle",
        amount=car.deductible_amount,
        rate=Decimal("0.67"),
        rate_basis="ATO_ITAA97_S8_1_SIMPLIFIED_IMPLIED_KM",
        fy=fy,
    )

    return car, deduction
