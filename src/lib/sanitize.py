import re


def normalize_spaces(text: str) -> str:
    """Normalize 3+ consecutive spaces to 2 spaces, keep 1-2 spaces. Strip leading/trailing."""
    text = text.strip()
    return re.sub(r" {3,}", "  ", text)


def strip_comment(text: str) -> str:
    """Remove inline comment (everything after #)."""
    return text.split("#")[0].strip()


def sanitize(text: str) -> str:
    """Sanitize text: strip comment, normalize spaces, strip whitespace."""
    text = strip_comment(text)
    return normalize_spaces(text)
