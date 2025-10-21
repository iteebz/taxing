from pathlib import Path

from src.pipeline import run


def test_pipeline_full_flow(tmp_path):
    tyson_raw = Path(tmp_path) / "data" / "fy25" / "tyson" / "raw"
    janice_raw = Path(tmp_path) / "data" / "fy25" / "janice" / "raw"
    tyson_raw.mkdir(parents=True)
    janice_raw.mkdir(parents=True)

    rules_dir = Path(tmp_path) / "rules"
    rules_dir.mkdir()
    (rules_dir / "groceries.txt").write_text("COLES\nWOOLWORTHS")
    (rules_dir / "transport.txt").write_text("UBER")

    tyson_cba = tyson_raw / "cba.csv"
    tyson_cba.write_text(
        "01/01/2025,50.00,COLES CHECKOUT,5000.00\n02/01/2025,30.00,UBER TRIP,4970.00\n"
    )

    janice_cba = janice_raw / "cba.csv"
    janice_cba.write_text("03/01/2025,100.00,RANDOM SHOP,9900.00\n")

    tyson_trades = Path(tmp_path) / "data" / "fy25" / "tyson" / "trades.csv"
    tyson_trades.write_text(
        "date,code,action,units,price,fee\n"
        "2023-01-01,ASX:BHP,buy,100.0,10.00,10.0\n"
        "2024-08-01,ASX:BHP,sell,50.0,20.00,10.0\n"
    )

    janice_trades = Path(tmp_path) / "data" / "fy25" / "janice" / "trades.csv"
    janice_trades.write_text("date,code,action,units,price,fee\n")

    weights_csv = Path(tmp_path) / "weights.csv"
    weights_csv.write_text("category,weight\ngroceries,0.5\ntransport,0.8\n")

    result = run(tmp_path, 25)

    assert len(result) == 2
    assert "tyson" in result
    assert "janice" in result

    assert result["tyson"]["txn_count"] == 2
    assert result["tyson"]["classified_count"] == 2
    assert result["tyson"]["gains_count"] == 1

    assert result["janice"]["txn_count"] == 1
    assert result["janice"]["classified_count"] == 0
    assert result["janice"]["gains_count"] == 0

    tyson_data = Path(tmp_path) / "data" / "fy25" / "tyson" / "data"
    assert (tyson_data / "transactions.csv").exists()
    assert (tyson_data / "deductions.csv").exists()
    assert (tyson_data / "summary.csv").exists()
    assert (tyson_data / "gains.csv").exists()

    janice_data = Path(tmp_path) / "data" / "fy25" / "janice" / "data"
    assert (janice_data / "transactions.csv").exists()
    assert (janice_data / "deductions.csv").exists()
    assert (janice_data / "summary.csv").exists()
    assert (janice_data / "gains.csv").exists()
