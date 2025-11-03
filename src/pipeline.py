from dataclasses import replace
from pathlib import Path

from src.core import classify, deduce, load_rules, process_trades
from src.core.dedupe import dedupe
from src.core.models import Summary
from src.core.transfers import is_transfer
from src.core.validate import validate_transactions
from src.io import (
    ingest_all_trades,
    ingest_all_years,
    to_csv,
    weights_from_csv,
)


def run(
    base_dir: str | Path,
    persons: list[str] | None = None,
) -> dict[str, dict[str, object]]:
    """Execute full pipeline: ingest all years → classify → deduce → trades → persist.

    Loads all transactions and trades from all fiscal years, classifies universe-wide,
    then splits output by year/person for persistence.

    Args:
        base_dir: Root directory
        persons: List of persons to process (if None, auto-detect)

    Returns:
        Dict mapping person -> {txn_count, classified_count, deductions, gains_count}
    """
    base = Path(base_dir)

    txns_all = ingest_all_years(base, persons=persons)
    trades_all = ingest_all_trades(base, persons=persons)
    txns_all = dedupe(txns_all)
    rules = load_rules(base)

    if not txns_all:
        return {}

    txns_classified = [
        replace(
            t,
            cats=(cat := classify(t.description, rules)),
            is_transfer=is_transfer(replace(t, cats=cat)),
        )
        for t in txns_all
    ]

    results = {}

    for individual in sorted({t.individual for t in txns_classified}):
        txns_ind = [t for t in txns_classified if t.individual == individual]
        trades_ind = [t for t in trades_all if t.individual == individual]

        fy_groups = {}
        for txn in txns_ind:
            year = txn.date.year
            month = txn.date.month
            fy = year if month < 7 else year + 1
            if fy not in fy_groups:
                fy_groups[fy] = []
            fy_groups[fy].append(txn)

        all_deductions = []
        for fy, txns_fy in sorted(fy_groups.items()):
            validate_transactions(txns_fy, fy)

            weights_path = base / "data" / f"fy{fy}" / individual / "data" / "weights.csv"
            deductions = deduce(
                txns_fy,
                fy=fy,
                individual=individual,
                business_percentages={},
                weights_path=weights_path,
            )
            all_deductions.extend(deductions)

            summary = Summary.from_transactions(txns_fy)
            gains = process_trades([t for t in trades_ind if t.date.year == fy])

            data_dir = base / "data" / f"fy{fy}" / individual / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            to_csv(txns_fy, data_dir / "transactions.csv")
            to_csv(deductions, data_dir / "deductions.csv")
            to_csv(summary, data_dir / "summary.csv")
            to_csv(gains, data_dir / "gains.csv")

        results[individual] = {
            "txn_count": len(txns_ind),
            "classified_count": sum(1 for t in txns_ind if t.cats),
            "deductions": all_deductions,
            "gains_count": len(trades_ind),
        }

    return results
