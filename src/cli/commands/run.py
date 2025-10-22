from pathlib import Path

from src.pipeline import run


def handle(args):
    """Run full pipeline: ingest → classify → deduce → persist."""
    base_dir = Path(args.base_dir or ".")
    fy = args.fy

    result = run(base_dir, fy)

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


def register(subparsers):
    """Register run command."""
    parser = subparsers.add_parser("run", help="Run full tax pipeline")
    parser.add_argument("--fy", type=int, required=True, help="Fiscal year (e.g., 25)")
    parser.add_argument("--base-dir", default=".", help="Base directory (default: .)")
    parser.set_defaults(func=handle)
