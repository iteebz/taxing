import contextlib
from decimal import Decimal
from pathlib import Path

from src.core.config import get_deduction_groups, get_rate_basis_map
from src.core.models import Deduction, Transaction


def deduce(
    txns: list[Transaction],
    fy: int,
    individual: str,
    business_percentages: dict[str, float],
    weights_path: Path | None = None,
) -> list[Deduction]:
    """Calculate deductions using weights and deduction groupings.

    Args:
        txns: List of categorized transactions.
        fy: Fiscal year.
        individual: Individual identifier.
        business_percentages: Map of deduction group to business use percentage (0.0-1.0).
        weights_path: Path to weights.csv for category weights. If None, assumes weight=1.0.

    Returns:
        List of Deduction records, grouped by deduction category.
    """
    deduction_groups = get_deduction_groups()
    rate_basis_map = get_rate_basis_map()

    weights = _load_weights(weights_path) if weights_path else {}

    deductions: dict[str, Deduction] = {}

    for group_name, raw_categories in deduction_groups.items():
        group_total = Decimal("0")

        for txn in txns:
            if not txn.cats:
                continue
            for cat in txn.cats:
                if cat in raw_categories:
                    weight = Decimal(str(weights.get(cat, 1.0)))
                    group_total += txn.amount * weight

        if group_total > 0:
            business_pct = Decimal(str(business_percentages.get(group_name, 0.0)))
            deductible_amount = group_total * business_pct

            if deductible_amount > 0:
                deductions[group_name] = Deduction(
                    individual=individual,
                    fy=fy,
                    category=group_name,
                    amount=deductible_amount,
                    rate=business_pct,
                    rate_basis=rate_basis_map.get(group_name, f"NEXUS_{group_name.upper()}"),
                )

    return list(deductions.values())


def _load_weights(weights_path: Path) -> dict[str, float]:
    """Load weights from CSV: category,weight."""
    if not weights_path.exists():
        return {}

    weights = {}
    try:
        with open(weights_path) as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            if not lines or lines[0] != "category,weight":
                return {}

            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) == 2:
                    with contextlib.suppress(ValueError):
                        weights[parts[0].strip()] = float(parts[1].strip())
    except Exception:
        pass

    return weights
