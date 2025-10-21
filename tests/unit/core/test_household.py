from decimal import Decimal

from src.core.household import _tax_liability, optimize_household
from src.core.models import AUD, Gain, Individual, Loss, Money


def test_taxable_income_with_deductions():
    ind = Individual(
        name="you",
        fy=25,
        income=Money(Decimal("50000"), AUD),
        deductions=[Money(Decimal("5000"), AUD), Money(Decimal("2000"), AUD)],
    )
    assert ind.taxable_income == Money(Decimal("43000"), AUD)


def test_taxable_income_with_gains_and_losses():
    gains = [
        Gain(
            fy=25,
            raw_profit=Money(Decimal("1000"), AUD),
            taxable_gain=Money(Decimal("500"), AUD),
            action="SELL",
        )
    ]
    losses = [Loss(fy=25, amount=Money(Decimal("100"), AUD), source_fy=24)]
    ind = Individual(
        name="you",
        fy=25,
        income=Money(Decimal("50000"), AUD),
        gains=gains,
        losses=losses,
    )
    assert ind.taxable_income == Money(Decimal("50400"), AUD)


def test_tax_liability_under_threshold():
    tax = _tax_liability(Money(Decimal("10000"), AUD), 25)
    assert tax == Money(Decimal("0"), AUD)


def test_tax_liability_basic():
    tax = _tax_liability(Money(Decimal("50000"), AUD), 25)
    b1 = (Decimal("45000") - Decimal("18200")) * Decimal("0.16")
    b2 = (Decimal("50000") - Decimal("45000")) * Decimal("0.30")
    expected = Money(b1 + b2, AUD)
    assert tax == expected


def test_optimize_household_routes_deductions_to_lower_bracket():
    yours = Individual(
        name="you",
        fy=25,
        income=Money(Decimal("80000"), AUD),
        deductions=[Money(Decimal("5000"), AUD)],
    )
    janice = Individual(
        name="janice",
        fy=25,
        income=Money(Decimal("40000"), AUD),
        deductions=[Money(Decimal("2000"), AUD)],
    )

    result = optimize_household(yours, janice)

    assert result.yours.total_deductions == Money(Decimal("0"), AUD)
    assert result.janice.total_deductions == Money(Decimal("7000"), AUD)


def test_optimize_household_preserves_gains_and_losses():
    gains = [
        Gain(
            fy=25,
            raw_profit=Money(Decimal("1000"), AUD),
            taxable_gain=Money(Decimal("500"), AUD),
            action="SELL",
        )
    ]
    losses = [Loss(fy=25, amount=Money(Decimal("100"), AUD), source_fy=24)]

    yours = Individual(
        name="you",
        fy=25,
        income=Money(Decimal("50000"), AUD),
        gains=gains,
        losses=losses,
    )
    janice = Individual(
        name="janice",
        fy=25,
        income=Money(Decimal("40000"), AUD),
    )

    result = optimize_household(yours, janice)

    assert result.yours.gains == gains
    assert result.yours.losses == losses


def test_optimize_household_household_tax():
    yours = Individual(
        name="you",
        fy=25,
        income=Money(Decimal("80000"), AUD),
    )
    janice = Individual(
        name="janice",
        fy=25,
        income=Money(Decimal("40000"), AUD),
    )

    result = optimize_household(yours, janice)

    assert result.total == result.your_tax + result.janice_tax
