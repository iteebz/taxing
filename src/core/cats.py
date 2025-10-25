"""Category taxonomy and deduction mapping."""

from dataclasses import dataclass
from typing import Literal

TaxTreatment = Literal["actual_cost", "fixed_rate", "non_expense"]
DeductionType = Literal[
    "home_office", "vehicle", "meals", "health", "donations", "income", "transfers"
]


@dataclass(frozen=True)
class CategoryMeta:
    """Metadata for a category."""

    tier2: str
    deductible: bool
    tier1: DeductionType | None = None
    treatment: TaxTreatment = "actual_cost"
    fixed_rate: float | None = None


# Tier 2 → Tier 1 mapping (merchant categories → deduction groups)
TIER1_TO_TIER2 = {
    "home_office": [
        "home/utilities",
        "home/furnishing",
        "home/rent",
    ],
    "vehicle": [
        "vehicle/fuel",
        "vehicle/maintenance",
        "vehicle/insurance",
    ],
    "meals": ["meals"],
    "health": ["health/medical"],
    "donations": ["donations"],
    "income": ["income"],
    "transfers": ["transfers"],
}

# Tier 2 categories → metadata
CATEGORY_META = {
    # home
    "electricity": CategoryMeta(
        tier2="home/utilities",
        deductible=True,
        tier1="home_office",
        treatment="actual_cost",
    ),
    "gas": CategoryMeta(
        tier2="home/utilities",
        deductible=True,
        tier1="home_office",
        treatment="actual_cost",
    ),
    "internet": CategoryMeta(
        tier2="home/utilities",
        deductible=True,
        tier1="home_office",
        treatment="actual_cost",
    ),
    "utilities": CategoryMeta(
        tier2="home/utilities",
        deductible=True,
        tier1="home_office",
        treatment="actual_cost",
    ),
    "home_stores": CategoryMeta(
        tier2="home/furnishing",
        deductible=True,
        tier1="home_office",
        treatment="actual_cost",
    ),
    "pet": CategoryMeta(
        tier2="home/furnishing",
        deductible=False,
        treatment="actual_cost",
    ),
    "home_office": CategoryMeta(
        tier2="home/furnishing",
        deductible=True,
        tier1="home_office",
        treatment="actual_cost",
    ),
    "rent": CategoryMeta(
        tier2="home/rent",
        deductible=True,
        tier1="home_office",
        treatment="actual_cost",
    ),
    # vehicle
    "fuel": CategoryMeta(
        tier2="vehicle/fuel",
        deductible=True,
        tier1="vehicle",
        treatment="actual_cost",
    ),
    "car": CategoryMeta(
        tier2="vehicle/maintenance",
        deductible=True,
        tier1="vehicle",
        treatment="actual_cost",
    ),
    "taxi": CategoryMeta(
        tier2="vehicle/maintenance",
        deductible=True,
        tier1="vehicle",
        treatment="actual_cost",
    ),
    "transport": CategoryMeta(
        tier2="vehicle/maintenance",
        deductible=True,
        tier1="vehicle",
        treatment="actual_cost",
    ),
    "registration": CategoryMeta(
        tier2="vehicle/maintenance",
        deductible=True,
        tier1="vehicle",
        treatment="actual_cost",
    ),
    "maintenance": CategoryMeta(
        tier2="vehicle/maintenance",
        deductible=True,
        tier1="vehicle",
        treatment="actual_cost",
    ),
    "insurance": CategoryMeta(
        tier2="vehicle/insurance",
        deductible=True,
        tier1="vehicle",
        treatment="actual_cost",
    ),
    "parking": CategoryMeta(
        tier2="vehicle/maintenance",
        deductible=True,
        tier1="vehicle",
        treatment="actual_cost",
    ),
    # health
    "medical": CategoryMeta(
        tier2="health/medical",
        deductible=True,
        tier1="health",
        treatment="actual_cost",
    ),
    "therapy": CategoryMeta(
        tier2="health/medical",
        deductible=True,
        tier1="health",
        treatment="actual_cost",
    ),
    "pharmacy": CategoryMeta(
        tier2="health/medical",
        deductible=True,
        tier1="health",
        treatment="actual_cost",
    ),
    # meals
    "dining": CategoryMeta(
        tier2="meals",
        deductible=True,
        tier1="meals",
        treatment="fixed_rate",
        fixed_rate=0.5,
    ),
    "bars": CategoryMeta(
        tier2="meals",
        deductible=True,
        tier1="meals",
        treatment="fixed_rate",
        fixed_rate=0.5,
    ),
    "food_delivery": CategoryMeta(
        tier2="meals",
        deductible=True,
        tier1="meals",
        treatment="fixed_rate",
        fixed_rate=0.5,
    ),
    # groceries
    "groceries": CategoryMeta(
        tier2="groceries",
        deductible=False,
        treatment="actual_cost",
    ),
    "supermarket": CategoryMeta(
        tier2="groceries",
        deductible=False,
        treatment="actual_cost",
    ),
    "convenience": CategoryMeta(
        tier2="groceries",
        deductible=False,
        treatment="actual_cost",
    ),
    # personal
    "clothing": CategoryMeta(
        tier2="personal/clothing",
        deductible=False,
        treatment="actual_cost",
    ),
    "accessories": CategoryMeta(
        tier2="personal/clothing",
        deductible=False,
        treatment="actual_cost",
    ),
    "cosmetics": CategoryMeta(
        tier2="personal/wellness",
        deductible=False,
        treatment="actual_cost",
    ),
    "nicotine": CategoryMeta(
        tier2="personal/wellness",
        deductible=False,
        treatment="actual_cost",
    ),
    "self_care": CategoryMeta(
        tier2="personal/wellness",
        deductible=False,
        treatment="actual_cost",
    ),
    "gifts": CategoryMeta(
        tier2="personal/gifts",
        deductible=False,
        treatment="actual_cost",
    ),
    # entertainment
    "entertainment": CategoryMeta(
        tier2="entertainment",
        deductible=False,
        treatment="actual_cost",
    ),
    "events": CategoryMeta(
        tier2="entertainment",
        deductible=False,
        treatment="actual_cost",
    ),
    "hobbies": CategoryMeta(
        tier2="entertainment",
        deductible=False,
        treatment="actual_cost",
    ),
    "sports": CategoryMeta(
        tier2="entertainment",
        deductible=False,
        treatment="actual_cost",
    ),
    # subscriptions
    "software": CategoryMeta(
        tier2="subscriptions",
        deductible=True,
        tier1="home_office",
        treatment="actual_cost",
    ),
    "subscriptions": CategoryMeta(
        tier2="subscriptions",
        deductible=False,
        treatment="actual_cost",
    ),
    "books": CategoryMeta(
        tier2="subscriptions",
        deductible=False,
        treatment="actual_cost",
    ),
    # work
    "business": CategoryMeta(
        tier2="work/business",
        deductible=False,
        treatment="actual_cost",
    ),
    "work_accessories": CategoryMeta(
        tier2="work/business",
        deductible=True,
        tier1="home_office",
        treatment="actual_cost",
    ),
    "self_education": CategoryMeta(
        tier2="work/education",
        deductible=False,
        treatment="actual_cost",
    ),
    # income (non-expense)
    "income": CategoryMeta(
        tier2="income",
        deductible=False,
        tier1="income",
        treatment="non_expense",
    ),
    # transfers (non-expense)
    "transfers": CategoryMeta(
        tier2="transfers",
        deductible=False,
        tier1="transfers",
        treatment="non_expense",
    ),
    "trust": CategoryMeta(
        tier2="transfers",
        deductible=False,
        tier1="transfers",
        treatment="non_expense",
    ),
    "bnpl": CategoryMeta(
        tier2="transfers",
        deductible=False,
        tier1="transfers",
        treatment="non_expense",
    ),
    "debts": CategoryMeta(
        tier2="transfers",
        deductible=False,
        tier1="transfers",
        treatment="non_expense",
    ),
    "refunds": CategoryMeta(
        tier2="transfers",
        deductible=False,
        tier1="transfers",
        treatment="non_expense",
    ),
    "scam": CategoryMeta(
        tier2="transfers",
        deductible=False,
        tier1="transfers",
        treatment="non_expense",
    ),
    "fees": CategoryMeta(
        tier2="transfers",
        deductible=False,
        tier1="transfers",
        treatment="non_expense",
    ),
    "taxation": CategoryMeta(
        tier2="transfers",
        deductible=False,
        tier1="transfers",
        treatment="non_expense",
    ),
    "investment": CategoryMeta(
        tier2="transfers",
        deductible=False,
        tier1="transfers",
        treatment="non_expense",
    ),
    "beems": CategoryMeta(
        tier2="transfers",
        deductible=False,
        tier1="transfers",
        treatment="non_expense",
    ),
    "craft": CategoryMeta(
        tier2="transfers",
        deductible=False,
        tier1="transfers",
        treatment="non_expense",
    ),
    # donations
    "donations": CategoryMeta(
        tier2="donations",
        deductible=True,
        tier1="donations",
        treatment="fixed_rate",
        fixed_rate=1.0,
    ),
    # mobile
    "mobile": CategoryMeta(
        tier2="subscriptions",
        deductible=False,
        treatment="actual_cost",
    ),
    "mobile_accessories": CategoryMeta(
        tier2="personal/clothing",
        deductible=False,
        treatment="actual_cost",
    ),
    # property (track for analytics, non-deductible personal)
    "property": CategoryMeta(
        tier2="transfers",
        deductible=False,
        tier1="transfers",
        treatment="non_expense",
    ),
    # additional categories
    "electronics": CategoryMeta(
        tier2="personal/clothing",
        deductible=False,
        treatment="actual_cost",
    ),
    "liquor": CategoryMeta(
        tier2="meals",
        deductible=True,
        tier1="meals",
        treatment="fixed_rate",
        fixed_rate=0.5,
    ),
    "online_retail": CategoryMeta(
        tier2="personal/clothing",
        deductible=False,
        treatment="actual_cost",
    ),
    "accom": CategoryMeta(
        tier2="entertainment",
        deductible=False,
        treatment="actual_cost",
    ),
    "travel": CategoryMeta(
        tier2="entertainment",
        deductible=False,
        treatment="actual_cost",
    ),
}


def get_category_meta(cat: str) -> CategoryMeta | None:
    """Get metadata for a category, return None if not found."""
    return CATEGORY_META.get(cat)


def get_tier2(cat: str) -> str | None:
    """Get Tier 2 category for a category."""
    meta = get_category_meta(cat)
    return meta.tier2 if meta else None


def is_deductible(cat: str) -> bool:
    """Check if category is deductible."""
    meta = get_category_meta(cat)
    return meta.deductible if meta else False


def get_tier1(cat: str) -> DeductionType | None:
    """Get Tier 1 deduction group for a category."""
    meta = get_category_meta(cat)
    return meta.tier1 if meta else None
