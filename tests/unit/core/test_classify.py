from src.core.classify import classify


def test_single_match():
    rules = {"groceries": ["WOOLWORTHS", "COLES"]}
    assert classify("WOOLWORTHS $50", rules) == {"groceries"}


def test_multiple_matches():
    rules = {
        "groceries": ["WOOLWORTHS"],
        "supermarkets": ["WOOLWORTHS"],
    }
    assert classify("WOOLWORTHS $50", rules) == {"groceries", "supermarkets"}


def test_no_match():
    rules = {"groceries": ["COLES"]}
    assert classify("RANDOM MERCHANT", rules) == set()


def test_partial_match():
    rules = {"transport": ["UBER", "LYFT"]}
    assert classify("UBER TRIP TO AIRPORT", rules) == {"transport"}


def test_case_insensitive():
    rules = {"groceries": ["woolworths"]}
    assert classify("WOOLWORTHS $50", rules) == {"groceries"}
