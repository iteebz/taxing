from decimal import Decimal

import pytest

from src.lib.currency import to_aud


def test_to_aud_usd():
    result = to_aud(Decimal("100"), "USD", Decimal("0.65"))
    assert result == Decimal("65")


def test_to_aud_gbp():
    result = to_aud(Decimal("100"), "GBP", Decimal("0.52"))
    assert result == Decimal("52")


def test_to_aud_preserves_precision():
    result = to_aud(Decimal("123.456"), "USD", Decimal("0.673"))
    assert result == Decimal("123.456") * Decimal("0.673")


def test_to_aud_with_string_conversion():
    result = to_aud("100", "USD", "0.65")
    assert result == Decimal("65")


def test_to_aud_rejects_aud():
    with pytest.raises(ValueError, match="Cannot convert AUD to AUD"):
        to_aud(Decimal("100"), "AUD", Decimal("1"))


def test_to_aud_rejects_zero_rate():
    with pytest.raises(ValueError, match="Exchange rate must be positive"):
        to_aud(Decimal("100"), "USD", Decimal("0"))


def test_to_aud_rejects_negative_rate():
    with pytest.raises(ValueError, match="Exchange rate must be positive"):
        to_aud(Decimal("100"), "USD", Decimal("-0.65"))
