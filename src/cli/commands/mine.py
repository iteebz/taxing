from pathlib import Path

from src.core.mining import mine_suggestions, score_suggestions, MiningConfig
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
    """Mine rule suggestions from labeled/unlabeled transactions."""
    base_dir = Path(args.base_dir or ".")
    fy = args.fy
    person = args.person
    use_search = args.search
    threshold = args.threshold
    dominance = args.dominance
    limit = args.limit

    txns = _load_txns(base_dir, fy, person)

    if not txns:
        print(f"\nNo transactions found for FY{fy}")
        return

    labeled = [t for t in txns if t.category]
    unlabeled = [t for t in txns if not t.category]

    if not labeled or not unlabeled:
        print(f"\nNeed both labeled and unlabeled transactions to mine rules")
        return

    print(f"\nMining Rules - FY{fy}")
    print("-" * 70)
    print(f"Labeled: {len(labeled)}")
    print(f"Unlabeled: {len(unlabeled)}")

    # Mine suggestions
    cache_path = base_dir / ".search_cache.json" if use_search else None
    suggestions = mine_suggestions(txns, use_search=use_search, cache_path=cache_path)

    if not suggestions:
        print(f"No suggestions found")
        return

    # Score suggestions
    cfg = MiningConfig(threshold=threshold, dominance=dominance)
    scored = score_suggestions(suggestions, cfg)

    if not scored:
        print(f"No suggestions passed threshold (threshold={threshold}, dominance={dominance:.1f})")
        return

    # Display top suggestions
    print(f"\nTop {len(scored[:limit])} Rules (threshold={threshold}, dominance={dominance:.1f})")
    print("-" * 70)
    for s in scored[:limit]:
        print(f"{s.keyword:<20} → {s.category:<18} | evidence={s.evidence:>3} | {s.source}")


def register(subparsers):
    """Register mine command."""
    parser = subparsers.add_parser("mine", help="Mine rule suggestions from transactions")
    parser.add_argument("--fy", type=int, required=True, help="Fiscal year (e.g., 25)")
    parser.add_argument("--person", help="Person name (optional, all if omitted)")
    parser.add_argument("--search", action="store_true", help="Enable merchant search via DDGS")
    parser.add_argument("--threshold", type=int, default=10, help="Minimum evidence threshold (default: 10)")
    parser.add_argument("--dominance", type=float, default=0.6, help="Dominance threshold 0.0-1.0 (default: 0.6)")
    parser.add_argument("--limit", type=int, default=20, help="Max suggestions to show (default: 20)")
    parser.add_argument("--base-dir", default=".", help="Base directory (default: .)")
    parser.set_defaults(func=handle)
