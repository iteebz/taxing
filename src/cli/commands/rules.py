from pathlib import Path


def handle(args):
    """Add a new classification rule to rules/<category>.txt."""
    category = args.category
    keyword = args.keyword

    rule_file = Path("rules") / f"{category}.txt"

    if not rule_file.exists():
        print(f"\nError: Category file not found: {rule_file}")
        available = sorted(p.stem for p in Path("rules").glob("*.txt"))
        print(f"Available categories: {', '.join(available)}")
        return

    with open(rule_file) as f:
        existing = {
            line.strip() for line in f
            if line.strip() and not line.strip().startswith("#")
        }

    if keyword in existing:
        print(f"\n✓ Rule already exists: {keyword} -> {category}")
        return

    existing.add(keyword)
    sorted_rules = sorted(existing, key=str.lower)

    with open(rule_file, "w") as f:
        for rule in sorted_rules:
            f.write(f"{rule}\n")

    print(f"\n✓ Added rule: {keyword} -> {category}")
    print(f"  File: {rule_file}")


def register(subparsers):
    """Register add-rule command."""
    parser = subparsers.add_parser("add-rule", help="Add classification rule")
    parser.add_argument("--category", required=True, help="Category name (e.g., groceries)")
    parser.add_argument("--keyword", required=True, help="Keyword/phrase to match")
    parser.set_defaults(func=handle)
