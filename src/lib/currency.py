from decimal import Decimal


def to_aud(amount: Decimal, currency: str, rate: Decimal) -> Decimal:
    """Convert foreign currency amount to AUD using provided exchange rate.

    Args:
        amount: Amount in foreign currency
        currency: ISO currency code (e.g., 'USD', 'EUR')
        rate: Exchange rate (foreign currency units per AUD)

    Returns:
        Amount in AUD

    Raises:
        ValueError: If currency is AUD (no conversion needed)
    """
    if currency == "AUD":
        raise ValueError("Cannot convert AUD to AUD")

    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    if not isinstance(rate, Decimal):
        rate = Decimal(str(rate))

    if rate <= 0:
        raise ValueError(f"Exchange rate must be positive, got {rate}")

    return amount * rate
