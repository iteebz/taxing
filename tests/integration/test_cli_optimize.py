import json

import pytest

from src.cli.commands.optimize import handle as cmd_optimize


class Args:
    """Mock argparse Namespace for testing."""

    def __init__(self, fy, persons, base_dir="."):
        self.fy = fy
        self.persons = persons
        self.base_dir = base_dir


def test_optimize_tyson_janice_basic(tmp_path, capsys):
    """Optimize allocation for tyson and janice with shared deductions."""
    fy = 25
    fy_dir = tmp_path / "data" / f"fy{fy}"

    for person in ["tyson", "janice"]:
        data_dir = fy_dir / person / "data"
        data_dir.mkdir(parents=True)

        deductions_csv = data_dir / "deductions.csv"
        if person == "tyson":
            deductions_csv.write_text("category,amount\ninvestment,5000\n")
        else:
            deductions_csv.write_text("category,amount\ntravel,3000\n")

    employment_income_file = tmp_path / f"employment_income_fy{fy}.json"
    employment_income_file.write_text(json.dumps({"tyson": 150000, "janice": 50000}))

    args = Args(fy=fy, persons="tyson,janice", base_dir=str(tmp_path))
    cmd_optimize(args)

    captured = capsys.readouterr()
    assert "tyson" in captured.out
    assert "janice" in captured.out
    assert "TOTAL" in captured.out
    assert "$" in captured.out


def test_optimize_single_person(tmp_path, capsys):
    """Optimize with single person."""
    fy = 25
    fy_dir = tmp_path / "data" / f"fy{fy}"

    data_dir = fy_dir / "tyson" / "data"
    data_dir.mkdir(parents=True)

    deductions_csv = data_dir / "deductions.csv"
    deductions_csv.write_text("category,amount\ninvestment,10000\n")

    employment_income_file = tmp_path / f"employment_income_fy{fy}.json"
    employment_income_file.write_text(json.dumps({"tyson": 100000}))

    args = Args(fy=fy, persons="tyson", base_dir=str(tmp_path))
    cmd_optimize(args)

    captured = capsys.readouterr()
    assert "tyson" in captured.out
    assert "$10,000" in captured.out


def test_optimize_no_persons_error():
    """Error when --persons not provided."""
    args = Args(fy=25, persons="", base_dir=".")

    with pytest.raises(ValueError, match="--persons required"):
        cmd_optimize(args)


def test_optimize_missing_employment_income(tmp_path):
    """Error when employment income config missing."""
    fy = 25
    args = Args(fy=fy, persons="tyson", base_dir=str(tmp_path))

    with pytest.raises(FileNotFoundError, match="employment_income"):
        cmd_optimize(args)


def test_optimize_missing_person_income(tmp_path):
    """Error when person missing from employment income."""
    fy = 25
    employment_income_file = tmp_path / f"employment_income_fy{fy}.json"
    employment_income_file.write_text(json.dumps({"janice": 50000}))

    args = Args(fy=fy, persons="tyson", base_dir=str(tmp_path))

    with pytest.raises(ValueError, match="Missing employment income"):
        cmd_optimize(args)


def test_optimize_three_persons(tmp_path, capsys):
    """Optimize with three persons at different brackets."""
    fy = 25
    fy_dir = tmp_path / "data" / f"fy{fy}"

    for person in ["tyson", "janice", "luna"]:
        data_dir = fy_dir / person / "data"
        data_dir.mkdir(parents=True)
        deductions_csv = data_dir / "deductions.csv"
        deductions_csv.write_text("category,amount\ntravel,5000\n")

    employment_income_file = tmp_path / f"employment_income_fy{fy}.json"
    employment_income_file.write_text(
        json.dumps(
            {
                "tyson": 200000,
                "janice": 100000,
                "luna": 30000,
            }
        )
    )

    args = Args(fy=fy, persons="tyson,janice,luna", base_dir=str(tmp_path))
    cmd_optimize(args)

    captured = capsys.readouterr()
    assert "tyson" in captured.out
    assert "janice" in captured.out
    assert "luna" in captured.out
    assert "$15,000" in captured.out
