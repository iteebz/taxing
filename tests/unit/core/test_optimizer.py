from decimal import Decimal

from src.core.models import AUD, Money
from src.core.optimizer import (
    Individual,
    Year,
    bracket_headroom,
    current_bracket,
    greedy_allocation,
)


def test_individual_creation():
    """Individual model captures person's tax profile."""
    ind = Individual(
        name="tyson",
        employment_income=Money(Decimal("100000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
            (Decimal("190000"), Decimal("0.45")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    assert ind.name == "tyson"
    assert ind.employment_income.amount == Decimal("100000")
    assert len(ind.tax_brackets) == 4


def test_year_creation_single_person():
    """Year model with single person."""
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("100000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    year = Year(fy=25, persons={"tyson": tyson})

    assert year.fy == 25
    assert len(year.persons) == 1
    assert year.persons["tyson"].name == "tyson"


def test_year_creation_multiple_persons():
    """Year model with multiple persons."""
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("100000"), AUD),
        tax_brackets=[(Decimal("0"), Decimal("0.45"))],
        available_losses=Money(Decimal("0"), AUD),
    )
    janice = Individual(
        name="janice",
        employment_income=Money(Decimal("50000"), AUD),
        tax_brackets=[(Decimal("0"), Decimal("0.30"))],
        available_losses=Money(Decimal("0"), AUD),
    )

    year = Year(fy=25, persons={"tyson": tyson, "janice": janice})

    assert year.fy == 25
    assert len(year.persons) == 2
    assert year.persons["janice"].employment_income.amount == Decimal("50000")


def test_bracket_headroom_simple():
    """Calculate available space before next bracket."""
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("100000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
            (Decimal("190000"), Decimal("0.45")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    headroom = bracket_headroom(tyson)

    assert headroom == Decimal("35000")


def test_bracket_headroom_middle_bracket():
    """Headroom when income is in middle of brackets."""
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("90000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    headroom = bracket_headroom(tyson)

    assert headroom == Decimal("45000")


def test_bracket_headroom_above_all_brackets():
    """Headroom infinite when income exceeds highest bracket."""
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("200000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
            (Decimal("190000"), Decimal("0.45")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    headroom = bracket_headroom(tyson)

    assert headroom == Decimal("0")


def test_current_bracket_simple():
    """Determine current marginal tax rate."""
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("50000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    rate = current_bracket(tyson)

    assert rate == Decimal("0.30")


def test_current_bracket_zero_income():
    """Current bracket at zero income."""
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("0"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    rate = current_bracket(tyson)

    assert rate == Decimal("0.16")


def test_greedy_allocation_single_person():
    """Single person allocation is straightforward."""
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("50000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    year = Year(fy=25, persons={"tyson": tyson})

    deductions = [
        Money(Decimal("10000"), AUD),
        Money(Decimal("5000"), AUD),
    ]

    allocation = greedy_allocation(year, deductions)

    assert allocation["tyson"] == Money(Decimal("15000"), AUD)


def test_greedy_allocation_two_persons_different_brackets():
    """Deductions assigned to lowest bracket person first."""
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("150000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
            (Decimal("190000"), Decimal("0.45")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )
    janice = Individual(
        name="janice",
        employment_income=Money(Decimal("50000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    year = Year(fy=25, persons={"tyson": tyson, "janice": janice})

    deductions = [
        Money(Decimal("10000"), AUD),
    ]

    allocation = greedy_allocation(year, deductions)

    assert allocation["janice"] == Money(Decimal("10000"), AUD)
    assert allocation["tyson"] == Money(Decimal("0"), AUD)


def test_greedy_allocation_respects_headroom():
    """Deductions don't exceed bracket headroom."""
    janice = Individual(
        name="janice",
        employment_income=Money(Decimal("40000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    year = Year(fy=25, persons={"janice": janice})

    deductions = [
        Money(Decimal("10000"), AUD),
    ]

    allocation = greedy_allocation(year, deductions)

    assert allocation["janice"] == Money(Decimal("5000"), AUD)


def test_greedy_allocation_multiple_persons_fills_lowest_first():
    """All deductions assigned to lowest bracket person until full."""
    janice = Individual(
        name="janice",
        employment_income=Money(Decimal("30000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("50000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    year = Year(fy=25, persons={"janice": janice, "tyson": tyson})

    deductions = [
        Money(Decimal("20000"), AUD),
    ]

    allocation = greedy_allocation(year, deductions)

    assert allocation["janice"] == Money(Decimal("15000"), AUD)
    assert allocation["tyson"] == Money(Decimal("5000"), AUD)


def test_tax_savings_single_person():
    """Calculate tax savings from deductions."""
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("100000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    deduction_amt = Decimal("10000")
    marginal_rate = current_bracket(tyson)

    tax_savings = deduction_amt * marginal_rate

    assert tax_savings == Decimal("3000")


def test_tax_savings_different_brackets():
    """Tax savings differ by bracket assignment."""
    tyson = Individual(
        name="tyson",
        employment_income=Money(Decimal("150000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
            (Decimal("190000"), Decimal("0.45")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )
    janice = Individual(
        name="janice",
        employment_income=Money(Decimal("50000"), AUD),
        tax_brackets=[
            (Decimal("0"), Decimal("0.16")),
            (Decimal("45000"), Decimal("0.30")),
            (Decimal("135000"), Decimal("0.37")),
        ],
        available_losses=Money(Decimal("0"), AUD),
    )

    year = Year(fy=25, persons={"tyson": tyson, "janice": janice})
    deductions = [Money(Decimal("10000"), AUD)]

    allocation = greedy_allocation(year, deductions)

    janice_savings = allocation["janice"].amount * current_bracket(janice)
    tyson_savings = allocation["tyson"].amount * current_bracket(tyson)

    assert janice_savings == Decimal("3000")
    assert tyson_savings == Decimal("0")
