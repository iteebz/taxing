from decimal import Decimal

from src.core.household import (
    _tax_liability,
    allocate_deductions,
    calculate_tax,
    optimize_household,
)
from src.core.models import Gain, Individual, Loss


def test_calculate_tax_single():
    ind = Individual(
        name="alice",
        fy=25,
        income=Decimal("60000"),
        deductions=[Decimal("5000")],
    )
    result = calculate_tax(ind)
    assert result.individual == ind
    assert result.liability.income_tax > Decimal("0")
    assert result.liability.total > Decimal("0")


def test_taxable_with_deduc():
    ind = Individual(
        name="you",
        fy=25,
        income=Decimal("50000"),
        deductions=[Decimal("5000"), Decimal("2000")],
    )
    assert ind.taxable_income == Decimal("43000")


def test_taxable_gains_loss():
    gains = [
        Gain(
            individual="you",
            fy=25,
            raw_profit=Decimal("1000"),
            taxable_gain=Decimal("500"),
        ),
        Gain(
            individual="you",
            fy=25,
            raw_profit=Decimal("-100"),
            taxable_gain=Decimal("-100"),
        ),
    ]
    ind = Individual(
        name="you",
        fy=25,
        income=Decimal("50000"),
        gains=gains,
    )
    assert ind.taxable_income == Decimal("50400")


def test_tax_under_thresh():
    liability = _tax_liability(Decimal("10000"), 25)
    assert liability.income_tax == Decimal("0")
    assert liability.medicare_levy == Decimal("0")
    assert liability.total == Decimal("0")


def test_tax_basic():
    liability = _tax_liability(Decimal("50000"), 25)
    b1 = (Decimal("45000") - Decimal("18200")) * Decimal("0.16")
    b2 = (Decimal("50000") - Decimal("45000")) * Decimal("0.30")
    expected_income_tax = b1 + b2
    assert liability.income_tax == expected_income_tax
    assert liability.medicare_levy == Decimal("1000")
    assert liability.total == expected_income_tax + Decimal("1000")


def test_low_inc_medicare():
    liability = _tax_liability(Decimal("26000"), 25)
    full_levy = Decimal("26000") * Decimal("0.02")
    reduced_levy = (Decimal("26000") - Decimal("24276")) * Decimal("0.10")
    assert liability.medicare_levy == min(full_levy, reduced_levy)


def test_high_inc_medicare():
    liability = _tax_liability(Decimal("120000"), 25)
    assert liability.medicare_levy == Decimal("2400")
    assert liability.total == liability.income_tax + Decimal("2400")


def test_opt_deduc_lower_bracket():
    person1 = Individual(
        name="person1",
        fy=25,
        income=Decimal("80000"),
        deductions=[Decimal("5000")],
    )
    person2 = Individual(
        name="person2",
        fy=25,
        income=Decimal("40000"),
        deductions=[Decimal("2000")],
    )

    result = optimize_household(person1, person2)

    assert result.person1.total_deductions == Decimal("7000")
    assert result.person2.total_deductions == Decimal("0")


def test_opt_preserve_gains_loss():
    gains = [
        Gain(
            individual="person1",
            fy=25,
            raw_profit=Decimal("1000"),
            taxable_gain=Decimal("500"),
        )
    ]
    [Loss(fy=25, amount=Decimal("100"), source_fy=24)]

    person1 = Individual(
        name="person1",
        fy=25,
        income=Decimal("50000"),
        gains=gains,
    )
    person2 = Individual(
        name="person2",
        fy=25,
        income=Decimal("40000"),
    )

    result = optimize_household(person1, person2)

    assert result.person1.gains == gains


def test_opt_household_tax():
    person1 = Individual(
        name="person1",
        fy=25,
        income=Decimal("80000"),
    )
    person2 = Individual(
        name="person2",
        fy=25,
        income=Decimal("40000"),
    )

    result = optimize_household(person1, person2)

    assert result.total == result.person1_liability.total + result.person2_liability.total


def test_opt_family_medicare():
    person1 = Individual(
        name="person1",
        fy=24,
        income=Decimal("24500"),
    )
    person2 = Individual(
        name="person2",
        fy=24,
        income=Decimal("16000"),
    )

    result = optimize_household(person1, person2)

    assert result.person1_liability.medicare_levy == Decimal("0")
    assert result.person2_liability.medicare_levy == Decimal("0")


def test_alloc_you_empty_janice_full():
    person1_deduction, person2_deduction = allocate_deductions(
        Decimal("0"),
        Decimal("30000"),
        [Decimal("5000"), Decimal("3000")],
        fy=25,
    )

    assert person1_deduction == Decimal("0")
    assert person2_deduction == Decimal("8000")


def test_alloc_you_buffer_janice_over():
    person1_deduction, person2_deduction = allocate_deductions(
        Decimal("10000"),
        Decimal("60000"),
        [Decimal("5000"), Decimal("5000")],
        fy=25,
    )

    assert person1_deduction == Decimal("0")
    assert person2_deduction == Decimal("10000")


def test_alloc_both_under():
    person1_deduction, person2_deduction = allocate_deductions(
        Decimal("15000"),
        Decimal("16000"),
        [Decimal("3000")],
        fy=25,
    )

    assert person1_deduction == Decimal("0")
    assert person2_deduction == Decimal("3000")


def test_alloc_insufficient():
    person1_deduction, person2_deduction = allocate_deductions(
        Decimal("10000"),
        Decimal("20000"),
        [Decimal("2000")],
        fy=25,
    )

    assert person1_deduction == Decimal("0")
    assert person2_deduction == Decimal("2000")


def test_alloc_excess_lower():
    person1_deduction, person2_deduction = allocate_deductions(
        Decimal("50000"),
        Decimal("30000"),
        [Decimal("10000")],
        fy=25,
    )

    assert person1_deduction == Decimal("10000")
    assert person2_deduction == Decimal("0")
