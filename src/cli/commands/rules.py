import json
from pathlib import Path

from src.core.mining import MiningConfig, mine_suggestions, score_suggestions
from src.core.models import Transaction
from src.io.persist import from_csv
from src.lib.sanitize import sanitize


def _load_classified_txns(base_dir: Path, fy: int | None = None) -> list[Transaction]:
    """Load classified transactions from output CSVs.

    If fy is None, loads all FY dirs.
    """
    data_dir = base_dir / "data"
    if not data_dir.exists():
        return []

    txns = []

    if fy is not None:
        fy_dirs = [data_dir / f"fy{fy}"]
    else:
        fy_dirs = sorted(d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith("fy"))

    for fy_dir in fy_dirs:
        if not fy_dir.exists():
            continue
        for person_dir in fy_dir.iterdir():
            if not person_dir.is_dir():
                continue
            csv_path = person_dir / "data" / "transactions.csv"
            if csv_path.exists():
                txns.extend(from_csv(csv_path, Transaction))

    return txns


def handle_suggest(args):
    """Mine high-confidence rule suggestions from classified transactions."""
    base_dir = Path(args.base_dir or ".")
    fy = args.fy
    json_output = args.json
    use_search = args.use_search

    config = MiningConfig(
        dominance=args.dominance or 0.6,
        threshold=args.threshold or 10,
    )

    all_txns = _load_classified_txns(base_dir, fy)
    if not all_txns:
        fy_str = f"FY{fy}" if fy else "any fiscal year"
        print(f"No classified transactions found in {fy_str}")
        return

    cache_path = base_dir / "data" / f"fy{fy}" / "search_cache.json" if fy and use_search else None
    if use_search and not fy:
        cache_path = base_dir / "data" / "search_cache.json"

    suggestions = mine_suggestions(all_txns, use_search=use_search, cache_path=cache_path)
    if not suggestions:
        print("No suggestions found.")
        return

    scored = score_suggestions(suggestions, config)
    if not scored:
        print(
            f"No suggestions met threshold (threshold={config.threshold}, "
            f"dominance={config.dominance:.0%})."
        )
        return

    fy_label = f"FY{fy}" if fy else "All FYs"
    search_label = " (with search)" if use_search else ""

    if json_output:
        data = [
            {
                "keyword": s.keyword,
                "category": s.category,
                "evidence": s.evidence,
                "source": s.source,
            }
            for s in scored
        ]
        print(json.dumps(data, indent=2))
    else:
        print(f"\nRule Suggestions - {fy_label}{search_label}")
        print("-" * 80)
        print(f"{'Keyword':<30} {'Category':<20} {'Evidence':<10} {'Source':<10}")
        print("-" * 80)
        for s in scored:
            print(f"{s.keyword:<30} {s.category:<20} {s.evidence:<10} {s.source:<10}")
        print()
        print(
            f"Total: {len(scored)} suggestions (threshold={config.threshold}, dominance={config.dominance:.0%})"
        )
        print("\nUsage: tax rules add --category CATEGORY --keyword KEYWORD")


def handle_add(args):
    """Add a new classification rule to rules/<category>.txt."""
    category = args.category
    keyword = args.keyword

    rule_file = Path("rules") / f"{category}.txt"

    if not rule_file.exists():
        print(f"Error: Category file not found: {rule_file}")
        available = sorted(p.stem for p in Path("rules").glob("*.txt"))
        print(f"Available categories: {', '.join(available)}")
        return

    with open(rule_file) as f:
        existing = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    if keyword in existing:
        print(f"✓ Rule already exists: {keyword} -> {category}")
        return

    existing.append(keyword)

    with open(rule_file, "w") as f:
        for rule in existing:
            f.write(f"{rule}\n")

    print(f"✓ Added rule: {keyword} -> {category}")
    handle_clean(quiet=True)


def handle_clean(args=None, quiet=False):
    """Remove duplicates, strip comments, sort alphabetically. All rule files."""
    rules_dir = Path("rules")

    if not rules_dir.exists():
        if not quiet:
            print("Error: rules/ directory not found")
        return

    cleaned_count = 0
    for rule_file in sorted(rules_dir.glob("*.txt")):
        with open(rule_file) as f:
            lines = [line.rstrip() for line in f]

        deduplicated = []
        seen = set()
        for line in lines:
            if line and not line.startswith("#"):
                keyword = sanitize(line)
                if keyword and keyword not in seen:
                    deduplicated.append(keyword)
                    seen.add(keyword)

        deduplicated.sort()

        if deduplicated != [sanitize(l) for l in lines if l and not l.startswith("#")]:
            with open(rule_file, "w") as f:
                for kw in deduplicated:
                    f.write(f"{kw}\n")
            cleaned_count += 1

    if not quiet:
        print(f"✓ Cleaned {cleaned_count} rule files (deduped, stripped comments, sorted)")


def register(subparsers):
    """Register rules subcommands."""
    parser = subparsers.add_parser("rules", help="Manage classification rules")
    rules_subparsers = parser.add_subparsers(dest="rules_command")

    suggest_parser = rules_subparsers.add_parser("suggest", help="Mine rule suggestions")
    suggest_parser.add_argument(
        "--fy", type=int, default=None, help="Fiscal year (e.g., 25). If omitted, uses all FY dirs"
    )
    suggest_parser.add_argument("--base-dir", default=".", help="Base directory (default: .)")
    suggest_parser.add_argument("--json", action="store_true", help="Output JSON")
    suggest_parser.add_argument(
        "--dominance",
        type=float,
        default=0.6,
        help="Category dominance threshold 0.0-1.0 (default: 0.6)",
    )
    suggest_parser.add_argument(
        "--threshold",
        type=int,
        default=10,
        help="Minimum occurrence count (default: 10)",
    )
    suggest_parser.add_argument(
        "--use-search",
        action="store_true",
        help="Enable DDGS merchant search for unclassified txns (caches results)",
    )
    suggest_parser.set_defaults(func=handle_suggest)

    add_parser = rules_subparsers.add_parser("add", help="Add classification rule")
    add_parser.add_argument("--category", required=True, help="Category name (e.g., groceries)")
    add_parser.add_argument("--keyword", required=True, help="Keyword/phrase to match")
    add_parser.set_defaults(func=handle_add)

    clean_parser = rules_subparsers.add_parser("clean", help="Remove duplicates & inline comments")
    clean_parser.set_defaults(func=handle_clean)
