from datetime import date
from decimal import Decimal

from src.core.models import AUD, Money, Transaction
from src.core.transfers import (
    extract_recipient,
    is_transfer,
    net_position,
    reconcile_transfers,
)


def _txn(
    desc: str,
    person: str = "bob",
    amount: Decimal = Decimal("100.00"),
    category: set[str] | None = None,
):
    """Helper to create test transactions."""
    return Transaction(
        date=date(2024, 1, 1),
        amount=Money(amount, AUD),
        description=desc,
        source_bank="anz",
        source_person=person,
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
    assert extract_recipient("TRANSFER TO ALICE") == "alice"


def test_extract_recipient_direct_credit():
    assert extract_recipient("DIRECT CREDIT 141000 ALICE") == "alice"


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
    txn = _txn("TRANSFER TO ALICE", category={"transfers"})
    result = reconcile_transfers([txn])
    assert len(result) == 1
    key = ("bob", "alice")
    assert key in result
    assert result[key].amount.amount == Decimal("100.00")
    assert result[key].txn_count == 1


def test_reconcile_multiple_transfers_same_person():
    txn1 = Transaction(
        date=date(2024, 1, 1),
        amount=Money(Decimal("50.00"), AUD),
        description="TRANSFER TO ALICE",
        source_bank="anz",
        source_person="bob",
        category={"transfers"},
    )
    txn2 = Transaction(
        date=date(2024, 1, 5),
        amount=Money(Decimal("75.00"), AUD),
        description="TRANSFER TO ALICE",
        source_bank="cba",
        source_person="bob",
        category={"transfers"},
    )
    result = reconcile_transfers([txn1, txn2])
    key = ("bob", "alice")
    assert result[key].amount.amount == Decimal("125.00")
    assert result[key].txn_count == 2
    assert result[key].date_first == "2024-01-01"
    assert result[key].date_last == "2024-01-05"


def test_net_position_owes():
    transfers = reconcile_transfers(
        [_txn("TRANSFER TO ALICE", person="bob", category={"transfers"})]
    )
    net = net_position(transfers, "bob")
    assert net.amount == Decimal("100.00")


def test_net_position_owed():
    transfers = reconcile_transfers(
        [_txn("TRANSFER TO ALICE", person="bob", category={"transfers"})]
    )
    net = net_position(transfers, "alice")
    assert net.amount == Decimal("-100.00")


def test_net_position_balanced():
    bob_to_alice = _txn("TRANSFER TO ALICE", person="bob", category={"transfers"})
    alice_to_bob = Transaction(
        date=date(2024, 1, 2),
        amount=Money(Decimal("100.00"), AUD),
        description="TRANSFER TO BOB",
        source_bank="anz",
        source_person="alice",
        category={"transfers"},
    )
    transfers = reconcile_transfers([bob_to_alice, alice_to_bob])
    bob_net = net_position(transfers, "bob")
    alice_net = net_position(transfers, "alice")
    assert bob_net.amount == Decimal("0.00")
    assert alice_net.amount == Decimal("0.00")
