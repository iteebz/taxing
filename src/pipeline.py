from dataclasses import replace
from pathlib import Path

from src.core import classify, deduce, load_rules
from src.io import (
    deductions_to_csv,
    ingest_dir,
    txns_to_csv,
    weights_from_csv,
)


def run(base_dir: str | Path, fiscal_year: str) -> dict[str, dict[str, object]]:
    """Execute full pipeline: ingest → classify → deduce → persist (all persons).

    Args:
        base_dir: Root directory (contains rules/, fy*/{person}/{raw,data}/, weights.csv)
        fiscal_year: Financial year (e.g., 'fy25')

    Returns:
        Dict mapping person -> {txn_count, classified_count, deductions}
    """
    base = Path(base_dir)
    raw_dir = base / fiscal_year / "raw"

    txns_all = ingest_dir(raw_dir)

    rules = load_rules(base)

    weights_path = base / "weights.csv"
    weights = weights_from_csv(weights_path) if weights_path.exists() else {}

    results = {}
    for person in sorted({t.source_person for t in txns_all}):
        txns_person = [t for t in txns_all if t.source_person == person]

        txns_classified = [
            replace(t, category=classify(t.description, rules)) for t in txns_person
        ]

        deductions = deduce(txns_classified, weights)

        data_dir = base / fiscal_year / person / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        txns_to_csv(txns_classified, data_dir / "transactions.csv")
        deductions_to_csv(deductions, data_dir / "deductions.csv")

        results[person] = {
            "txn_count": len(txns_person),
            "classified_count": sum(1 for t in txns_classified if t.category),
            "deductions": deductions,
        }

    return results
