from pathlib import Path

from src.core.mining import mine_suggestions, score_suggestions
from src.io.ingest import ingest_year


def handle(args):
    """Suggest new classification rules from unlabeled transactions."""
    base_dir = Path(args.base_dir or ".")
    fy = args.fy
    person = args.person

    txns = ingest_year(base_dir, fy, persons=[person])

    if not txns:
        print(f"\nNo transactions found for {person} FY{fy}")
        return

    unlabeled = [t for t in txns if t.category is None or not t.category]
    if not unlabeled:
        print("\n✓ All transactions categorized!")
        return

    print(f"\n📊 Analyzing {len(unlabeled)} unlabeled transactions...")

    suggestions = mine_suggestions(txns)
    scored = score_suggestions(suggestions)

    if not scored:
        print("No suggestions found.")
        return

    print("\n✅ Suggested Rules (by evidence)\n")
    print(f"{'Keyword':<20} {'Category':<20} {'Evidence':<10}")
    print("-" * 50)

    for sug in scored:
        print(f"{sug.keyword:<20} {sug.category:<20} {sug.evidence:<10}")

    print("\n" + "=" * 50)
    print("To add these rules:")
    print("  taxing add-rule --category <cat> --keyword <kw>")
    print("Or manually edit: rules/<category>.txt")
    print("=" * 50)


def register(subparsers):
    """Register suggest-rules command."""
    parser = subparsers.add_parser("suggest-rules", help="Suggest classification rules")
    parser.add_argument("--fy", type=int, required=True, help="Fiscal year (e.g., 25)")
    parser.add_argument("--person", required=True, help="Person name")
    parser.add_argument("--base-dir", default=".", help="Base directory (default: .)")
    parser.set_defaults(func=handle)
