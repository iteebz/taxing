import json

import pytest

from src.cli import cmd_optimize


class Args:
    """Mock argparse Namespace for testing."""

    def __init__(self, fy, persons, base_dir="."):
        self.fy = fy
        self.persons = persons
        self.base_dir = base_dir


def test_optimize_alice_bob_basic(tmp_path, capsys):
    """Optimize allocation for Alice and Bob with shared deductions."""
    fy = 25
    fy_dir = tmp_path / "data" / f"fy{fy}"

    for person in ["alice", "bob"]:
        data_dir = fy_dir / person / "data"
        data_dir.mkdir(parents=True)

        deductions_csv = data_dir / "deductions.csv"
        if person == "alice":
            deductions_csv.write_text("category,amount\ninvestment,5000\n")
        else:
            deductions_csv.write_text("category,amount\ntravel,3000\n")

    employment_income_file = tmp_path / f"employment_income_fy{fy}.json"
    employment_income_file.write_text(json.dumps({"alice": 150000, "bob": 50000}))

    args = Args(fy=fy, persons="alice,bob", base_dir=str(tmp_path))
    cmd_optimize(args)

    captured = capsys.readouterr()
    assert "alice" in captured.out
    assert "bob" in captured.out
    assert "TOTAL" in captured.out
    assert "$" in captured.out


def test_optimize_single_person(tmp_path, capsys):
    """Optimize with single person."""
    fy = 25
    fy_dir = tmp_path / "data" / f"fy{fy}"

    data_dir = fy_dir / "alice" / "data"
    data_dir.mkdir(parents=True)

    deductions_csv = data_dir / "deductions.csv"
    deductions_csv.write_text("category,amount\ninvestment,10000\n")

    employment_income_file = tmp_path / f"employment_income_fy{fy}.json"
    employment_income_file.write_text(json.dumps({"alice": 100000}))

    args = Args(fy=fy, persons="alice", base_dir=str(tmp_path))
    cmd_optimize(args)

    captured = capsys.readouterr()
    assert "alice" in captured.out
    assert "$10,000" in captured.out


def test_optimize_no_persons_error():
    """Error when --persons not provided."""
    args = Args(fy=25, persons="", base_dir=".")

    with pytest.raises(ValueError, match="--persons required"):
        cmd_optimize(args)


def test_optimize_missing_employment_income(tmp_path):
    """Error when employment income config missing."""
    fy = 25
    args = Args(fy=fy, persons="alice", base_dir=str(tmp_path))

    with pytest.raises(FileNotFoundError, match="employment_income"):
        cmd_optimize(args)


def test_optimize_missing_person_income(tmp_path):
    """Error when person missing from employment income."""
    fy = 25
    employment_income_file = tmp_path / f"employment_income_fy{fy}.json"
    employment_income_file.write_text(json.dumps({"bob": 50000}))

    args = Args(fy=fy, persons="alice", base_dir=str(tmp_path))

    with pytest.raises(ValueError, match="Missing employment income"):
        cmd_optimize(args)


def test_optimize_three_persons(tmp_path, capsys):
    """Optimize with three persons at different brackets."""
    fy = 25
    fy_dir = tmp_path / "data" / f"fy{fy}"

    for person in ["alice", "bob", "charlie"]:
        data_dir = fy_dir / person / "data"
        data_dir.mkdir(parents=True)
        deductions_csv = data_dir / "deductions.csv"
        deductions_csv.write_text("category,amount\ntravel,5000\n")

    employment_income_file = tmp_path / f"employment_income_fy{fy}.json"
    employment_income_file.write_text(
        json.dumps(
            {
                "alice": 200000,
                "bob": 100000,
                "charlie": 30000,
            }
        )
    )

    args = Args(fy=fy, persons="alice,bob,charlie", base_dir=str(tmp_path))
    cmd_optimize(args)

    captured = capsys.readouterr()
    assert "alice" in captured.out
    assert "bob" in captured.out
    assert "charlie" in captured.out
    assert "$15,000" in captured.out
