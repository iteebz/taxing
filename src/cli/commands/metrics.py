from pathlib import Path

from src.core.metrics import coverage, household_metrics
from src.core.models import Transaction
from src.io.ingest import ingest_year
from src.io.persist import from_csv


def _load_classified_txns(base_dir: Path, fy: int, person: str | None = None) -> list[Transaction]:
    """Load classified transactions from output CSVs, falling back to raw if not found."""
    persons = [person] if person else None
    fy_dir = base_dir / "data" / f"fy{fy}"

    if not fy_dir.exists():
        return ingest_year(base_dir, fy, persons=persons)

    txns = []
    if persons:
        dirs = [fy_dir / p for p in persons if (fy_dir / p).exists()]
    else:
        dirs = [d for d in fy_dir.iterdir() if d.is_dir() and (d / "data").exists()]

    for person_dir in dirs:
        csv_path = person_dir / "data" / "transactions.csv"
        if csv_path.exists():
            txns.extend(from_csv(csv_path, Transaction))

    if txns:
        return txns

    return ingest_year(base_dir, fy, persons=persons)


def handle(args):
    """Calculate coverage and household metrics."""
    base_dir = Path(args.base_dir or ".")
    fy = args.fy
    person = args.person

    all_txns = _load_classified_txns(base_dir, fy, person)

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
    print(f"{'Individual':<20} {'Spending':<18} {'Income':<18} {'Transfers':<18}")
    print("-" * 70)

    for individual in household["persons"]:
        print(
            f"{individual:<20} "
            f"${household['spending_by_person'].get(individual, 0):<17,.0f} "
            f"${household['income_by_person'].get(individual, 0):<17,.0f} "
            f"${household['transfers_by_person'].get(individual, 0):<17,.0f}"
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
