from pathlib import Path

from src.core.mining import MiningConfig, mine_suggestions, score_suggestions
from src.core.models import Transaction
from src.io.ingest import ingest_year
from src.io.persist import from_csv
from src.lib.search import load_cache, search_description


def _get_available_fys(base_dir: Path) -> list[int]:
    """Get all available FY directories, sorted descending."""
    data_dir = base_dir / "data"
    if not data_dir.exists():
        return []
    fys = []
    for d in data_dir.iterdir():
        if d.is_dir() and d.name.startswith("fy"):
            try:
                fy = int(d.name[2:])
                fys.append(fy)
            except ValueError:
                pass
    return sorted(fys, reverse=True)


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
    fys = [args.fy] if args.fy else _get_available_fys(base_dir)
    person = args.person
    use_search = args.search
    show_unlabeled = args.show_unlabeled
    threshold = args.threshold
    dominance = args.dominance
    limit = args.limit

    if not fys:
        print("\nNo FY data found. Provide --fy or ensure data/ directory exists.")
        return

    cache_path = base_dir / ".search_cache.json" if use_search else None

    for fy in fys:
        txns = _load_txns(base_dir, fy, person)

        if not txns:
            print(f"\nNo transactions found for FY{fy}")
            continue

        labeled = [t for t in txns if t.category]
        unlabeled = [t for t in txns if not t.category]

        if show_unlabeled:
            print(f"\nUnlabeled Transactions - FY{fy}")
            print("-" * 100)
            cache = load_cache(cache_path) if use_search else {}
            for i, txn in enumerate(unlabeled[:limit], 1):
                print(f"\n{i}. {txn.description}")
                print(f"   Date: {txn.date} | Amount: {txn.amount}")
                if use_search:
                    results = search_description(txn.description, cache, cache_path, max_results=2)
                    for j, result in enumerate(results, 1):
                        if isinstance(result, dict):
                            print(f"   {j}. {result.get('title', '')}")
                            print(f"      {result.get('body', '')[:80]}")
                        else:
                            print(f"   {j}. {str(result)[:80]}")
            continue

        if not labeled or not unlabeled:
            print(f"\nFY{fy}: Need both labeled and unlabeled transactions to mine rules")
            continue

        print(f"\nMining Rules - FY{fy}")
        print("-" * 70)
        print(f"Labeled: {len(labeled)}")
        print(f"Unlabeled: {len(unlabeled)}")

        # Mine suggestions
        suggestions = mine_suggestions(txns, use_search=use_search, cache_path=cache_path)

        if not suggestions:
            print("No suggestions found")
            continue

        # Score suggestions
        cfg = MiningConfig(threshold=threshold, dominance=dominance)
        scored = score_suggestions(suggestions, cfg)

        if not scored:
            print(
                f"No suggestions passed threshold (threshold={threshold}, dominance={dominance:.1f})"
            )
            continue

        # Display top suggestions
        print(
            f"\nTop {len(scored[:limit])} Rules (threshold={threshold}, dominance={dominance:.1f})"
        )
        print("-" * 70)
        for s in scored[:limit]:
            print(f"{s.keyword:<20} → {s.category:<18} | evidence={s.evidence:>3} | {s.source}")


def register(subparsers):
    """Register mine command."""
    parser = subparsers.add_parser("mine", help="Mine rule suggestions from transactions")
    parser.add_argument(
        "--fy", type=int, default=None, help="Fiscal year (e.g., 25), omit to process all"
    )
    parser.add_argument("--person", help="Person name (optional, all if omitted)")
    parser.add_argument("--search", action="store_true", help="Enable search for categorization hints")
    parser.add_argument("--show-unlabeled", action="store_true", help="Show unlabeled txns + search results")
    parser.add_argument(
        "--threshold", type=int, default=10, help="Minimum evidence threshold (default: 10)"
    )
    parser.add_argument(
        "--dominance", type=float, default=0.6, help="Dominance threshold 0.0-1.0 (default: 0.6)"
    )
    parser.add_argument(
        "--limit", type=int, default=20, help="Max suggestions to show (default: 20)"
    )
    parser.add_argument("--base-dir", default=".", help="Base directory (default: .)")
    parser.set_defaults(func=handle)
