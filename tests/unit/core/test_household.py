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
    liability = _tax_liability(Money(Decimal("10000"), AUD), 25)
    assert liability.income_tax == Money(Decimal("0"), AUD)
    assert liability.medicare_levy == Money(Decimal("0"), AUD)
    assert liability.total == Money(Decimal("0"), AUD)


def test_tax_liability_basic():
    liability = _tax_liability(Money(Decimal("50000"), AUD), 25)
    b1 = (Decimal("45000") - Decimal("18200")) * Decimal("0.16")
    b2 = (Decimal("50000") - Decimal("45000")) * Decimal("0.30")
    expected_income_tax = Money(b1 + b2, AUD)
    assert liability.income_tax == expected_income_tax
    assert liability.medicare_levy == Money(Decimal("1000"), AUD)
    assert liability.total == expected_income_tax + Money(Decimal("1000"), AUD)


def test_tax_liability_low_income_medicare_reduction():
    liability = _tax_liability(Money(Decimal("26000"), AUD), 25)
    full_levy = Decimal("26000") * Decimal("0.02")
    reduced_levy = (Decimal("26000") - Decimal("24276")) * Decimal("0.10")
    assert liability.medicare_levy == Money(min(full_levy, reduced_levy), AUD)


def test_tax_liability_high_income_full_medicare():
    liability = _tax_liability(Money(Decimal("120000"), AUD), 25)
    assert liability.medicare_levy == Money(Decimal("2400"), AUD)
    assert liability.total == liability.income_tax + Money(Decimal("2400"), AUD)


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

    assert result.total == result.your_liability.total + result.janice_liability.total


def test_optimize_household_applies_family_medicare_threshold():
    yours = Individual(
        name="you",
        fy=24,
        income=Money(Decimal("24500"), AUD),
    )
    janice = Individual(
        name="janice",
        fy=24,
        income=Money(Decimal("16000"), AUD),
    )

    result = optimize_household(yours, janice)

    assert result.your_liability.medicare_levy == Money(Decimal("0"), AUD)
    assert result.janice_liability.medicare_levy == Money(Decimal("0"), AUD)
