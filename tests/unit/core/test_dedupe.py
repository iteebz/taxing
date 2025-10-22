from datetime import date
from decimal import Decimal

from src.core.dedupe import dedupe, fingerprint
from src.core.models import Transaction


def _txn(
    desc: str = "woolworths",
    person: str = "janice",
    amount: Decimal = Decimal("100.00"),
    bank: str = "cba",
    date_val: date = date(2024, 1, 1),
    category: set[str] | None = None,
):
    """Helper to create test transactions."""
    return Transaction(
        date=date_val,
        amount=amount,
        description=desc,
        bank=bank,
        individual=person,
        category=category,
    )


def test_same_merchant_txn_same_fingerprint():
    txn1 = _txn("WOOLWORTHS", person="janice", amount=Decimal("50.00"))
    txn2 = _txn("WOOLWORTHS", person="janice", amount=Decimal("50.00"))
    assert fingerprint(txn1) == fingerprint(txn2)


def test_different_amount_different_fingerprint():
    txn1 = _txn("WOOLWORTHS", amount=Decimal("50.00"))
    txn2 = _txn("WOOLWORTHS", amount=Decimal("51.00"))
    assert fingerprint(txn1) != fingerprint(txn2)


def test_different_date_different_fingerprint():
    txn1 = _txn("WOOLWORTHS", date_val=date(2024, 1, 1))
    txn2 = _txn("WOOLWORTHS", date_val=date(2024, 1, 2))
    assert fingerprint(txn1) != fingerprint(txn2)


def test_transfer_same_person_same_fingerprint():
    txn1 = _txn(
        "TRANSFER TO OTHER BANK NETBANK SAVINGS",
        person="janice",
        bank="cba",
        amount=Decimal("1000.00"),
    )
    txn2 = _txn("TRANSFER FROM OTHER BANK", person="janice", bank="anz", amount=Decimal("1000.00"))
    assert fingerprint(txn1) == fingerprint(txn2)


def test_p2p_transfer_both_sides_same_fingerprint():
    janice_sends = Transaction(
        date=date(2024, 1, 1),
        amount=Decimal("100.00"),
        description="TRANSFER TO TYSON PAYID PHONE FROM COMMBANK APP",
        bank="cba",
        individual="janice",
        category={"transfers"},
    )
    tyson_receives = Transaction(
        date=date(2024, 1, 1),
        amount=Decimal("100.00"),
        description="DIRECT CREDIT 141000 JANICE",
        bank="anz",
        individual="tyson",
        category={"transfers"},
    )
    assert fingerprint(janice_sends) == fingerprint(tyson_receives)


def test_different_person_different_fingerprint():
    txn1 = _txn("WOOLWORTHS", person="janice")
    txn2 = _txn("WOOLWORTHS", person="tyson")
    assert fingerprint(txn1) != fingerprint(txn2)


def test_category_ignored_in_fingerprint():
    txn1 = _txn("WOOLWORTHS")
    txn2 = _txn("WOOLWORTHS", category={"groceries"})
    assert fingerprint(txn1) == fingerprint(txn2)


def test_no_duplicates():
    txns = [
        _txn("WOOLWORTHS"),
        _txn("COLES"),
        _txn("UBER"),
    ]
    result = dedupe(txns)
    assert len(result) == 3


def test_merge_identical_txns():
    txn1 = _txn("WOOLWORTHS", bank="cba")
    txn2 = _txn("WOOLWORTHS", bank="cba")
    result = dedupe([txn1, txn2])
    assert len(result) == 1
    assert result[0].sources == frozenset({"cba"})


def test_merge_cross_bank_transfer():
    cba_txn = _txn("TRANSFER OUT", bank="cba")
    anz_txn = _txn("TRANSFER IN", bank="anz")
    result = dedupe([cba_txn, anz_txn])
    assert len(result) == 1
    assert result[0].sources == frozenset({"cba", "anz"})


def test_merge_p2p_transfer():
    janice_debit = Transaction(
        date=date(2024, 1, 1),
        amount=Decimal("100.00"),
        description="TRANSFER TO TYSON PAYID PHONE FROM COMMBANK APP",
        bank="cba",
        individual="janice",
        category={"transfers"},
    )
    tyson_credit = Transaction(
        date=date(2024, 1, 1),
        amount=Decimal("100.00"),
        description="DIRECT CREDIT 141000 JANICE",
        bank="anz",
        individual="tyson",
        category={"transfers"},
    )
    result = dedupe([janice_debit, tyson_credit])
    assert len(result) == 1
    assert result[0].sources == frozenset({"cba", "anz"})


def test_preserves_non_duplicate_txns():
    dup1 = _txn("WOOLWORTHS", bank="cba")
    dup2 = _txn("WOOLWORTHS", bank="cba")
    unique = _txn("UBER", bank="cba")
    result = dedupe([dup1, dup2, unique])
    assert len(result) == 2


def test_merge_uses_first_txn_as_base():
    txn1 = Transaction(
        date=date(2024, 1, 1),
        amount=Decimal("100.00"),
        description="WOOLWORTHS CHECKOUT",
        bank="cba",
        individual="janice",
        category={"groceries"},
    )
    txn2 = Transaction(
        date=date(2024, 1, 1),
        amount=Decimal("100.00"),
        description="WOOLWORTHS CHECKOUT",
        bank="anz",
        individual="janice",
        category=None,
    )
    result = dedupe([txn1, txn2])
    assert len(result) == 1
    assert result[0].description == "WOOLWORTHS CHECKOUT"
    assert result[0].category == {"groceries"}
    assert result[0].sources == frozenset({"cba", "anz"})


def test_multiple_duplicate_groups():
    group1_dup1 = _txn("WOOLWORTHS", bank="cba")
    group1_dup2 = _txn("WOOLWORTHS", bank="anz")
    group2_dup1 = _txn("UBER", bank="cba")
    group2_dup2 = _txn("UBER", bank="anz")
    result = dedupe([group1_dup1, group1_dup2, group2_dup1, group2_dup2])
    assert len(result) == 2


def test_source_txn_ids_tracked():
    txn1 = Transaction(
        date=date(2024, 1, 1),
        amount=Decimal("100.00"),
        description="WOOLWORTHS",
        bank="cba",
        individual="janice",
        source_txn_ids=("cba_001",),
    )
    txn2 = Transaction(
        date=date(2024, 1, 1),
        amount=Decimal("100.00"),
        description="WOOLWORTHS",
        bank="cba",
        individual="janice",
        source_txn_ids=("cba_002",),
    )
    result = dedupe([txn1, txn2])
    assert len(result[0].source_txn_ids) == 2
    assert "cba_001" in result[0].source_txn_ids
    assert "cba_002" in result[0].source_txn_ids


def test_empty_input():
    result = dedupe([])
    assert result == []


def test_single_txn():
    txn = _txn("WOOLWORTHS")
    result = dedupe([txn])
    assert len(result) == 1
    assert result[0].sources == frozenset({"cba"})
