from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from src.core import classify, deduce, load_rules, process_trades
from src.core.models import AUD, Money
from src.io import (
    deductions_to_csv,
    gains_to_csv,
    ingest_dir,
    ingest_trades_dir,
    summary_to_csv,
    txns_to_csv,
    weights_from_csv,
)


def run(base_dir: str | Path, fiscal_year: str) -> dict[str, dict[str, object]]:
    """Execute full pipeline: ingest → classify → deduce → trades → persist (all persons).

    Args:
        base_dir: Root directory (contains rules/, fy*/{person}/{raw,data}/, weights.csv)
        fiscal_year: Financial year (e.g., 'fy25')

    Returns:
        Dict mapping person -> {txn_count, classified_count, deductions, gains}
    """
    base = Path(base_dir)
    raw_dir = base / fiscal_year / "raw"

    txns_all = ingest_dir(raw_dir)
    trades_all = ingest_trades_dir(base / fiscal_year)

    rules = load_rules(base)

    weights_path = base / "weights.csv"
    weights = weights_from_csv(weights_path) if weights_path.exists() else {}

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

        data_dir = base / fiscal_year / person / "data"
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
