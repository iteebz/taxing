from dataclasses import dataclass
from decimal import Decimal

from src.core.models import AUD, Individual, Money

TAX_FREE_THRESHOLD = {
    23: Decimal("18200"),
    24: Decimal("18200"),
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

    your_buf = max(Decimal("0"), threshold - your_income.amount)
    janice_buf = max(Decimal("0"), threshold - janice_income.amount)

    your_alloc = Money(Decimal("0"), AUD)
    janice_alloc = Money(Decimal("0"), AUD)
    remain = total_ded.amount

    if your_buf > 0:
        your_alloc = Money(min(your_buf, remain), AUD)
        remain -= your_alloc.amount

    if remain > 0 and janice_buf > 0:
        janice_alloc = Money(min(janice_buf, remain), AUD)
        remain -= janice_alloc.amount

    if remain > 0:
        your_rate = _tax_rate(your_income.amount, fy)
        janice_rate = _tax_rate(janice_income.amount, fy)

        if janice_rate < your_rate:
            janice_alloc = Money(janice_alloc.amount + remain, AUD)
        else:
            your_alloc = Money(your_alloc.amount + remain, AUD)

    return your_alloc, janice_alloc


@dataclass(frozen=True)
class Allocation:
    yours: Individual
    janice: Individual
    your_tax: Money
    janice_tax: Money

    @property
    def total(self) -> Money:
        return self.your_tax + self.janice_tax


BRACKETS = {
    23: [
        (0, Decimal("0")),
        (18200, Decimal("0.19")),
        (45000, Decimal("0.325")),
        (120000, Decimal("0.37")),
        (180000, Decimal("0.45")),
    ],
    24: [
        (0, Decimal("0")),
        (18200, Decimal("0.19")),
        (45000, Decimal("0.325")),
        (120000, Decimal("0.37")),
        (180000, Decimal("0.45")),
    ],
    25: [
        (0, Decimal("0")),
        (18200, Decimal("0.16")),
        (45000, Decimal("0.30")),
        (135000, Decimal("0.37")),
        (190000, Decimal("0.45")),
    ],
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
    threshold = TAX_FREE_THRESHOLD.get(fy, TAX_FREE_THRESHOLD[25])
    if amt <= threshold:
        return Money(Decimal("0"), AUD)

    brackets = BRACKETS.get(fy, BRACKETS[25])
    tax = Decimal("0")

    for i, (threshold, rate) in enumerate(brackets):
        if amt <= threshold:
            break
        nxt = brackets[i + 1][0] if i + 1 < len(brackets) else amt
        taxable = min(amt, nxt) - threshold
        if taxable > 0:
            tax += taxable * rate

    return Money(tax, AUD)


def optimize_household(
    yours: Individual,
    janice: Individual,
) -> Allocation:
    """Allocate deductions & gains to minimize household tax.

    Strategy:
    - Fill tax-free thresholds first, then route deductions by marginal rate
    - Preserve gains/losses on original claimant
    - Minimize: your_tax + janice_tax
    """
    shared_deductions = yours.deductions + janice.deductions
    your_shared, janice_shared = allocate_deductions(
        yours.income,
        janice.income,
        shared_deductions,
        fy=yours.fy,
    )

    your_deductions = []
    if your_shared.amount > 0:
        your_deductions.append(your_shared)

    janice_deductions = []
    if janice_shared.amount > 0:
        janice_deductions.append(janice_shared)

    your_a = Individual(
        name=yours.name,
        fy=yours.fy,
        income=yours.income,
        deductions=your_deductions,
        gains=yours.gains,
        losses=yours.losses,
    )
    janice_a = Individual(
        name=janice.name,
        fy=janice.fy,
        income=janice.income,
        deductions=janice_deductions,
        gains=janice.gains,
        losses=janice.losses,
    )

    your_tax = _tax_liability(your_a.taxable_income, your_a.fy)
    janice_tax = _tax_liability(janice_a.taxable_income, janice_a.fy)

    return Allocation(
        yours=your_a,
        janice=janice_a,
        your_tax=your_tax,
        janice_tax=janice_tax,
    )
