from datetime import date
from decimal import Decimal

from src.core.models import Transaction
from src.core.transfers import (
    extract_recipient,
    is_transfer,
    net_position,
    reconcile_transfers,
)


def _txn(
    desc: str,
    person: str = "janice",
    amount: Decimal = Decimal("100.00"),
    category: set[str] | None = None,
):
    """Helper to create test transactions."""
    return Transaction(
        date=date(2024, 1, 1),
        amount=amount,
        description=desc,
        bank="anz",
        individual=person,
        category=category,
    )


def test_is_transfer_marked():
    txn = _txn("transfer to alice", category={"transfers"})
    assert is_transfer(txn)


def test_is_transfer_unmarked():
    txn = _txn("woolworths", category={"groceries"})
    assert not is_transfer(txn)


def test_is_transfer_none_category():
    txn = _txn("random", category=None)
    assert not is_transfer(txn)


def test_extract_recipient_transfer_to():
    assert extract_recipient("TRANSFER TO JANICE") == "janice"


def test_extract_recipient_direct_credit():
    assert extract_recipient("DIRECT CREDIT 141000 JANICE") == "janice"


def test_extract_recipient_transfer_to_ignore_bank():
    result = extract_recipient("TRANSFER TO OTHER BANK NETBANK SAVINGS")
    assert result is None


def test_extract_recipient_no_match():
    assert extract_recipient("WOOLWORTHS") is None


def test_reconcile_empty():
    txns = [_txn("random", category={"groceries"})]
    result = reconcile_transfers(txns)
    assert result == {}


def test_reconcile_single_transfer():
    txn = _txn("TRANSFER TO TYSON", category={"transfers"})
    result = reconcile_transfers([txn])
    assert len(result) == 1
    key = ("janice", "tyson")
    assert key in result
    assert result[key].amount == Decimal("100.00")
    assert result[key].txn_count == 1


def test_reconcile_multiple_transfers_same_person():
    txn1 = Transaction(
        date=date(2024, 1, 1),
        amount=Decimal("50.00"),
        description="TRANSFER TO TYSON",
        bank="anz",
        individual="janice",
        category={"transfers"},
    )
    txn2 = Transaction(
        date=date(2024, 1, 5),
        amount=Decimal("75.00"),
        description="TRANSFER TO TYSON",
        bank="cba",
        individual="janice",
        category={"transfers"},
    )
    result = reconcile_transfers([txn1, txn2])
    key = ("janice", "tyson")
    assert result[key].amount == Decimal("125.00")
    assert result[key].txn_count == 2
    assert result[key].date_first == "2024-01-01"
    assert result[key].date_last == "2024-01-05"


def test_net_position_owes():
    transfers = reconcile_transfers(
        [_txn("TRANSFER TO ALICE", person="janice", category={"transfers"})]
    )
    net = net_position(transfers, "janice")
    assert net == Decimal("100.00")


def test_net_position_owed():
    transfers = reconcile_transfers(
        [_txn("TRANSFER TO TYSON", person="janice", category={"transfers"})]
    )
    net = net_position(transfers, "tyson")
    assert net == Decimal("-100.00")


def test_net_position_balanced():
    janice_to_tyson = _txn("TRANSFER TO TYSON", person="janice", category={"transfers"})
    tyson_to_janice = Transaction(
        date=date(2024, 1, 2),
        amount=Decimal("100.00"),
        description="TRANSFER TO JANICE",
        bank="anz",
        individual="tyson",
        category={"transfers"},
    )
    transfers = reconcile_transfers([janice_to_tyson, tyson_to_janice])
    janice_net = net_position(transfers, "janice")
    tyson_net = net_position(transfers, "tyson")
    assert janice_net == Decimal("0.00")
    assert tyson_net == Decimal("0.00")
