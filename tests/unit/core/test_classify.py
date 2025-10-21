from src.core.classify import classify


def test_single_match():
    rules = {"groceries": ["WOOLWORTHS", "COLES"]}
    result = classify("WOOLWORTHS $50", rules)
    assert result == {"groceries"}


def test_multiple_matches():
    rules = {
        "groceries": ["WOOLWORTHS"],
        "supermarkets": ["WOOLWORTHS"],
    }
    result = classify("WOOLWORTHS $50", rules)
    assert result == {"groceries", "supermarkets"}


def test_no_match():
    rules = {"groceries": ["COLES"]}
    result = classify("RANDOM MERCHANT", rules)
    assert result == set()


def test_case_insensitive():
    rules = {"groceries": ["woolworths"]}
    result = classify("WOOLWORTHS $50", rules)
    assert result == {"groceries"}


def test_partial_match():
    rules = {"transport": ["UBER", "LYFT"]}
    result = classify("UBER TRIP TO AIRPORT", rules)
    assert result == {"transport"}


def test_empty_rules():
    rules = {}
    result = classify("WOOLWORTHS $50", rules)
    assert result == set()


def test_empty_description():
    rules = {"groceries": ["WOOLWORTHS"]}
    result = classify("", rules)
    assert result == set()


def test_multiple_keywords():
    rules = {"home_office": ["OFFICEWORKS", "STAPLES", "BUNNINGS"]}
    result = classify("BUNNINGS $100", rules)
    assert result == {"home_office"}


def test_overlapping():
    rules = {
        "groceries": ["WOOLWORTHS"],
        "supermarkets": ["WOOLWORTHS SUPERMARKET"],
    }
    result = classify("WOOLWORTHS SUPERMARKET", rules)
    assert result == {"groceries", "supermarkets"}


def test_whitespace():
    rules = {"groceries": ["WOOLWORTHS"]}
    result = classify("  WOOLWORTHS  ", rules)
    assert result == {"groceries"}


def test_classify_with_actual_rules():
    """Test classification with actual project rules."""
    from src.core.rules import load_rules

    rules = load_rules(".")

    # These merchants should match groceries rules
    result = classify("HARRIS FARM MARKET", rules)
    assert "groceries" in result

    # Taxi
    result = classify("UBER TRIP", rules)
    assert "taxi" in result
