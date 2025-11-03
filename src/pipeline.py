from dataclasses import replace
from pathlib import Path

from src.core import audit, calculate_gains, classify, deduce, dedupe, load_rules, validate
from src.core.transfers import is_transfer
from src.io import (
    ingest_all_trades,
    ingest_all_years,
    to_csv,
)
from src.lib.paths import data_root, deductions_csv, gains_csv, trades_csv, transactions_csv


def run(
    base_dir: str | Path,
    persons: list[str] | None = None,
) -> dict[str, dict[str, object]]:
    """Execute full pipeline: ingest all years → classify → deduce → trades → persist.

    Loads all transactions and trades from all fiscal years, classifies universe-wide,
    then persists to unified CSVs in data/.

    Args:
        base_dir: Root directory
        persons: List of persons to process (if None, auto-detect)

    Returns:
        Dict mapping person -> {txn_count, classified_count, deductions, gains_count}
    """
    base = Path(base_dir)
    data_dir = data_root(base_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

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

    all_deductions = []
    all_gains = []
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

        individual_deductions = []
        for fy, txns_fy in sorted(fy_groups.items()):
            validate(txns_fy, fy)

            weights_path = base / "weights.csv"
            deductions = deduce(
                txns_fy,
                fy=fy,
                individual=individual,
                business_percentages={},
                weights_path=weights_path,
            )
            individual_deductions.extend(deductions)
            all_deductions.extend(deductions)

        individual_gains = calculate_gains(trades_ind)
        all_gains.extend(individual_gains)

        results[individual] = {
            "txn_count": len(txns_ind),
            "classified_count": sum(1 for t in txns_ind if t.cats),
            "deductions": individual_deductions,
            "gains_count": len(individual_gains),
        }

    to_csv(txns_classified, transactions_csv(base_dir))
    to_csv(all_deductions, deductions_csv(base_dir))
    to_csv(trades_all, trades_csv(base_dir))
    to_csv(all_gains, gains_csv(base_dir))

    audit_alerts = audit(all_deductions)
    if audit_alerts:
        results["_audit_alerts"] = audit_alerts

    return results
