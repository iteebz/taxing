from pathlib import Path

import typer

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


def handle(
    fy: int = typer.Option(None, "--fy", help="Fiscal year (e.g., 25), omit to process all"),
    person: str = typer.Option(None, "--person", help="Person name (all if omitted)"),
    search: bool = typer.Option(False, "--search", help="Enable search for categorization hints"),
    show_unlabeled: bool = typer.Option(
        False, "--show-unlabeled", help="Show unlabeled txns + search results"
    ),
    threshold: int = typer.Option(10, "--threshold", help="Minimum evidence threshold"),
    dominance: float = typer.Option(0.6, "--dominance", help="Dominance threshold 0.0-1.0"),
    limit: int = typer.Option(20, "--limit", help="Max suggestions to show"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Mine rule suggestions from high-confidence keyword patterns."""
    base_dir = Path(base_dir or ".")
    fys = [fy] if fy else _get_available_fys(base_dir)

    if not fys:
        print("\nNo FY data found. Provide --fy or ensure data/ directory exists.")
        return

    cache_path = base_dir / ".search_cache.json" if search else None

    for fy_val in fys:
        txns = _load_txns(base_dir, fy_val, person)

        if not txns:
            print(f"\nNo transactions found for FY{fy_val}")
            continue

        labeled = [t for t in txns if t.cats]
        unlabeled = [t for t in txns if not t.cats]

        if show_unlabeled:
            print(f"\nUnlabeled Transactions - FY{fy_val}")
            print("-" * 100)
            cache = load_cache(cache_path) if search else {}
            for i, txn in enumerate(unlabeled[:limit], 1):
                print(f"\n{i}. {txn.description}")
                print(f"   Date: {txn.date} | Amount: {txn.amount}")
                if search:
                    results = search_description(txn.description, cache, cache_path, max_results=2)
                    for j, result in enumerate(results, 1):
                        if isinstance(result, dict):
                            print(f"   {j}. {result.get('title', '')}")
                            print(f"      {result.get('body', '')[:80]}")
                        else:
                            print(f"   {j}. {str(result)[:80]}")
            continue

        if not labeled or not unlabeled:
            print(f"\nFY{fy_val}: Need both labeled and unlabeled transactions to mine rules")
            continue

        print(f"\nMining Rules - FY{fy_val}")
        print("-" * 70)
        print(f"Labeled: {len(labeled)}")
        print(f"Unlabeled: {len(unlabeled)}")

        # Mine suggestions
        suggestions = mine_suggestions(txns, use_search=search, cache_path=cache_path)

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
