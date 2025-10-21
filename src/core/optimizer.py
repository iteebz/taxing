from dataclasses import dataclass
from decimal import Decimal

from src.core.models import AUD, Money


@dataclass(frozen=True)
class Individual:
    """Tax-relevant characteristics of a person in a given year.

    Represents a single person's tax profile for optimization:
    - name: Person identifier
    - employment_income: W2-equivalent income (salary, wages)
    - tax_brackets: [(threshold, rate), ...] ordered by threshold
    - available_losses: Capital losses available for current year

    Example (FY25 Australia):
        Individual(
            name="alice",
            employment_income=Money(Decimal("100000"), AUD),
            tax_brackets=[
                (Decimal("0"), Decimal("0.16")),
                (Decimal("45000"), Decimal("0.30")),
                (Decimal("135000"), Decimal("0.37")),
                (Decimal("190000"), Decimal("0.45")),
            ],
            available_losses=Money(Decimal("0"), AUD),
        )
    """

    name: str
    employment_income: Money
    tax_brackets: list[tuple[Decimal, Decimal]]
    available_losses: Money


@dataclass(frozen=True)
class Year:
    """Multi-person tax year context.

    - fy: Fiscal year (e.g., 25 for FY2024-25)
    - persons: All individuals for this year, keyed by name
    """

    fy: int
    persons: dict[str, Individual]


def bracket_headroom(person: Individual) -> Decimal:
    """Calculate income space before next tax bracket tier.

    E.g., if income=$100k and brackets are [0, 45k, 135k, 190k],
    headroom is $35k (distance to $135k).

    Returns 0 if income exceeds all brackets.
    """
    income = person.employment_income.amount

    for _i, (threshold, _rate) in enumerate(person.tax_brackets):
        if income < threshold:
            return threshold - income

    return Decimal("0")


def current_bracket(person: Individual) -> Decimal:
    """Get marginal tax rate at current income level.

    E.g., if income=$100k and brackets are [0, 45k, 135k],
    return 0.30 (30% rate applies at $45k-$135k).
    """
    income = person.employment_income.amount

    rate = Decimal("0")
    for threshold, bracket_rate in person.tax_brackets:
        if income >= threshold:
            rate = bracket_rate
        else:
            break

    return rate


def greedy_allocation(
    year: Year,
    deductions: list[Money],
) -> dict[str, Money]:
    """Assign deductions to minimize total tax liability across all persons.

    Algorithm: Greedy lowest-bracket-first
    1. Sort persons by marginal tax rate (lowest first)
    2. For each person, assign deductions up to bracket headroom
    3. Continue with next person until all deductions allocated

    This maximizes tax savings by applying deductions to lower-bracket
    persons first (wider tax rate gaps).

    Args:
        year: Multi-person year context
        deductions: List of Money amounts to allocate

    Returns:
        Dict mapping person name -> Money allocated

    Example:
        alice (50% bracket, $10k headroom) + bob (30% bracket, $50k headroom)
        $60k deductions:
        - Bob gets $50k (30% bracket, full headroom)
        - Alice gets $10k (50% bracket, headroom limit)
    """
    result = {name: Money(Decimal("0"), AUD) for name in year.persons}

    remaining = sum((d.amount for d in deductions), Decimal("0"))

    persons_by_bracket = sorted(
        year.persons.items(),
        key=lambda x: current_bracket(x[1]),
    )

    for name, person in persons_by_bracket:
        if remaining <= 0:
            break

        room = bracket_headroom(person)
        allocated = min(remaining, room)

        result[name] = Money(allocated, AUD)
        remaining -= allocated

    return result
