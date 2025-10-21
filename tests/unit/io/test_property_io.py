"""Property expense I/O tests."""

from src.io.property import load_property_expenses


def test_load_property_expenses_complete(tmp_path):
    """Load all four property expense categories."""
    fy = 25
    person = "tyson"

    property_dir = tmp_path / "archive" / str(fy) / person / "property"
    property_dir.mkdir(parents=True)

    (property_dir / "rent.csv").write_text("2000\n2000\n")
    (property_dir / "water.csv").write_text("100\n100\n")
    (property_dir / "council.csv").write_text("200\n200\n")
    (property_dir / "strata.csv").write_text("150\n150\n")

    expenses = load_property_expenses(tmp_path, fy, person)

    assert len(expenses) == 8
    assert sum(1 for e in expenses if e.expense_type == "rent") == 2
    assert sum(1 for e in expenses if e.expense_type == "water") == 2
    assert sum(1 for e in expenses if e.expense_type == "council") == 2
    assert sum(1 for e in expenses if e.expense_type == "strata") == 2


def test_load_property_expenses_missing_directory(tmp_path):
    """Missing property directory returns empty list."""
    expenses = load_property_expenses(tmp_path, 25, "tyson")
    assert expenses == []


def test_load_property_expenses_partial_categories(tmp_path):
    """Load subset of categories gracefully."""
    fy = 25
    person = "tyson"

    property_dir = tmp_path / "archive" / str(fy) / person / "property"
    property_dir.mkdir(parents=True)

    (property_dir / "rent.csv").write_text("2000\n")

    expenses = load_property_expenses(tmp_path, fy, person)

    assert len(expenses) == 1
    assert expenses[0].expense_type == "rent"


def test_load_property_expenses_decimal_values(tmp_path):
    """Load decimal amounts correctly."""
    fy = 25
    person = "tyson"

    property_dir = tmp_path / "archive" / str(fy) / person / "property"
    property_dir.mkdir(parents=True)

    (property_dir / "rent.csv").write_text("1234.56\n5678.90\n")

    expenses = load_property_expenses(tmp_path, fy, person)

    assert len(expenses) == 2
    assert str(expenses[0].amount) == "1234.56"
    assert str(expenses[1].amount) == "5678.90"


def test_load_property_expenses_skip_comments(tmp_path):
    """Skip comment lines in CSV."""
    fy = 25
    person = "tyson"

    property_dir = tmp_path / "archive" / str(fy) / person / "property"
    property_dir.mkdir(parents=True)

    (property_dir / "rent.csv").write_text("# comment\n2000\n# another comment\n")

    expenses = load_property_expenses(tmp_path, fy, person)

    assert len(expenses) == 1
    assert str(expenses[0].amount) == "2000"


def test_load_property_expenses_skip_invalid(tmp_path):
    """Skip invalid amount lines."""
    fy = 25
    person = "tyson"

    property_dir = tmp_path / "archive" / str(fy) / person / "property"
    property_dir.mkdir(parents=True)

    (property_dir / "rent.csv").write_text("2000\ninvalid\n3000\n")

    expenses = load_property_expenses(tmp_path, fy, person)

    assert len(expenses) == 2
    assert str(expenses[0].amount) == "2000"
    assert str(expenses[1].amount) == "3000"


def test_load_property_expenses_empty_file(tmp_path):
    """Empty file returns no expenses."""
    fy = 25
    person = "tyson"

    property_dir = tmp_path / "archive" / str(fy) / person / "property"
    property_dir.mkdir(parents=True)

    (property_dir / "rent.csv").write_text("")

    expenses = load_property_expenses(tmp_path, fy, person)

    assert expenses == []
