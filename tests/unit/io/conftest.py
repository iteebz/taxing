from datetime import date
from decimal import Decimal

import pytest

from src.core.models import AUD, Money, Transaction


@pytest.fixture
def sample_anz_row():
    return {
        "date_raw": "01/10/2024",
        "amount": "100.50",
        "description_raw": "WOOLWORTHS SUPERMARKET",
        "source_person": "tyson",
    }


@pytest.fixture
def sample_cba_row():
    return {
        "date_raw": "02/10/2024",
        "amount": "-50.25",
        "description_raw": "AMAZON PURCHASE",
        "balance": "5000.00",
        "source_person": "jaynice",
    }


@pytest.fixture
def sample_beem_row():
    return {
        "datetime": "2024-10-03T14:30:00",
        "type": "PAYMENT",
        "reference": "ref123",
        "amount_str": "$250.00",
        "payer": "tyson",
        "recipient": "tysonchan",
        "message": "dinner split",
        "source_person": "tyson",
    }


@pytest.fixture
def sample_wise_row():
    return {
        "id": "tx123",
        "status": "COMPLETED",
        "direction": "out",
        "created_on": "2024-10-04T10:00:00",
        "finished_on": "2024-10-04T10:05:00",
        "source_fee_amount": "5.00",
        "source_fee_currency": "AUD",
        "target_fee_amount": "2.00",
        "target_fee_currency": "USD",
        "source_name": "tyson chan",
        "source_amount_after_fees": "495.00",
        "source_currency": "AUD",
        "target_name": "janice quach",
        "target_amount_after_fees": "300.00",
        "target_currency": "USD",
        "exchange_rate": "0.65",
        "reference": "ref456",
        "batch": "batch1",
        "source_person": "tyson",
    }


@pytest.fixture
def sample_txn():
    return Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("100.00"), AUD),
        description="woolworths supermarket",
        source_bank="anz",
        source_person="tyson",
    )


@pytest.fixture
def sample_txn_with_category():
    return Transaction(
        date=date(2024, 10, 1),
        amount=Money(Decimal("50.00"), AUD),
        description="groceries",
        source_bank="anz",
        source_person="tyson",
        category={"supermarkets", "groceries"},
    )
