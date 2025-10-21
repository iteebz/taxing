import pytest

from src.core.rates import (
    DeductionDivision,
    DEDUCTIBLE_DIVISIONS,
    get_rate_basis,
    validate_category,
)


def test_validate_category_valid():
    # Test categories that are in DEDUCTIBLE_DIVISIONS and are deductible
    assert validate_category("work_accessories") is None
    assert validate_category("software") is None


def test_validate_category_not_in_deductible_divisions():
    # Test a category that is not in DEDUCTIBLE_DIVISIONS (e.g., a sub-category for actual cost)
    # It should not raise an error, as the calling function will handle it.
    assert validate_category("electricity") is None


def test_validate_category_prohibited():
    with pytest.raises(ValueError, match="never deductible"):
        validate_category("clothing")
    with pytest.raises(ValueError, match="never deductible"):
        validate_category("groceries")


def test_validate_category_error():
    with pytest.raises(ValueError, match="income"):
        validate_category("salary")
    with pytest.raises(ValueError, match="income"):
        validate_category("income")


def test_validate_category_unknown():
    # This case should now be handled by the calling function, not raise an error here
    assert validate_category("invalid_category_xyz") is None


def test_get_rate_basis_mapped():
    assert get_rate_basis("home_office") == "ATO_DIVISION_63_ACTUAL_COST"
    assert get_rate_basis("vehicle") == "ATO_ITAA97_S8_1_ACTUAL_COST"
    assert get_rate_basis("donations") == "ATO_DIVISION_30"
    assert get_rate_basis("meals") == "ATO_50PCT_RULE"


def test_get_rate_basis_default():
    assert get_rate_basis("software") == "ITAA97_DIVISION_8_NEXUS_SOFTWARE"
    assert get_rate_basis("work_accessories") == "ITAA97_DIVISION_8_NEXUS_WORK_ACCESSORIES"
