from pathlib import Path

from src.lib.sanitize import sanitize


def dedupe_keywords(keywords: list[str]) -> list[str]:
    """Remove subsumed keywords and duplicates.

    Args:
        keywords: List of keywords (case-insensitive)

    Returns:
        Deduplicated list, alphabetically sorted, with subsumed keywords removed
    """
    if not keywords:
        return []

    normalized = sorted({k.strip().upper() for k in keywords})

    filtered = []
    for kw in normalized:
        if not any(kw != other and other in kw for other in normalized):
            filtered.append(kw)

    return sorted(filtered)


def load_rules(base_dir: str | Path) -> dict[str, list[str]]:
    """Load rules from .txt files in base_dir/rules/.

    Args:
        base_dir: Root directory containing rules/ subdirectory

    Returns:
        Dict mapping category (filename without .txt) -> list of deduplicated keywords
    """
    base = Path(base_dir)
    rules_dir = base / "rules"

    if not rules_dir.exists():
        return {}

    rules = {}
    for rule_file in sorted(rules_dir.glob("*.txt")):
        category = rule_file.stem
        keywords = []

        with open(rule_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    keyword = sanitize(line)
                    if keyword:
                        keywords.append(keyword)

        if keywords:
            rules[category] = dedupe_keywords(keywords)

    return rules
