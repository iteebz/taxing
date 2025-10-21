from decimal import Decimal

from src.core.audit import (
    detect_suspicious_patterns,
    generate_audit_statement,
    validate_loss_reconciliation,
)
from src.core.models import Deduction, Individual, Loss


def test_validate_loss_reconciliation_valid():
    losses = [
        Loss(fy=25, amount=Decimal("1000"), source_fy=24),
        Loss(fy=26, amount=Decimal("500"), source_fy=25),
    ]
    errors = validate_loss_reconciliation(losses, current_fy=26)
    assert errors == []


def test_validate_loss_reconciliation_future_loss():
    losses = [
        Loss(fy=27, amount=Decimal("1000"), source_fy=27),
    ]
    errors = validate_loss_reconciliation(losses, current_fy=26)
    assert len(errors) == 1
    assert "Future loss" in errors[0]


def test_validate_loss_reconciliation_wrong_sequence():
    losses = [
        Loss(fy=24, amount=Decimal("1000"), source_fy=25),
    ]
    errors = validate_loss_reconciliation(losses, current_fy=26)
    assert len(errors) == 1
    assert "cannot apply" in errors[0]


def test_zero_income_deduc():
    persons = {
        "tyson": Individual(
            name="tyson",
            fy=25,
            income=Decimal("0"),
        )
    }
    deductions = {
        "tyson": [
            Deduction(
                category="software",
                amount=Decimal("5000"),
                rate=Decimal("1.0"),
                rate_basis="test",
                fy=25,
            )
        ]
    }
    alerts = detect_suspicious_patterns(persons, deductions)
    assert len(alerts) == 1
    assert "Division 19AA" in alerts[0]


def test_high_deduc_rate():
    persons = {
        "tyson": Individual(
            name="tyson",
            fy=25,
            income=Decimal("100000"),
        )
    }
    deductions = {
        "tyson": [
            Deduction(
                category="software",
                amount=Decimal("60000"),
                rate=Decimal("1.0"),
                rate_basis="test",
                fy=25,
            )
        ]
    }
    alerts = detect_suspicious_patterns(persons, deductions)
    assert len(alerts) >= 1
    assert "60" in alerts[0]


def test_extreme_deduc_rate():
    persons = {
        "tyson": Individual(
            name="tyson",
            fy=25,
            income=Decimal("100000"),
        )
    }
    deductions = {
        "tyson": [
            Deduction(
                category="software",
                amount=Decimal("80000"),
                rate=Decimal("1.0"),
                rate_basis="test",
                fy=25,
            )
        ]
    }
    alerts = detect_suspicious_patterns(persons, deductions)
    assert len(alerts) >= 1
    assert any("75" in alert for alert in alerts)


def test_normal_deduc_rate():
    persons = {
        "tyson": Individual(
            name="tyson",
            fy=25,
            income=Decimal("100000"),
        )
    }
    deductions = {
        "tyson": [
            Deduction(
                category="software",
                amount=Decimal("10000"),
                rate=Decimal("1.0"),
                rate_basis="test",
                fy=25,
            )
        ]
    }
    alerts = detect_suspicious_patterns(persons, deductions)
    assert len(alerts) == 0


def test_generate_audit_statement_empty():
    statement = generate_audit_statement([], 25)
    assert statement == ""


def test_audit_single_cat():
    deductions = [
        Deduction(
            category="software",
            amount=Decimal("5000"),
            rate=Decimal("1.0"),
            rate_basis="ATO_DIVISION_8",
            fy=25,
        )
    ]
    statement = generate_audit_statement(deductions, 25)
    assert "DEDUCTION AUDIT STATEMENT" in statement
    assert "FY25" in statement
    assert "software" in statement
    assert "100%" in statement
    assert "5000" in statement


def test_audit_multi_cat():
    deductions = [
        Deduction(
            category="software",
            amount=Decimal("5000"),
            rate=Decimal("1.0"),
            rate_basis="ATO_DIVISION_8",
            fy=25,
        ),
        Deduction(
            category="home_office",
            amount=Decimal("3000"),
            rate=Decimal("0.45"),
            rate_basis="ATO_DIVISION_63_SIMPLIFIED",
            fy=25,
        ),
    ]
    statement = generate_audit_statement(deductions, 25)
    assert "software" in statement
    assert "home_office" in statement
    assert "100%" in statement
    assert "45%" in statement
