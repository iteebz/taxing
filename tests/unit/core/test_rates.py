import pytest

from src.core.rates import (
    ATO_ALIGNED_RATES_CONSERVATIVE,
    ATO_ALIGNED_RATES_STANDARD,
    get_rate,
    get_rate_basis,
    validate_category,
)


def test_validate_category_valid():
    assert validate_category("work_accessories") is None
    assert validate_category("software") is None
    assert validate_category("home_office") is None


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
    with pytest.raises(ValueError, match="Unknown category"):
        validate_category("invalid_category_xyz")


def test_get_rate_standard():
    assert get_rate("home_office", conservative=False) == ATO_ALIGNED_RATES_STANDARD["home_office"]
    assert get_rate("vehicle", conservative=False) == ATO_ALIGNED_RATES_STANDARD["vehicle"]


def test_get_rate_conservative():
    assert (
        get_rate("home_office", conservative=True) == ATO_ALIGNED_RATES_CONSERVATIVE["home_office"]
    )
    assert get_rate("vehicle", conservative=True) == ATO_ALIGNED_RATES_CONSERVATIVE["vehicle"]
    assert get_rate("home_office", conservative=True) < get_rate("home_office", conservative=False)


def test_get_rate_prohibited():
    with pytest.raises(ValueError, match="never deductible"):
        get_rate("clothing")


def test_get_rate_basis():
    assert "DIVISION_63" in get_rate_basis("home_office")
    assert "S8_1" in get_rate_basis("vehicle")


def test_rates_conservative_lte_standard():
    for category in ATO_ALIGNED_RATES_STANDARD:
        assert category in ATO_ALIGNED_RATES_CONSERVATIVE
        conservative = ATO_ALIGNED_RATES_CONSERVATIVE[category]
        standard = ATO_ALIGNED_RATES_STANDARD[category]
        assert conservative <= standard
