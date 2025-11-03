import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.deduce import deduce
from src.core.models import Transaction


@pytest.fixture
def mock_config_fy25():
    return {
        "deductions": {
            "home_office": ["electricity", "internet"],
            "vehicle": ["fuel", "maintenance"],
        },
        "rate_basis": {
            "home_office": "ATO_DIVISION_63_ACTUAL_COST",
            "vehicle": "ATO_ITAA97_S8_1_ACTUAL_COST",
        },
        "fy_2025": {
            "brackets": [],
            "medicare": {
                "base_rate": 0.02,
                "low_income_threshold_single": 24276,
                "phase_in_rate_single": 0.10,
                "low_income_threshold_family": 40939,
                "phase_in_rate_family": 0.10,
                "dependent_increment": 3760,
            },
        },
    }


@pytest.fixture
def sample_txns():
    return [
        Transaction(
            date=date(2024, 10, 1),
            amount=Decimal("100.00"),
            description="Electricity Bill",
            bank="anz",
            individual="tyson",
            cats={"electricity"},
            personal_pct=Decimal("0"),
        ),
        Transaction(
            date=date(2024, 10, 2),
            amount=Decimal("50.00"),
            description="Internet Bill",
            bank="anz",
            individual="tyson",
            cats={"internet"},
            personal_pct=Decimal("0"),
        ),
        Transaction(
            date=date(2024, 10, 3),
            amount=Decimal("200.00"),
            description="Fuel for Car",
            bank="anz",
            individual="tyson",
            cats={"fuel"},
            personal_pct=Decimal("0"),
        ),
        Transaction(
            date=date(2024, 10, 4),
            amount=Decimal("75.00"),
            description="Donation to Charity",
            bank="anz",
            individual="tyson",
            cats={"donations"},
            personal_pct=Decimal("0"),
        ),
        Transaction(
            date=date(2024, 10, 5),
            amount=Decimal("40.00"),
            description="Work Lunch",
            bank="anz",
            individual="tyson",
            cats={"meals"},
            personal_pct=Decimal("0"),
        ),
        Transaction(
            date=date(2024, 10, 6),
            amount=Decimal("100.00"),
            description="Personal Shopping",
            bank="anz",
            individual="tyson",
            cats={"clothing"},
            personal_pct=Decimal("1"),
        ),
    ]


@patch("src.core.config.yaml.safe_load")
def test_actual_cost_deduction_home_office(mock_safe_load, mock_config_fy25, sample_txns):
    mock_safe_load.return_value = mock_config_fy25
    business_percentages = {"home_office": 0.8}
    ded_list = deduce(
        sample_txns[:2], fy=25, individual="tyson", business_percentages=business_percentages
    )

    assert len(ded_list) == 1
    deduction = ded_list[0]
    assert deduction.category == "home_office"
    assert deduction.amount == Decimal("120.00")  # (100 + 50) * 0.8
    assert deduction.rate == Decimal("0.8")
    assert deduction.rate_basis == "ATO_DIVISION_63_ACTUAL_COST"


@patch("src.core.config.yaml.safe_load")
def test_actual_cost_deduction_vehicle(mock_safe_load, mock_config_fy25, sample_txns):
    mock_safe_load.return_value = mock_config_fy25
    business_percentages = {"vehicle": 0.75}
    ded_list = deduce(
        sample_txns[2:3], fy=25, individual="tyson", business_percentages=business_percentages
    )

    assert len(ded_list) == 1
    deduction = ded_list[0]
    assert deduction.category == "vehicle"
    assert deduction.amount == Decimal("150.00")  # 200 * 0.75
    assert deduction.rate == Decimal("0.75")
    assert deduction.rate_basis == "ATO_ITAA97_S8_1_ACTUAL_COST"


@patch("src.core.config.yaml.safe_load")
def test_multiple_deductions_combined(mock_safe_load, mock_config_fy25, sample_txns):
    mock_safe_load.return_value = mock_config_fy25
    business_percentages = {"home_office": 0.8, "vehicle": 0.75}
    ded_list = deduce(
        sample_txns[:3], fy=25, individual="tyson", business_percentages=business_percentages
    )

    assert len(ded_list) == 2
    deductions_map = {d.category: d for d in ded_list}

    assert deductions_map["home_office"].amount == Decimal("120.00")
    assert deductions_map["vehicle"].amount == Decimal("150.00")


@patch("src.core.config.yaml.safe_load")
def test_empty_transactions(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    ded_list = deduce([], fy=25, individual="tyson", business_percentages={})
    assert ded_list == []


@patch("src.core.config.yaml.safe_load")
def test_txn_no_category(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Decimal("100.00"),
        description="RANDOM",
        bank="anz",
        individual="tyson",
        cats=None,
    )
    ded_list = deduce([txn], fy=25, individual="tyson", business_percentages={})
    assert ded_list == []


@patch("src.core.config.yaml.safe_load")
def test_category_not_in_deductions_skipped(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Decimal("100.00"),
        description="Donation",
        bank="anz",
        individual="tyson",
        cats={"donations"},
    )
    ded_list = deduce([txn], fy=25, individual="tyson", business_percentages={})
    assert len(ded_list) == 0  # donations not in deductions groups


@patch("src.core.config.yaml.safe_load")
def test_actual_cost_no_business_pct(mock_safe_load, mock_config_fy25):
    mock_safe_load.return_value = mock_config_fy25
    txn = Transaction(
        date=date(2024, 10, 1),
        amount=Decimal("100.00"),
        description="Electricity Bill",
        bank="anz",
        individual="tyson",
        cats={"electricity"},
    )
    ded_list = deduce([txn], fy=25, individual="tyson", business_percentages={})

    assert len(ded_list) == 0  # No business percentage provided, no deduction


@patch("src.core.config.yaml.safe_load")
def test_weights_applied(mock_safe_load, mock_config_fy25):
    """Test that weights from weights.csv are applied correctly."""
    mock_safe_load.return_value = mock_config_fy25

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("category,weight\n")
        f.write("electricity,0.5\n")
        f.write("internet,1.0\n")
        weights_path = Path(f.name)

    try:
        txns = [
            Transaction(
                date=date(2024, 10, 1),
                amount=Decimal("100.00"),
                description="Electricity",
                bank="anz",
                individual="tyson",
                cats={"electricity"},
            ),
            Transaction(
                date=date(2024, 10, 2),
                amount=Decimal("50.00"),
                description="Internet",
                bank="anz",
                individual="tyson",
                cats={"internet"},
            ),
        ]

        business_percentages = {"home_office": 1.0}
        ded_list = deduce(
            txns,
            fy=25,
            individual="tyson",
            business_percentages=business_percentages,
            weights_path=weights_path,
        )

        assert len(ded_list) == 1
        # (100 * 0.5) + (50 * 1.0) = 50 + 50 = 100
        assert ded_list[0].amount == Decimal("100.00")
    finally:
        weights_path.unlink()
