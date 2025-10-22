from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from src.core import classify, deduce, load_rules, process_trades
from src.core.dedupe import dedupe
from src.core.models import Summary
from src.core.transfers import is_transfer, reconcile_transfers
from src.core.validate import validate_transactions
from src.io import (
    ingest_trades_year,
    ingest_year,
    to_csv,
    weights_from_csv,
)


def run(
    base_dir: str | Path,
    year: int,
    persons: list[str] | None = None,
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

    txns_all = dedupe(txns_all)

    rules = load_rules(base)

    weights_path = base / "data" / f"fy{year}" / "weights.csv"
    weights_from_csv(weights_path) if weights_path.exists() else {}

    if not txns_all:
        return {}

    results = {}
    txns_classified_all = []

    for individual in sorted({t.individual for t in txns_all}):
        txns_individual = [t for t in txns_all if t.individual == individual]
        trades_individual = [t for t in trades_all if t.individual == individual]

        txns_classified = [
            replace(
                t,
                category=(cat := classify(t.description, rules)),
                is_transfer=is_transfer(replace(t, category=cat)),
            )
            for t in txns_individual
        ]
        txns_classified_all.extend(txns_classified)

        validate_transactions(txns_classified, year)

        deductions = deduce(txns_classified, fy=year, business_percentages={})

        summary_dict = {}
        for t in txns_classified:
            if t.category and not t.is_transfer and t.amount is not None and not t.amount.is_nan():
                for cat in t.category:
                    if cat not in summary_dict:
                        summary_dict[cat] = (Decimal(0), Decimal(0))
                    credit, debit = summary_dict[cat]
                    amt = t.amount
                    if amt > 0:
                        summary_dict[cat] = (credit + amt, debit)
                    else:
                        summary_dict[cat] = (credit, debit + abs(amt))
        summary = [Summary(cat, credit, debit) for cat, (credit, debit) in summary_dict.items()]

        gains = process_trades(trades_individual)

        data_dir = base / "data" / f"fy{year}" / individual / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        to_csv(txns_classified, data_dir / "transactions.csv")
        to_csv(deductions, data_dir / "deductions.csv")
        to_csv(summary, data_dir / "summary.csv")
        to_csv(gains, data_dir / "gains.csv")

        results[individual] = {
            "txn_count": len(txns_individual),
            "classified_count": sum(1 for t in txns_classified if t.category),
            "deductions": deductions,
            "gains_count": len(gains),
        }

    transfers = reconcile_transfers(txns_classified_all)

    if transfers:
        transfer_list = list(transfers.values())
        transfers_path = base / "data" / f"fy{year}" / "transfers.csv"
        to_csv(transfer_list, transfers_path)

    results["_transfers"] = transfers

    return results
