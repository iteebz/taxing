from pathlib import Path

from src.core.rules import dedupe_keywords, load_rules


def test_dedupe_keywords_removes_subsumed():
    keywords = ["COLES", "COLES CHECKOUT"]
    result = dedupe_keywords(keywords)
    assert result == ["COLES"]


def test_dedupe_keywords_removes_duplicates():
    keywords = ["COLES", "coles", "COLES"]
    result = dedupe_keywords(keywords)
    assert result == ["COLES"]


def test_dedupe_keywords_case_normalization():
    keywords = ["coles", "Woolworths", "ALDI"]
    result = dedupe_keywords(keywords)
    assert result == ["ALDI", "COLES", "WOOLWORTHS"]


def test_dedupe_keywords_sorts_alphabetically():
    keywords = ["ZEBRA", "APPLE", "BANANA"]
    result = dedupe_keywords(keywords)
    assert result == ["APPLE", "BANANA", "ZEBRA"]


def test_dedupe_keywords_empty():
    result = dedupe_keywords([])
    assert result == []


def test_dedupe_keywords_whitespace_handling():
    keywords = ["  COLES  ", "COLES"]
    result = dedupe_keywords(keywords)
    assert result == ["COLES"]


def test_dedupe_keywords_multiple_subsumed():
    keywords = ["A", "AB", "ABC", "ABCD"]
    result = dedupe_keywords(keywords)
    assert result == ["A"]


def test_dedupe_keywords_no_subsumption():
    keywords = ["COLES", "WOOLWORTHS", "ALDI"]
    result = dedupe_keywords(keywords)
    assert result == ["ALDI", "COLES", "WOOLWORTHS"]


def test_load_rules_from_files(tmp_path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    (rules_dir / "groceries.txt").write_text(
        "COLES\nCOLES CHECKOUT\nWOOLWORTHS\n# comment\n\nALDI"
    )
    (rules_dir / "transport.txt").write_text("UBER\nLYFT\n")

    result = load_rules(tmp_path)

    assert set(result.keys()) == {"groceries", "transport"}
    assert result["groceries"] == ["ALDI", "COLES", "WOOLWORTHS"]
    assert result["transport"] == ["LYFT", "UBER"]


def test_load_rules_missing_directory():
    result = load_rules("/nonexistent")
    assert result == {}


def test_load_rules_empty_files(tmp_path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "empty.txt").write_text("")

    result = load_rules(tmp_path)
    assert result == {}


def test_load_rules_comments_and_blanks(tmp_path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    (rules_dir / "test.txt").write_text("# Header\n\nKEYWORD1\n  \n# Another comment\nKEYWORD2\n")

    result = load_rules(tmp_path)
    assert result == {"test": ["KEYWORD1", "KEYWORD2"]}


def test_load_rules_path_object(tmp_path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "cat.txt").write_text("KW1\nKW2")

    result = load_rules(Path(tmp_path))
    assert result == {"cat": ["KW1", "KW2"]}
