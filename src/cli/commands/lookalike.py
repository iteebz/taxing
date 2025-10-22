from difflib import SequenceMatcher
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


def _similarity(desc1: str, desc2: str) -> float:
    """Compute string similarity 0.0-1.0."""
    return SequenceMatcher(None, desc1.lower(), desc2.lower()).ratio()


def handle(args):
    """Find labeled transactions similar to an unlabeled one."""
    base_dir = Path(args.base_dir or ".")
    fy = args.fy
    txn_idx = args.index
    limit = args.limit

    txns = _load_txns(base_dir, fy, args.person)

    if txn_idx >= len(txns) or txn_idx < 0:
        print(f"Invalid index {txn_idx}, max={len(txns) - 1}")
        return

    target = txns[txn_idx]

    if target.category:
        print(f"Transaction {txn_idx} is already labeled as {target.category}")
        return

    # Find similar labeled transactions
    labeled = [t for t in txns if t.category]
    sims = [(t, _similarity(target.description, t.description)) for t in labeled]
    sims = sorted(sims, key=lambda x: -x[1])[:limit]

    date_str = target.date if target.date else "????-??-??"
    amt = float(target.amount) if target.amount else 0.0

    print(f"\nLookalike - Transaction {txn_idx}")
    print("-" * 100)
    print(f"Target: {date_str} | {amt:>10.2f} | {target.description}")
    print("-" * 100)
    print(f"Similar labeled transactions (top {len(sims)}):")
    print("-" * 100)

    for sim_txn, score in sims:
        cat_str = ", ".join(sorted(sim_txn.category))
        sim_amt = float(sim_txn.amount) if sim_txn.amount else 0.0
        print(f"  {score:.2f} | {sim_amt:>10.2f} | {cat_str:<25} | {sim_txn.description}")


def register(subparsers):
    """Register lookalike command."""
    parser = subparsers.add_parser("lookalike", help="Find similar labeled txns for reference")
    parser.add_argument("--fy", type=int, required=True, help="Fiscal year (e.g., 24)")
    parser.add_argument("--index", type=int, required=True, help="Transaction index to analyze")
    parser.add_argument("--person", help="Person name (optional, all if omitted)")
    parser.add_argument(
        "--limit", type=int, default=10, help="Max similar txns to show (default: 10)"
    )
    parser.add_argument("--base-dir", default=".", help="Base directory (default: .)")
    parser.set_defaults(func=handle)
