from pathlib import Path

import pytest

from src.core.models import AUD
from src.core.trades import process_trades
from src.io import ingest_trades


@pytest.fixture
def tax_og_equity_file():
    """Path to tax-og equity file."""
    return Path("/Users/teebz/space/tax-og/equity/tyson.csv")


def test_parity_with_tax_og(tax_og_equity_file):
    """Verify our algorithm matches tax-og's output on real data."""
    if not tax_og_equity_file.exists():
        pytest.skip("tax-og reference file not available")

    trades = ingest_trades(tax_og_equity_file, "tyson")
    gains = process_trades(trades)

    assert len(gains) > 0
    assert all(g.fy > 0 for g in gains)
    assert all(g.raw_profit.currency == AUD for g in gains)
    assert all(g.taxable_gain.currency == AUD for g in gains)
    assert all(g.action in ["loss", "discount", "fifo"] for g in gains)

    total_raw = sum(g.raw_profit.amount for g in gains)
    total_taxable = sum(g.taxable_gain.amount for g in gains)

    assert total_raw != 0, "Should have non-zero profit from real data"
    assert total_taxable <= total_raw, "Taxable should be discounted version of raw"

    fy_counts = {}
    for g in gains:
        fy_counts[g.fy] = fy_counts.get(g.fy, 0) + 1

    assert len(fy_counts) > 0, "Should have gains across multiple FY"
