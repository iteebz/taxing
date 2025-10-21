from decimal import Decimal
from enum import Enum


class DeductionDivision(Enum):
    """Australian tax law divisions."""

    DIVISION_8 = "8"
    DIVISION_63 = "63"
    PROHIBITED = "PROHIBITED"
    ERROR = "ERROR"


DEDUCTIBLE_DIVISIONS = {
    "work_accessories": DeductionDivision.DIVISION_8,
    "software": DeductionDivision.DIVISION_8,
    "home_office": DeductionDivision.DIVISION_63,
    "vehicle": DeductionDivision.DIVISION_8,
    "clothing": DeductionDivision.PROHIBITED,
    "groceries": DeductionDivision.PROHIBITED,
    "salary": DeductionDivision.ERROR,
    "income": DeductionDivision.ERROR,
    "investment": DeductionDivision.DIVISION_8,
    "subscriptions": DeductionDivision.DIVISION_8,
    "internet": DeductionDivision.DIVISION_8,
    "mobile": DeductionDivision.DIVISION_8,
    "books": DeductionDivision.DIVISION_8,
    "electronics": DeductionDivision.DIVISION_8,
    "professional_fees": DeductionDivision.DIVISION_8,
    "training": DeductionDivision.DIVISION_8,
    "travel": DeductionDivision.DIVISION_8,
    "accom": DeductionDivision.DIVISION_8,
    "meals": DeductionDivision.DIVISION_8,
    "gifts": DeductionDivision.PROHIBITED,
    "donations": DeductionDivision.DIVISION_8,
    "medical": DeductionDivision.PROHIBITED,
    "pet": DeductionDivision.PROHIBITED,
    "self_care": DeductionDivision.PROHIBITED,
    "entertainment": DeductionDivision.PROHIBITED,
    "bars": DeductionDivision.PROHIBITED,
    "liquor": DeductionDivision.PROHIBITED,
    "nicotine": DeductionDivision.PROHIBITED,
    "refunds": DeductionDivision.PROHIBITED,
    "transfers": DeductionDivision.ERROR,
    "scam": DeductionDivision.ERROR,
    "uncategorized": DeductionDivision.PROHIBITED,
}

CATEGORY_NEXUS = {
    "work_accessories": (
        "Tools and equipment used in day-to-day work generating assessable income (ITAA97 s8-1)"
    ),
    "software": ("Software essential for income-producing work (ITAA97 s8-1, Division 8)"),
    "home_office": ("Work-from-home expenses: $0.45/hour under Division 63 simplified method"),
    "vehicle": ("Work-related vehicle expenses: $0.67/km under ITAA97 s8-1 simplified method"),
    "clothing": (
        "Personal clothing, never deductible under ITAA97 s8-1 (prevents double-counting)"
    ),
    "groceries": ("Personal consumption, no nexus to income production"),
    "subscriptions": ("Work-related subscriptions and memberships (ITAA97 s8-1)"),
    "internet": ("Internet/telecommunications used for work (ITAA97 s8-1, proportional deduction)"),
    "mobile": ("Mobile phone used for work (ITAA97 s8-1, proportional deduction)"),
    "books": ("Professional development and reference materials (ITAA97 s8-1)"),
    "electronics": ("Work-related IT equipment and consumables (ITAA97 s8-1)"),
    "professional_fees": ("Professional development and licensing fees (ITAA97 s8-1)"),
    "training": ("Work-related training and education (ITAA97 s8-1, subject to nexus)"),
    "travel": ("Work-related travel expenses (ITAA97 s8-1, subject to nexus)"),
    "accom": ("Accommodation for work-related travel (ITAA97 s8-1, subject to nexus)"),
    "meals": ("Meal expenses during work-related travel (ITAA97 s8-1, 50% deductible)"),
    "donations": ("Tax-deductible donations to endorsed organizations (ITAA97 Division 30)"),
    "gifts": ("Personal gifts, generally not deductible (no nexus to income production)"),
    "medical": (
        "Personal medical expenses, not deductible (covered by Medicare/private insurance)"
    ),
    "pet": ("Personal pet expenses, not deductible"),
    "self_care": ("Personal self-care and wellness, not deductible"),
    "entertainment": ("Personal entertainment, generally not deductible (ITAA97 s8-1)"),
    "bars": ("Personal bar/beverage purchases, not deductible"),
    "liquor": ("Personal alcohol purchases, not deductible"),
    "nicotine": ("Personal tobacco/nicotine, not deductible"),
}

ATO_ALIGNED_RATES_STANDARD = {
    "home_office": Decimal("0.45"),
    "vehicle": Decimal("0.67"),
    "subscriptions": Decimal("1.0"),
    "internet": Decimal("0.3"),
    "mobile": Decimal("0.5"),
    "software": Decimal("1.0"),
    "books": Decimal("1.0"),
    "electronics": Decimal("0.8"),
    "professional_fees": Decimal("1.0"),
    "training": Decimal("1.0"),
    "travel": Decimal("1.0"),
    "accom": Decimal("1.0"),
    "meals": Decimal("0.5"),
    "donations": Decimal("1.0"),
    "investment": Decimal("0.8"),
    "work_accessories": Decimal("0.85"),
}

ATO_ALIGNED_RATES_CONSERVATIVE = {
    "home_office": Decimal("0.30"),
    "vehicle": Decimal("0.55"),
    "subscriptions": Decimal("0.8"),
    "internet": Decimal("0.2"),
    "mobile": Decimal("0.35"),
    "software": Decimal("0.8"),
    "books": Decimal("0.8"),
    "electronics": Decimal("0.6"),
    "professional_fees": Decimal("0.8"),
    "training": Decimal("0.8"),
    "travel": Decimal("0.8"),
    "accom": Decimal("0.8"),
    "meals": Decimal("0.3"),
    "donations": Decimal("0.9"),
    "investment": Decimal("0.6"),
    "work_accessories": Decimal("0.7"),
}

RATE_BASIS_MAP = {
    "home_office": "ATO_DIVISION_63_SIMPLIFIED",
    "vehicle": "ATO_ITAA97_S8_1_SIMPLIFIED",
    "donations": "ATO_DIVISION_30",
    "meals": "ATO_50PCT_RULE",
}


def validate_category(category: str) -> None:
    """Validate that category is deductible and not in error state."""
    if category not in DEDUCTIBLE_DIVISIONS:
        raise ValueError(f"Unknown category: {category}")

    division = DEDUCTIBLE_DIVISIONS[category]
    if division == DeductionDivision.PROHIBITED:
        raise ValueError(f"Category '{category}' is never deductible under Australian tax law")
    if division == DeductionDivision.ERROR:
        raise ValueError(f"Category '{category}' is income, not a deduction")


def get_rate(
    category: str,
    conservative: bool = False,
) -> Decimal:
    """Get ATO-aligned deduction rate for category."""
    validate_category(category)

    rates = ATO_ALIGNED_RATES_CONSERVATIVE if conservative else ATO_ALIGNED_RATES_STANDARD
    return rates.get(category, Decimal("0"))


def get_rate_basis(category: str) -> str:
    """Get audit-friendly rate basis description."""
    validate_category(category)
    return RATE_BASIS_MAP.get(
        category,
        f"ITAA97_DIVISION_8_NEXUS_{category.upper()}",
    )
