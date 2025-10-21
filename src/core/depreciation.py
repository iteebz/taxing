from datetime import date
from decimal import Decimal

from src.core.models import AUD, Asset, Money


def calc_days_held(asset: Asset, fy: int) -> int:
    """Calculate days held in a fiscal year (July-June in Australia).

    If purchase_date not set, assumes full year (365 days).
    FY25 = 1 Jul 2024 - 30 Jun 2025, so start_year = 2024, end_year = 2025
    Formula: start_year = 2000 + fy - 1, end_year = 2000 + fy

    If purchase_date is on or before FY start, assume held full year.
    """
    if asset.purchase_date is None:
        return 365

    start_year = 2000 + fy - 1
    fy_start = date(start_year, 7, 1)
    fy_end = date(start_year + 1, 6, 30)

    purchase = asset.purchase_date

    if purchase > fy_end:
        return 0

    if purchase <= fy_start:
        return 365

    return (fy_end - purchase).days + 1


def _calc_pc(cost: Decimal, life_years: int) -> Decimal:
    """Prime Cost: straight-line depreciation."""
    return cost / Decimal(life_years)


def _calc_dv(
    cost: Decimal, life_years: int, year_num: int, opening_value: Decimal | None = None
) -> Decimal:
    """Diminishing Value: applies fixed % to remaining value each year."""
    if opening_value is None:
        opening_value = cost
    rate = (Decimal("2") / Decimal(life_years)) if life_years > 0 else Decimal("0")
    return opening_value * rate


def calc_depreciation(asset: Asset, current_fy: int) -> Money:
    """Calculate annual depreciation for asset (ATO-compliant).

    Formula (ATO):
    - PC: cost × (days_held / 365) × (100 / effective_life)
    - DV: cost × (days_held / 365) × (200 / effective_life)

    For DV subsequent years, use base_value instead of cost.
    Only depreciates from purchase year onwards.
    """
    if current_fy < asset.fy:
        return Money(Decimal("0"), AUD)

    days = calc_days_held(asset, current_fy)
    if days == 0:
        return Money(Decimal("0"), AUD)

    days_ratio = Decimal(days) / Decimal("365")

    if asset.depreciation_method == "DV":
        years_since = current_fy - asset.fy
        if years_since == 0:
            base_value = asset.cost.amount
        else:
            cum = _calc_cumulative_dv(asset.cost.amount, asset.life_years, years_since)
            base_value = asset.cost.amount - cum

        rate = Decimal("200") / Decimal(asset.life_years) / Decimal("100")
        annual = base_value * days_ratio * rate
    else:
        rate = Decimal("100") / Decimal(asset.life_years) / Decimal("100")
        annual = asset.cost.amount * days_ratio * rate

    return Money(annual, AUD)


def _calc_cumulative_dv(cost: Decimal, life_years: int, years: int) -> Decimal:
    """Calculate cumulative DV depreciation over N years."""
    rate = (Decimal("2") / Decimal(life_years)) if life_years > 0 else Decimal("0")
    total = Decimal("0")
    bv = cost
    for _ in range(years):
        dep = bv * rate
        total += dep
        bv -= dep
    return total


def calc_cumulative_depreciation(asset: Asset, from_fy: int, to_fy: int) -> Money:
    """Calculate total depreciation from from_fy to to_fy (inclusive)."""
    if to_fy < asset.fy or from_fy > to_fy:
        return Money(Decimal("0"), AUD)

    start = max(from_fy, asset.fy)
    years = to_fy - start + 1

    if asset.depreciation_method == "DV":
        total = _calc_cumulative_dv(asset.cost.amount, asset.life_years, years)
    else:
        annual = _calc_pc(asset.cost.amount, asset.life_years)
        total = annual * Decimal(years)

    return Money(total, AUD)


def calc_book_value(asset: Asset, current_fy: int) -> Money:
    """Calculate remaining book value after depreciation."""
    depreciated = calc_cumulative_depreciation(asset, asset.fy, current_fy)
    return asset.cost - depreciated


def depreciation_schedule(asset: Asset, to_fy: int) -> dict[int, Money]:
    """Generate year-by-year depreciation schedule."""
    schedule = {}
    for fy in range(asset.fy, to_fy + 1):
        schedule[fy] = calc_depreciation(asset, fy)
    return schedule
