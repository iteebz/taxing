from src.core.classify import classify


def test_classify_single_match():
    rules = {"groceries": ["WOOLWORTHS", "COLES"]}
    result = classify("WOOLWORTHS $50", rules)
    assert result == {"groceries"}


def test_classify_multiple_matches():
    rules = {
        "groceries": ["WOOLWORTHS"],
        "supermarkets": ["WOOLWORTHS"],
    }
    result = classify("WOOLWORTHS $50", rules)
    assert result == {"groceries", "supermarkets"}


def test_classify_no_match():
    rules = {"groceries": ["COLES"]}
    result = classify("RANDOM MERCHANT", rules)
    assert result == set()


def test_classify_case_insensitive():
    rules = {"groceries": ["woolworths"]}
    result = classify("WOOLWORTHS $50", rules)
    assert result == {"groceries"}


def test_classify_partial_match():
    rules = {"transport": ["UBER", "LYFT"]}
    result = classify("UBER TRIP TO AIRPORT", rules)
    assert result == {"transport"}


def test_classify_empty_rules():
    rules = {}
    result = classify("WOOLWORTHS $50", rules)
    assert result == set()


def test_classify_empty_description():
    rules = {"groceries": ["WOOLWORTHS"]}
    result = classify("", rules)
    assert result == set()


def test_classify_multiple_keywords_in_category():
    rules = {"home_office": ["OFFICEWORKS", "STAPLES", "BUNNINGS"]}
    result = classify("BUNNINGS $100", rules)
    assert result == {"home_office"}


def test_classify_overlapping_keywords():
    rules = {
        "groceries": ["WOOLWORTHS"],
        "supermarkets": ["WOOLWORTHS SUPERMARKET"],
    }
    result = classify("WOOLWORTHS SUPERMARKET", rules)
    assert result == {"groceries", "supermarkets"}


def test_classify_whitespace_handling():
    rules = {"groceries": ["WOOLWORTHS"]}
    result = classify("  WOOLWORTHS  ", rules)
    assert result == {"groceries"}
