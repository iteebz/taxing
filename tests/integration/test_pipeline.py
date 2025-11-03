from pathlib import Path

import pytest

from src.lib.paths import (
    data_raw_fy_person,
    deductions_csv,
    gains_csv,
    trades_csv,
    transactions_csv,
)
from src.pipeline import run


@pytest.mark.skip(reason="Trades ingestion needs investigation")
def test_pipeline_full_flow(tmp_path):
    tyson_dir = data_raw_fy_person(tmp_path, 25, "tyson")
    janice_dir = data_raw_fy_person(tmp_path, 25, "janice")

    tyson_raw = tyson_dir / "raw"
    janice_raw = janice_dir / "raw"
    tyson_raw.mkdir(parents=True)
    janice_raw.mkdir(parents=True)

    rules_dir = Path(tmp_path) / "rules"
    rules_dir.mkdir()
    (rules_dir / "groceries.txt").write_text("COLES\nWOOLWORTHS")
    (rules_dir / "transport.txt").write_text("UBER")
    (rules_dir / "uncategorized.txt").write_text("RANDOM")

    tyson_cba = tyson_raw / "cba.csv"
    tyson_cba.write_text(
        "15/11/2024,50.00,COLES CHECKOUT,5000.00\n16/11/2024,30.00,UBER TRIP,4970.00\n"
    )

    janice_cba = janice_raw / "cba.csv"
    janice_cba.write_text("20/11/2024,100.00,RANDOM SHOP,9900.00\n")

    tyson_trades_file = tyson_raw / "trades.csv"
    tyson_trades_file.write_text(
        "date,code,action,units,price,fee\n"
        "2023-01-01,ASX:BHP,buy,100.0,10.00,10.0\n"
        "2024-08-01,ASX:BHP,sell,50.0,20.00,10.0\n"
    )

    janice_trades_file = janice_raw / "trades.csv"
    janice_trades_file.write_text("date,code,action,units,price,fee\n")

    weights_csv = Path(tmp_path) / "weights.csv"
    weights_csv.write_text("category,weight\ngroceries,0.5\ntransport,0.8\n")

    result = run(tmp_path)

    assert "tyson" in result
    assert "janice" in result

    assert result["tyson"]["txn_count"] == 2
    assert result["tyson"]["classified_count"] == 2
    assert result["tyson"]["gains_count"] == 1

    assert result["janice"]["txn_count"] == 1
    assert result["janice"]["classified_count"] == 1
    assert result["janice"]["gains_count"] == 0

    assert transactions_csv(tmp_path).exists()
    assert deductions_csv(tmp_path).exists()
    assert trades_csv(tmp_path).exists()
    assert gains_csv(tmp_path).exists()
