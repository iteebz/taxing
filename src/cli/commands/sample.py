import random
from pathlib import Path

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
    """Sample transactions matching a keyword/pattern."""
    base_dir = Path(args.base_dir or ".")
    fy = args.fy
    keyword = args.keyword.lower()
    limit = args.limit
    labeled_only = args.labeled
    unlabeled_only = args.unlabeled

    txns = _load_txns(base_dir, fy, args.person)

    # Filter by keyword
    matches = [t for t in txns if keyword in t.description.lower()]

    # Filter by label status
    if labeled_only:
        matches = [t for t in matches if t.category]
    elif unlabeled_only:
        matches = [t for t in matches if not t.category]

    if not matches:
        print(f"\nNo transactions found matching '{keyword}'")
        return

    # Show summary
    labeled_count = len([t for t in matches if t.category])
    unlabeled_count = len([t for t in matches if not t.category])
    total_amt = sum(float(t.amount or 0) for t in matches)

    print(f"\nSample: '{keyword}' - FY{fy}")
    print("-" * 100)
    print(
        f"Total matches: {len(matches)} (labeled={labeled_count}, unlabeled={unlabeled_count}, total=${total_amt:,.0f})"
    )
    print("-" * 100)

    # Sample and sort by amount
    sample = random.sample(matches, min(limit, len(matches)))
    sample = sorted(sample, key=lambda x: float(abs(x.amount or 0)), reverse=True)

    for t in sample:
        status = "✓" if t.category else "✗"
        cat_str = ", ".join(sorted(t.category)) if t.category else "UNCATEGORIZED"
        date_str = t.date if t.date else "????-??-??"
        amt = float(t.amount) if t.amount else 0.0
        print(f"{status} {date_str} | {amt:>10.2f} | {cat_str:<25} | {t.description}")


def register(subparsers):
    """Register sample command."""
    parser = subparsers.add_parser("sample", help="Sample transactions by keyword")
    parser.add_argument("--fy", type=int, required=True, help="Fiscal year (e.g., 24)")
    parser.add_argument("--keyword", required=True, help="Keyword to search (case-insensitive)")
    parser.add_argument("--person", help="Person name (optional, all if omitted)")
    parser.add_argument("--limit", type=int, default=20, help="Max samples to show (default: 20)")
    parser.add_argument("--labeled", action="store_true", help="Only labeled transactions")
    parser.add_argument("--unlabeled", action="store_true", help="Only unlabeled transactions")
    parser.add_argument("--base-dir", default=".", help="Base directory (default: .)")
    parser.set_defaults(func=handle)
