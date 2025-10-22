import random
from pathlib import Path

from src.core.metrics import coverage
from src.core.models import Transaction
from src.io.ingest import ingest_year
from src.io.persist import from_csv


def _load_txns(base_dir: Path, fy: int, person: str | None = None) -> list[Transaction]:
    """Load classified transactions from pipeline output, fallback to raw."""
    base_dir = Path(base_dir)
    fy_dir = base_dir / "data" / f"fy{fy}"

    txns = []
    if fy_dir.exists():
        if person:
            dirs = [fy_dir / person]
        else:
            dirs = [d for d in fy_dir.iterdir() if d.is_dir() and (d / "data").exists()]

        for person_dir in dirs:
            csv_path = person_dir / "data" / "transactions.csv"
            if csv_path.exists():
                txns.extend(from_csv(csv_path, Transaction))

    return txns if txns else ingest_year(base_dir, fy, persons=[person] if person else None)


def handle(args):
    """Show coverage metrics and sample uncategorized transactions."""
    base_dir = Path(args.base_dir or ".")
    fy = args.fy
    person = args.person
    sample_size = args.sample

    txns = _load_txns(base_dir, fy, person)

    if not txns:
        print(f"\nNo transactions found for FY{fy}")
        return

    # Coverage metrics
    cov = coverage(txns)
    print(f"\nMining Coverage - FY{fy}")
    print("-" * 70)
    print(
        f"Transactions Categorized:     {cov['pct_txns']:>6.1f}% ({cov['count_labeled']}/{cov['count_total']})"
    )
    print(
        f"Outbound Spending Categorized: {cov['pct_debit']:>6.1f}% (${cov['debit_labeled']:>12,.0f}/${cov['debit_total']:>12,.0f})"
    )
    print(
        f"Inbound Income Categorized:    {cov['pct_credit']:>6.1f}% (${cov['credit_labeled']:>12,.0f}/${cov['credit_total']:>12,.0f})"
    )

    # Sample uncategorized
    if sample_size:
        uncategorized = [t for t in txns if not t.category and t.amount is not None]
        if uncategorized:
            sample = random.sample(uncategorized, min(sample_size, len(uncategorized)))
            sample = sorted(sample, key=lambda x: float(abs(x.amount)), reverse=True)
            print(f"\nUncategorized Sample ({len(sample)} of {len(uncategorized)})")
            print("-" * 70)
            for t in sample:
                print(f"{t.date} | {t.amount:>10.2f} | {t.description[:55]}")
        else:
            print("\nNo uncategorized transactions")


def register(subparsers):
    """Register coverage command."""
    parser = subparsers.add_parser(
        "coverage", help="Show coverage gaps & uncategorized transactions"
    )
    parser.add_argument("--fy", type=int, required=True, help="Fiscal year (e.g., 25)")
    parser.add_argument("--person", help="Person name (optional, all if omitted)")
    parser.add_argument("--sample", type=int, help="Sample N uncategorized transactions")
    parser.add_argument("--base-dir", default=".", help="Base directory (default: .)")
    parser.set_defaults(func=handle)
