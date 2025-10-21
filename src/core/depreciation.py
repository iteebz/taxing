from decimal import Decimal

from src.core.models import AUD, Asset, Money


def calc_depreciation(asset: Asset, current_fy: int) -> Money:
    """Calculate annual prime cost depreciation for asset.

    Prime cost: equal depreciation each year = cost / life_years
    Only depreciates from purchase year onwards.
    """
    if current_fy < asset.fy:
        return Money(Decimal("0"), AUD)

    annual = asset.cost.amount / Decimal(asset.life_years)
    return Money(annual, AUD)


def calc_cumulative_depreciation(asset: Asset, from_fy: int, to_fy: int) -> Money:
    """Calculate total depreciation from from_fy to to_fy (inclusive)."""
    if to_fy < asset.fy or from_fy > to_fy:
        return Money(Decimal("0"), AUD)

    start = max(from_fy, asset.fy)
    years = to_fy - start + 1

    annual = asset.cost.amount / Decimal(asset.life_years)
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
