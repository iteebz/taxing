from src.cli.commands.rules import handle_add, handle_clean


class Args:
    """Mock argparse Namespace for testing."""

    def __init__(self, category=None, keyword=None):
        self.category = category
        self.keyword = keyword


def test_add_rule_cli(tmp_path, capsys):
    """Test adding a new rule via the CLI."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    groceries_file = rules_dir / "groceries.txt"
    groceries_file.write_text("OLD_KEYWORD\n")

    # Mock args for 'tax rule groceries "NEW_KEYWORD"'
    args = Args(category="groceries", keyword="NEW_KEYWORD")

    handle_add(args, rules_base_path=rules_dir)

    captured = capsys.readouterr()
    assert "✓ Added rule: NEW_KEYWORD -> groceries" in captured.out

    expected_content = "NEW_KEYWORD\nOLD_KEYWORD\n"  # Sorted alphabetically
    assert groceries_file.read_text() == expected_content


def test_add_existing_rule_cli(tmp_path, capsys):
    """Test adding an already existing rule via the CLI."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    groceries_file = rules_dir / "groceries.txt"
    groceries_file.write_text("EXISTING_KEYWORD\n")

    args = Args(category="groceries", keyword="EXISTING_KEYWORD")

    handle_add(args, rules_base_path=rules_dir)

    captured = capsys.readouterr()
    assert "✓ Rule already exists: EXISTING_KEYWORD -> groceries" in captured.out

    assert groceries_file.read_text() == "EXISTING_KEYWORD\n"


def test_clean_rules_cli(tmp_path, capsys):
    """Test cleaning rule files via the CLI."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    messy_file = rules_dir / "messy.txt"
    messy_file.write_text("# Comment\nKEYWORD2\nKEYWORD1\nKEYWORD2\n  KEYWORD3  \n")

    args = Args()  # handle_clean doesn't use category/keyword args

    handle_clean(args, rules_base_path=rules_dir)

    captured = capsys.readouterr()
    assert "✓ Cleaned 1 rule files (deduped, stripped comments, sorted)" in captured.out

    expected_content = "KEYWORD1\nKEYWORD2\nKEYWORD3\n"
    assert messy_file.read_text() == expected_content
