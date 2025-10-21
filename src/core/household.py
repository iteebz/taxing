from dataclasses import dataclass
from decimal import Decimal

from src.core.models import AUD, Individual, Money

TAX_FREE_THRESHOLD = {
    25: Decimal("18200"),
}


def allocate_deductions(
    your_income: Money,
    janice_income: Money,
    shared_deductions: list[Money],
    fy: int,
) -> tuple[Money, Money]:
    """Allocate shared deductions to minimize household taxable income.

    Strategy:
    1. Fill tax-free thresholds first (no tax benefit, but preserves bracket space)
    2. Route excess to lower-bracket person (maximize tax saving)
    """
    if not shared_deductions:
        return Money(Decimal("0"), AUD), Money(Decimal("0"), AUD)

    threshold = TAX_FREE_THRESHOLD.get(fy, Decimal("18200"))
    total_ded = sum(shared_deductions, Money(Decimal("0"), AUD))

    your_buffer = max(Decimal("0"), threshold - your_income.amount)
    janice_buffer = max(Decimal("0"), threshold - janice_income.amount)

    your_alloc = Money(Decimal("0"), AUD)
    janice_alloc = Money(Decimal("0"), AUD)
    remaining = total_ded.amount

    if your_buffer > 0:
        take_your = min(your_buffer, remaining)
        your_alloc = Money(take_your, AUD)
        remaining -= take_your

    if remaining > 0 and janice_buffer > 0:
        take_janice = min(janice_buffer, remaining)
        janice_alloc = Money(janice_alloc.amount + take_janice, AUD)
        remaining -= take_janice

    if remaining > 0:
        your_rate = _tax_rate(your_income.amount, fy)
        janice_rate = _tax_rate(janice_income.amount, fy)

        if janice_rate < your_rate:
            janice_alloc = Money(janice_alloc.amount + remaining, AUD)
        else:
            your_alloc = Money(your_alloc.amount + remaining, AUD)

    return your_alloc, janice_alloc


@dataclass(frozen=True)
class HouseholdAllocation:
    yours: Individual
    janice: Individual
    your_tax: Money
    janice_tax: Money

    @property
    def household_tax(self) -> Money:
        return self.your_tax + self.janice_tax


BRACKETS = {
    25: [
        (0, Decimal("0")),
        (18200, Decimal("0.19")),
        (45000, Decimal("0.325")),
        (120000, Decimal("0.37")),
        (180000, Decimal("0.45")),
    ]
}


def _tax_rate(income: Decimal, fy: int) -> Decimal:
    """Get marginal tax rate for income (rate at which last dollar is taxed)."""
    brackets = BRACKETS.get(fy, BRACKETS[25])
    rate = Decimal("0")
    for threshold, r in brackets:
        if income >= threshold:
            rate = r
    return rate


def _tax_liability(income: Money, fy: int) -> Money:
    amt = income.amount
    if amt <= 18200:
        return Money(Decimal("0"), AUD)

    brackets = BRACKETS.get(fy, BRACKETS[25])
    tax = Decimal("0")
    prev_threshold = 0

    for threshold, rate in brackets:
        if amt <= prev_threshold:
            break
        taxable_in_bracket = min(amt, Decimal(threshold)) - Decimal(prev_threshold)
        if taxable_in_bracket > 0:
            tax += taxable_in_bracket * rate
        prev_threshold = threshold

    return Money(tax, AUD)


def optimize_household(
    yours: Individual,
    janice: Individual,
) -> HouseholdAllocation:
    """Allocate deductions & gains to minimize household tax.

    Strategy:
    - Route deductions to lower-bracket person (Janice if employed FY25)
    - Route gains to person with loss carryforwards (you)
    - Minimize: your_tax + janice_tax
    """
    your_rate = _tax_rate(yours.income.amount, yours.fy)
    janice_rate = _tax_rate(janice.income.amount, janice.fy)

    your_alloc = yours
    janice_alloc = janice

    if janice_rate < your_rate:
        total_ded = sum(yours.deductions + janice.deductions, Money(Decimal("0"), AUD))
        your_alloc = Individual(
            name=yours.name,
            fy=yours.fy,
            income=yours.income,
            deductions=[],
            gains=yours.gains,
            losses=yours.losses,
        )
        janice_alloc = Individual(
            name=janice.name,
            fy=janice.fy,
            income=janice.income,
            deductions=[total_ded],
            gains=janice.gains,
            losses=janice.losses,
        )

    your_tax = _tax_liability(your_alloc.taxable_income, your_alloc.fy)
    janice_tax = _tax_liability(janice_alloc.taxable_income, janice_alloc.fy)

    return HouseholdAllocation(
        yours=your_alloc,
        janice=janice_alloc,
        your_tax=your_tax,
        janice_tax=janice_tax,
    )
