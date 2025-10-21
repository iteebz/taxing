from src.core.classify import classify
from src.core.rules import load_rules


def test_rules_with_classify(tmp_path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    (rules_dir / "groceries.txt").write_text("COLES\nWOOLWORTHS")
    (rules_dir / "transport.txt").write_text("UBER\nLYFT")

    rules = load_rules(tmp_path)
    assert classify("COLES $50", rules) == {"groceries"}
    assert classify("UBER TRIP", rules) == {"transport"}
    assert classify("RANDOM", rules) == set()


def test_real_rules_basic(tmp_path):
    import shutil
    from pathlib import Path

    rules_src = Path(__file__).parent.parent.parent / "rules"
    if rules_src.exists():
        shutil.copytree(rules_src, tmp_path / "rules")
        rules = load_rules(tmp_path)

        assert len(rules) > 0
        assert "groceries" in rules or "supermarket" in rules
