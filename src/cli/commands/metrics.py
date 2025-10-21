from pathlib import Path

from src.core.metrics import coverage, household_metrics
from src.io.ingest import ingest_year


def handle(args):
    """Calculate coverage and household metrics."""
    base_dir = Path(args.base_dir or ".")
    fy = args.fy
    person = args.person

    if person:
        all_txns = ingest_year(base_dir, fy, persons=[person])
    else:
        all_txns = ingest_year(base_dir, fy)

    if not all_txns:
        print(f"\nNo transactions found for FY{fy}")
        return

    cov = coverage(all_txns)
    household = household_metrics(all_txns)

    print(f"\nCoverage Metrics - FY{fy}")
    print("-" * 70)
    print(
        f"{'Transactions Categorized':<35} {cov['pct_txns']:>6.1f}% ({cov['count_labeled']}/{cov['count_total']})"
    )
    print(
        f"{'Outbound Spending Categorized':<35} {cov['pct_debit']:>6.1f}% (${cov['debit_labeled']:>12,.0f}/${cov['debit_total']:>12,.0f})"
    )
    print(
        f"{'Inbound Income Categorized':<35} {cov['pct_credit']:>6.1f}% (${cov['credit_labeled']:>12,.0f}/${cov['credit_total']:>12,.0f})"
    )

    print("\nHousehold Metrics")
    print("-" * 70)
    print(f"{'Person':<20} {'Spending':<18} {'Income':<18} {'Transfers':<18}")
    print("-" * 70)

    for person in household["persons"]:
        print(
            f"{person:<20} "
            f"${household['spending_by_person'].get(person, 0):<17,.0f} "
            f"${household['income_by_person'].get(person, 0):<17,.0f} "
            f"${household['transfers_by_person'].get(person, 0):<17,.0f}"
        )

    print("-" * 70)
    print(
        f"{'TOTAL':<20} "
        f"${household['total_spending']:<17,.0f} "
        f"${household['total_income']:<17,.0f} "
        f"${household['total_transfers']:<17,.0f}"
    )


def register(subparsers):
    """Register metrics command."""
    parser = subparsers.add_parser("metrics", help="Calculate coverage & household metrics")
    parser.add_argument("--fy", type=int, required=True, help="Fiscal year (e.g., 25)")
    parser.add_argument("--person", help="Person name (optional, all if omitted)")
    parser.add_argument("--base-dir", default=".", help="Base directory (default: .)")
    parser.set_defaults(func=handle)
