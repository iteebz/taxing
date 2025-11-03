from pathlib import Path

import typer

from src.pipeline import run as run_pipeline


def handle(
    fy: int = typer.Option(..., "--fy", help="Fiscal year (e.g., 25)"),
    base_dir: str = typer.Option(".", "--base-dir", help="Base directory"),
):
    """Run full tax pipeline (ingest → classify → deduce → trades → persist)."""
    base_dir = Path(base_dir or ".")
    result = run_pipeline(base_dir, fy)

    print(f"\nPipeline Results - FY{fy}")
    print("-" * 70)

    for person in sorted([k for k in result if k != "_transfers"]):
        data = result[person]
        print(
            f"{person:<20} txns={data['txn_count']:<5} "
            f"classified={data['classified_count']:<5} "
            f"deductions={len(data['deductions']):<5} "
            f"gains={data['gains_count']}"
        )

    if "_transfers" in result:
        transfers = result["_transfers"]
        print(f"\nTransfers reconciled: {len(transfers)} total")

    print("-" * 70)
