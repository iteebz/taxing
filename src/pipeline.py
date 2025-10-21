from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from src.core import classify, deduce, load_rules, process_trades
from src.core.models import AUD, Money
from src.io import (
    deductions_to_csv,
    gains_to_csv,
    ingest_trades_year,
    ingest_year,
    summary_to_csv,
    txns_to_csv,
    weights_from_csv,
)


def run(
    base_dir: str | Path, year: int, persons: list[str] | None = None
) -> dict[str, dict[str, object]]:
    """Execute full pipeline: ingest → classify → deduce → trades → persist.

    Uses standardized directory structure: {base_dir}/data/fy{year}/{person}/

    Args:
        base_dir: Root directory
        year: Fiscal year (e.g., 25 for FY2025)
        persons: List of persons to process (if None, auto-detect)

    Returns:
        Dict mapping person -> {txn_count, classified_count, deductions, gains_count}
    """
    base = Path(base_dir)

    txns_all = ingest_year(base, year, persons=persons)
    trades_all = ingest_trades_year(base, year, persons=persons)

    rules = load_rules(base)

    weights_path = base / "weights.csv"
    weights = weights_from_csv(weights_path) if weights_path.exists() else {}

    if not txns_all:
        return {}

    results = {}
    for person in sorted({t.source_person for t in txns_all}):
        txns_person = [t for t in txns_all if t.source_person == person]
        trades_person = [t for t in trades_all if t.source_person == person]

        txns_classified = [replace(t, category=classify(t.description, rules)) for t in txns_person]

        deductions = deduce(txns_classified, weights)

        summary = {}
        for t in txns_classified:
            if t.category and not t.is_transfer and t.amount.currency == AUD:
                for cat in t.category:
                    if cat not in summary:
                        summary[cat] = Money(Decimal(0), AUD)
                    summary[cat] = Money(summary[cat].amount + t.amount.amount, AUD)

        gains = process_trades(trades_person)

        data_dir = base / "data" / f"fy{year}" / person / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        txns_to_csv(txns_classified, data_dir / "transactions.csv")
        deductions_to_csv(deductions, data_dir / "deductions.csv")
        summary_to_csv(summary, data_dir / "summary.csv")
        gains_to_csv(gains, data_dir / "gains.csv")

        results[person] = {
            "txn_count": len(txns_person),
            "classified_count": sum(1 for t in txns_classified if t.category),
            "deductions": deductions,
            "gains_count": len(gains),
        }

    return results
