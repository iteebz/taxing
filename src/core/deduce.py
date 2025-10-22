from decimal import Decimal

from src.core.config import load_config
from src.core.models import Deduction, Transaction
from src.core.rates import get_rate_basis, validate_category


def _accumulate_actual_cost(
    actual_cost_totals: dict[str, Decimal],
    sub_to_main_cat: dict[str, str],
    txn: Transaction,
) -> None:
    for cat in txn.category:
        if cat in sub_to_main_cat:
            main_cat = sub_to_main_cat[cat]
            actual_cost_totals[main_cat] += txn.amount


def _process_actual_cost(
    actual_cost_totals: dict[str, Decimal],
    business_percentages: dict[str, float],
    fy: int,
) -> dict[str, Deduction]:
    deductions = {}
    for main_cat, total_amount in actual_cost_totals.items():
        if total_amount > 0:
            business_pct = Decimal(str(business_percentages.get(main_cat, 0.0)))
            deductible_amount = total_amount * business_pct
            if deductible_amount > 0:
                deductions[main_cat] = Deduction(
                    category=main_cat,
                    amount=deductible_amount,
                    rate=business_pct,
                    rate_basis=get_rate_basis(main_cat),
                    fy=fy,
                )
    return deductions


def _process_fixed_rate(
    deductions: dict[str, Deduction],
    config,
    txn: Transaction,
    fy: int,
) -> None:
    for cat in txn.category:
        if cat not in config.fixed_rates:
            continue
        try:
            validate_category(cat)
        except ValueError:
            continue

        rate = config.fixed_rates[cat]
        business_pct = 1 - txn.personal_pct
        deductible_amount = txn.amount * rate * business_pct

        if deductible_amount > 0:
            if cat in deductions:
                existing = deductions[cat]
                deductions[cat] = Deduction(
                    category=cat,
                    amount=existing.amount + deductible_amount,
                    rate=rate,
                    rate_basis=get_rate_basis(cat),
                    fy=fy,
                )
            else:
                deductions[cat] = Deduction(
                    category=cat,
                    amount=deductible_amount,
                    rate=rate,
                    rate_basis=get_rate_basis(cat),
                    fy=fy,
                )


def deduce(
    txns: list[Transaction],
    fy: int,
    business_percentages: dict[str, float],
    min_confidence: float = 0.5,
) -> list[Deduction]:
    """
    Calculate deductions using the actual cost method based on config.

    Args:
        txns: List of categorized transactions.
        fy: Fiscal year to load config for.
        business_percentages: Map of deduction group (e.g., 'home_office') to business use percentage (0.0-1.0).
        min_confidence: Minimum classification confidence to process.

    Returns:
        List of Deduction records.
    """
    config = load_config(fy)
    deductions: dict[str, Deduction] = {}

    sub_to_main_cat = {
        sub_cat: main_cat
        for main_cat, sub_cats in config.actual_cost_categories.items()
        for sub_cat in sub_cats
    }

    actual_cost_totals: dict[str, Decimal] = {
        main_cat: Decimal("0") for main_cat in config.actual_cost_categories
    }

    for txn in txns:
        if txn.category is None or not txn.category or txn.confidence < min_confidence:
            continue
        _accumulate_actual_cost(actual_cost_totals, sub_to_main_cat, txn)

    deductions.update(_process_actual_cost(actual_cost_totals, business_percentages, fy))

    for txn in txns:
        if txn.category is None or not txn.category or txn.confidence < min_confidence:
            continue
        _process_fixed_rate(deductions, config, txn, fy)

    return list(deductions.values())
