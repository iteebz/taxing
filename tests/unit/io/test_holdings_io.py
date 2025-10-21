"""Holdings I/O tests."""

from decimal import Decimal

from src.io.holdings import load_holdings


def test_load_holdings_complete(tmp_path):
    """Load multiple holdings from CSV."""
    holdings_csv = tmp_path / "holdings.csv"
    holdings_csv.write_text(
        "ticker,units,cost_basis,current_price\nASX:SYI,100,5000,60\nASX:VAS,50,2500,100\n"
    )

    holdings = load_holdings(tmp_path, "tyson")

    assert len(holdings) == 2
    assert holdings[0].ticker == "ASX:SYI"
    assert holdings[0].units == Decimal("100")
    assert holdings[1].ticker == "ASX:VAS"


def test_load_holdings_missing_file(tmp_path):
    """Missing holdings file returns empty list."""
    holdings = load_holdings(tmp_path, "tyson")
    assert holdings == []


def test_load_holdings_single_holding(tmp_path):
    """Load single holding."""
    holdings_csv = tmp_path / "holdings.csv"
    holdings_csv.write_text("ticker,units,cost_basis,current_price\nASX:VGS,200,10000,60\n")

    holdings = load_holdings(tmp_path, "janice")

    assert len(holdings) == 1
    assert holdings[0].ticker == "ASX:VGS"
    assert holdings[0].units == Decimal("200")


def test_load_holdings_decimal_precision(tmp_path):
    """Preserve decimal precision."""
    holdings_csv = tmp_path / "holdings.csv"
    holdings_csv.write_text(
        "ticker,units,cost_basis,current_price\nASX:VAS,123.456,12345.67,45.6789\n"
    )

    holdings = load_holdings(tmp_path, "luna")

    assert len(holdings) == 1
    assert holdings[0].units == Decimal("123.456")
    assert holdings[0].cost_basis.amount == Decimal("12345.67")
    assert holdings[0].current_price.amount == Decimal("45.6789")


def test_load_holdings_fractional_units(tmp_path):
    """Support fractional units."""
    holdings_csv = tmp_path / "holdings.csv"
    holdings_csv.write_text("ticker,units,cost_basis,current_price\nASX:VAS,0.5,50,120\n")

    holdings = load_holdings(tmp_path, "tyson")

    assert len(holdings) == 1
    assert holdings[0].units == Decimal("0.5")


def test_load_holdings_skip_invalid_row(tmp_path):
    """Skip rows that can't be parsed."""
    holdings_csv = tmp_path / "holdings.csv"
    holdings_csv.write_text(
        "ticker,units,cost_basis,current_price\nASX:SYI,100,5000,60\nbroken,bad,data,\n"
    )

    holdings = load_holdings(tmp_path, "tyson")

    assert len(holdings) == 1
    assert holdings[0].ticker == "ASX:SYI"


def test_load_holdings_skip_invalid_amounts(tmp_path):
    """Skip rows with invalid amounts."""
    holdings_csv = tmp_path / "holdings.csv"
    holdings_csv.write_text(
        "ticker,units,cost_basis,current_price\nASX:SYI,100,5000,60\nASX:VAS,invalid,2500,100\n"
    )

    holdings = load_holdings(tmp_path, "tyson")

    assert len(holdings) == 1
    assert holdings[0].ticker == "ASX:SYI"


def test_load_holdings_various_tickers(tmp_path):
    """Support various ticker formats."""
    holdings_csv = tmp_path / "holdings.csv"
    holdings_csv.write_text(
        "ticker,units,cost_basis,current_price\n"
        "ASX:SYI,100,5000,60\n"
        "VAS,50,2500,100\n"
        "TSLA,10,1500,150\n"
        "AAPL,5,1000,200\n"
    )

    holdings = load_holdings(tmp_path, "tyson")

    assert len(holdings) == 4
    assert holdings[0].ticker == "ASX:SYI"
    assert holdings[1].ticker == "VAS"
    assert holdings[2].ticker == "TSLA"
    assert holdings[3].ticker == "AAPL"
