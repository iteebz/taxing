from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from src.core.deduce import deduce
from src.core.models import AUD, Money, Transaction


@pytest.fixture
def mock_config_fy25():
    # Mock the config for FY25 to control test behavior
    return {
        "fy_2025": {
            "brackets": [],
            "actual_cost_categories": {
                "home_office": ["electricity", "internet"],
                "vehicle": ["fuel", "maintenance"],
            },
            "fixed_rates": {
                "donations": Decimal("1.0"),
                "meals": Decimal("0.5"),
            },
        }
    }


@pytest.fixture
def sample_txns():
    return [
        Transaction(
            date=date(2024, 10, 1),
            amount=Money(Decimal("100.00"), AUD),
            description="Electricity Bill",
            source_bank="anz",
            source_person="tyson",
            category={"electricity"},
            personal_pct=Decimal("0"),
        ),
        Transaction(
            date=date(2024, 10, 2),
            amount=Money(Decimal("50.00"), AUD),
            description="Internet Bill",
            source_bank="anz",
            source_person="tyson",
            category={"internet"},
            personal_pct=Decimal("0"),
        ),
        Transaction(
            date=date(2024, 10, 3),
            amount=Money(Decimal("200.00"), AUD),
            description="Fuel for Car",
            source_bank="anz",
            source_person="tyson",
            category={"fuel"},
            personal_pct=Decimal("0"),
        ),
        Transaction(
            date=date(2024, 10, 4),
            amount=Money(Decimal("75.00"), AUD),
            description="Donation to Charity",
            source_bank="anz",
            source_person="tyson",
            category={"donations"},
            personal_pct=Decimal("0"),
        ),
        Transaction(
            date=date(2024, 10, 5),
            amount=Money(Decimal("40.00"), AUD),
            description="Work Lunch",
            source_bank="anz",
            source_person="tyson",
            category={"meals"},
            personal_pct=Decimal("0"),
        ),
        Transaction(
            date=date(2024, 10, 6),
            amount=Money(Decimal("100.00"), AUD),
            description="Personal Shopping",
            source_bank="anz",
            source_person="tyson",
            category={"clothing"},
            personal_pct=Decimal("1"),
        ),
    ]


@patch("src.core.config.yaml.safe_load")
def test_actual_cost_deduction_home_office(mock_safe_load, mock_config_fy25, sample_txns):
    mock_safe_load.return_value = mock_config_fy25
    business_percentages = {"home_office": 0.8}
    ded_list = deduce(sample_txns[:2], fy=25, business_percentages=business_percentages)

    assert len(ded_list) == 1
    deduction = ded_list[0]
    assert deduction.category == "home_office"
    assert deduction.amount.amount == Decimal("120.00")  # (100 + 50) * 0.8
    assert deduction.rate == Decimal("0.8")
    assert deduction.rate_basis == "ATO_DIVISION_63_ACTUAL_COST"


@patch("src.core.config.yaml.safe_load")
def test_actual_cost_deduction_vehicle(mock_safe_load, mock_config_fy25, sample_txns):
    mock_safe_load.return_value = mock_config_fy25
    business_percentages = {"vehicle": 0.75}
    ded_list = deduce(sample_txns[2:3], fy=25, business_percentages=business_percentages)

    assert len(ded_list) == 1
    deduction = ded_list[0]
    assert deduction.category == "vehicle"
    assert deduction.amount.amount == Decimal("150.00")  # 200 * 0.75
    assert deduction.rate == Decimal("0.75")
    assert deduction.rate_basis == "ATO_ITAA97_S8_1_ACTUAL_COST"


@patch("src.core.config.yaml.safe_load")
def test_fixed_rate_deduction_donations(mock_safe_load, mock_config_fy25, sample_txns):
    mock_safe_load.return_value = mock_config_fy25
    business_percentages = {}
    ded_list = deduce(sample_txns[3:4], fy=25, business_percentages=business_percentages)

    assert len(ded_list) == 1
    deduction = ded_list[0]
    assert deduction.category == "donations"
    assert deduction.amount.amount == Decimal("75.00")  # 75 * 1.0
    assert deduction.rate == Decimal("1.0")
    assert deduction.rate_basis == "ATO_DIVISION_30"


@patch("src.core.config.yaml.safe_load")
def test_fixed_rate_deduction_meals(mock_safe_load, mock_config_fy25, sample_txns):
    mock_safe_load.return_value = mock_config_fy25
    business_percentages = {}
    ded_list = deduce(sample_txns[4:5], fy=25, business_percentages=business_percentages)

    assert len(ded_list) == 1
    deduction = ded_list[0]
    assert deduction.category == "meals"
    assert deduction.amount.amount == Decimal("20.00")  # 40 * 0.5
    assert deduction.rate == Decimal("0.5")
    assert deduction.rate_basis == "ATO_50PCT_RULE"


@patch("src.core.config.yaml.safe_load")
def test_multiple_deductions_combined(mock_safe_load, mock_config_fy25, sample_txns):
    mock_safe_load.return_value = mock_config_fy25
    business_percentages = {"home_office": 0.8, "vehicle": 0.75}
    ded_list = deduce(sample_txns[:5], fy=25, business_percentages=business_percentages)

    assert len(ded_list) == 4
    deductions_map = {d.category: d for d in ded_list}

    assert deductions_map["home_office"].amount.amount == Decimal("120.00")
    assert deductions_map["vehicle"].amount.amount == Decimal("150.00")
    assert deductions_map["donations"].amount.amount == Decimal("75.00")
    assert deductions_map["meals"].amount.amount == Decimal("20.00")


@patch("src.core.config.yaml.safe_load")
def test_empty_transactions(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    ded_list = deduce([], fy=25, business_percentages={})
    assert ded_list == []


@patch("src.core.config.yaml.safe_load")
def test_txn_no_category(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="RANDOM",
        source_bank="anz",
        source_person="tyson",
        category=None,
    )
    ded_list = deduce([txn], fy=25, business_percentages={})
    assert ded_list == []


@patch("src.core.config.yaml.safe_load")
def test_personal_pct_reduces_fixed_rate_deduction(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    txn = Transaction(
        date=date(2024, 10, 5),
        amount=Money(Decimal("40.00"), AUD),
        description="Work Lunch",
        source_bank="anz",
        source_person="tyson",
        category={"meals"},
        personal_pct=Decimal("0.5"),
    )
    ded_list = deduce([txn], fy=25, business_percentages={})
    assert len(ded_list) == 1
    # (40 * 0.5 rate) * (1 - 0.5 personal_pct) = 10.00
    assert ded_list[0].amount.amount == Decimal("10.00")


@patch("src.core.config.yaml.safe_load")
def test_prohibited_category_skipped(mock_safe_load, mock_config_fy25, sample_txns):
    mock_safe_load.return_value = mock_config_fy25
    # 'clothing' is in DEDUCTIBLE_DIVISIONS as PROHIBITED
    ded_list = deduce(sample_txns[5:6], fy=25, business_percentages={})
    assert len(ded_list) == 0


@patch("src.core.config.yaml.safe_load")
def test_ignores_foreign_currency(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    eur = "EUR"
    aud_txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="Electricity Bill",
        source_bank="anz",
        source_person="tyson",
        category={"electricity"},
    )
    eur_txn = Transaction(
        date=date(2024, 10, 2),
        amount=Money(Decimal("100.00"), eur),
        description="FOREIGN",
        source_bank="wise",
        source_person="tyson",
        category={"electricity"},
    )
    ded_list = deduce([aud_txn, eur_txn], fy=25, business_percentages={"home_office": 1.0})
    assert len(ded_list) == 1
    assert ded_list[0].amount.amount == Decimal("100.00")


@patch("src.core.config.yaml.safe_load")
def test_confidence_filtering(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    high_conf = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="Electricity Bill",
        source_bank="anz",
        source_person="tyson",
        category={"electricity"},
        confidence=0.9,
    )
    low_conf = Transaction(
        date=date(2024, 10, 2),
        amount=Money(Decimal("50.00"), AUD),
        description="Electricity Bill",
        source_bank="anz",
        source_person="tyson",
        category={"electricity"},
        confidence=0.3,
    )
    ded_list = deduce(
        [high_conf, low_conf], fy=25, business_percentages={"home_office": 1.0}, min_confidence=0.5
    )
    assert len(ded_list) == 1
    assert ded_list[0].amount.amount == Decimal("100.00")


@patch("src.core.config.yaml.safe_load")
def test_category_not_in_config_skipped(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="Unknown Category",
        source_bank="anz",
        source_person="tyson",
        category={"unknown_category"},
    )
    ded_list = deduce([txn], fy=25, business_percentages={})
    assert len(ded_list) == 0


@patch("src.core.config.yaml.safe_load")
def test_actual_cost_with_personal_pct_in_txn(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="Electricity Bill",
        source_bank="anz",
        source_person="tyson",
        category={"electricity"},
        personal_pct=Decimal("0.2"),  # This personal_pct should be ignored for actual cost
    )
    business_percentages = {"home_office": 0.8}
    ded_list = deduce([txn], fy=25, business_percentages=business_percentages)

    assert len(ded_list) == 1
    deduction = ded_list[0]
    # The personal_pct on the transaction is ignored for actual cost, only the overall business_percentage is used
    assert deduction.amount.amount == Decimal("80.00")  # 100 * 0.8


@patch("src.core.config.yaml.safe_load")
def test_fixed_rate_with_no_business_percentage_provided(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    txn = Transaction(
        date=date(2024, 10, 4),
        amount=Money(Decimal("75.00"), AUD),
        description="Donation to Charity",
        source_bank="anz",
        source_person="tyson",
        category={"donations"},
        personal_pct=Decimal("0"),
    )
    ded_list = deduce([txn], fy=25, business_percentages={})

    assert len(ded_list) == 1
    deduction = ded_list[0]
    assert deduction.category == "donations"
    assert deduction.amount.amount == Decimal(
        "75.00"
    )  # 75 * 1.0 (fixed rate) * (1 - 0 personal_pct)


@patch("src.core.config.yaml.safe_load")
def test_actual_cost_with_no_business_percentage_provided(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="Electricity Bill",
        source_bank="anz",
        source_person="tyson",
        category={"electricity"},
    )
    ded_list = deduce([txn], fy=25, business_percentages={})

    assert len(ded_list) == 0  # No business percentage provided for home_office, so no deduction
