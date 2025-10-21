from decimal import Decimal

from src.core.models import Deduction, Loss
from src.core.optimizer import Individual


def validate_loss_reconciliation(losses: list[Loss], current_fy: int) -> list[str]:
    """Validate loss carryforward reconciliation for audit compliance.

    Returns list of validation errors (empty if valid).
    """
    errors = []

    for loss in losses:
        if loss.fy > current_fy:
            errors.append(f"Future loss: {loss.fy} (cannot anticipate losses before year ends)")
        if loss.source_fy > loss.fy:
            errors.append(
                f"Loss from {loss.source_fy} cannot apply to {loss.fy} "
                f"(losses applied in year incurred or later)"
            )

    return errors


def detect_suspicious_patterns(
    persons: dict[str, Individual],
    deductions: dict[str, list[Deduction]],
) -> list[str]:
    """Detect Division 19AA (anti-avoidance) red flags.

    Returns list of audit risk alerts.
    """
    alerts = []

    for name, ded_list in deductions.items():
        if name not in persons:
            continue

        person = persons[name]
        total_deductions = sum((d.amount.amount for d in ded_list), Decimal("0"))

        if person.employment_income.amount == 0:
            if total_deductions > 0:
                alerts.append(
                    f"{name}: $0 employment income but ${total_deductions} deductions claimed "
                    f"(high Division 19AA risk—no nexus to income)"
                )
        else:
            deduction_rate = total_deductions / person.employment_income.amount
            if deduction_rate > Decimal("0.50"):
                alerts.append(
                    f"{name}: Deductions {deduction_rate:.1%} of income "
                    f"(suspiciously high, typical 5-20%; Division 19AA risk)"
                )

            if deduction_rate > Decimal("0.75"):
                alerts.append(
                    f"{name}: Deductions exceed 75% of income "
                    f"(extreme, likely to be challenged in audit)"
                )

    return alerts


def generate_audit_statement(
    deductions: list[Deduction],
    fy: int,
) -> str:
    """Generate audit-ready nexus and rate basis statement."""
    if not deductions:
        return ""

    statement = [
        f"DEDUCTION AUDIT STATEMENT — FY{fy}",
        "=" * 60,
        "",
    ]

    by_category = {}
    for ded in deductions:
        if ded.category not in by_category:
            by_category[ded.category] = []
        by_category[ded.category].append(ded)

    for category in sorted(by_category.keys()):
        ded_list = by_category[category]
        total = sum((d.amount.amount for d in ded_list), Decimal("0"))
        count = len(ded_list)

        rate = ded_list[0].rate if ded_list else Decimal("0")
        rate_basis = ded_list[0].rate_basis if ded_list else ""

        statement.append(f"Category: {category}")
        statement.append(f"  Rate: {rate:.0%} ({rate_basis})")
        statement.append(f"  Transactions: {count}")
        statement.append(f"  Total claimed: ${total:.2f}")
        statement.append("")

    return "\n".join(statement)
