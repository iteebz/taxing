"""Phase 3a property CLI integration tests."""

from pathlib import Path

from src.cli import cmd_property


class Args:
    """Mock argparse Namespace for testing."""

    def __init__(self, fy, person, base_dir="."):
        self.fy = fy
        self.person = person
        self.base_dir = base_dir


def test_property_cli_complete(tmp_path, capsys):
    """Full CLI flow: load CSVs → aggregate → display."""
    fy = 25
    person = "alice"

    property_dir = tmp_path / "archive" / str(fy) / person / "property"
    property_dir.mkdir(parents=True)

    (property_dir / "rent.csv").write_text("2000\n2000\n")
    (property_dir / "water.csv").write_text("100\n100\n")
    (property_dir / "council.csv").write_text("200\n200\n")
    (property_dir / "strata.csv").write_text("150\n150\n")

    args = Args(fy=fy, person=person, base_dir=str(tmp_path))
    cmd_property(args)

    captured = capsys.readouterr()

    assert "alice" in captured.out
    assert "FY25" in captured.out
    assert "4000" in captured.out or "4,000" in captured.out
    assert "Rent" in captured.out
    assert "Water" in captured.out
    assert "Council" in captured.out
    assert "Strata" in captured.out
    assert "TOTAL" in captured.out


def test_property_cli_missing_property_dir(tmp_path, capsys):
    """No property directory returns graceful message."""
    fy = 25
    person = "bob"

    args = Args(fy=fy, person=person, base_dir=str(tmp_path))
    cmd_property(args)

    captured = capsys.readouterr()

    assert "No property expenses found" in captured.out
    assert person in captured.out


def test_property_cli_partial_categories(tmp_path, capsys):
    """Only rent provided; other categories show zero."""
    fy = 25
    person = "charlie"

    property_dir = tmp_path / "archive" / str(fy) / person / "property"
    property_dir.mkdir(parents=True)

    (property_dir / "rent.csv").write_text("3000\n")

    args = Args(fy=fy, person=person, base_dir=str(tmp_path))
    cmd_property(args)

    captured = capsys.readouterr()

    assert "3000" in captured.out or "3,000" in captured.out
    assert "Rent" in captured.out
    assert "0.00" in captured.out
