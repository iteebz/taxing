from pathlib import Path

from src.pipeline import run


def test_pipeline_full_flow(tmp_path):
    raw_dir = Path(tmp_path) / "fy25" / "raw"
    raw_dir.mkdir(parents=True)

    rules_dir = Path(tmp_path) / "rules"
    rules_dir.mkdir()
    (rules_dir / "groceries.txt").write_text("COLES\nWOOLWORTHS")
    (rules_dir / "transport.txt").write_text("UBER")

    cba_csv = raw_dir / "cba.csv"
    cba_csv.write_text(
        "date_raw,amount,description_raw,balance,source_person\n"
        "01/01/2025,50.00,COLES CHECKOUT,5000.00,tyson\n"
        "02/01/2025,30.00,UBER TRIP,4970.00,tyson\n"
        "03/01/2025,100.00,RANDOM SHOP,9900.00,janice\n"
    )

    weights_csv = Path(tmp_path) / "weights.csv"
    weights_csv.write_text("category,weight\ngroceries,0.5\ntransport,0.8\n")

    result = run(tmp_path, "fy25")

    assert len(result) == 2
    assert "tyson" in result
    assert "janice" in result

    assert result["tyson"]["txn_count"] == 2
    assert result["tyson"]["classified_count"] == 2

    assert result["janice"]["txn_count"] == 1
    assert result["janice"]["classified_count"] == 0

    tyson_data = Path(tmp_path) / "fy25" / "tyson" / "data"
    assert (tyson_data / "transactions.csv").exists()
    assert (tyson_data / "deductions.csv").exists()

    janice_data = Path(tmp_path) / "fy25" / "janice" / "data"
    assert (janice_data / "transactions.csv").exists()
    assert (janice_data / "deductions.csv").exists()
