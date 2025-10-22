import json
from pathlib import Path

from ddgs import DDGS


def load_cache(cache_path: Path) -> dict[str, list[str]]:
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)
    return {}


def save_cache(cache: dict[str, list[str]], cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)


def search_merchant(
    merchant: str,
    cache: dict[str, list[str]],
    cache_path: Path,
    max_results: int = 3,
) -> list[str]:
    if merchant in cache:
        return cache[merchant]

    try:
        results = DDGS().text(merchant, max_results=max_results)
        snippets = [r.get("body", "") for r in results]
        cache[merchant] = snippets
        save_cache(cache, cache_path)
        return snippets
    except Exception:
        return []


def extract_search_categories(snippets: list[str]) -> list[str]:
    keyword_map = {
        "dining": ["restaurant", "café", "cafe", "pizzeria", "taverna", "bistro", "cuisine"],
        "accom": ["hotel", "accommodation", "hostel", "airbnb", "resort"],
        "travel": ["airline", "flight", "airport", "rail", "train", "tourism"],
        "supermarket": ["supermarket", "grocer", "grocery", "market"],
        "software": ["software", "app", "saas", "subscription", "platform"],
        "medical": ["doctor", "hospital", "clinic", "pharmacy", "health"],
        "electronics": ["electronics", "computer", "tech", "digital"],
        "online_retail": ["retail", "store", "shop", "online"],
    }

    text = " ".join(snippets).lower()
    hints = []
    for cat, keywords in keyword_map.items():
        if any(kw in text for kw in keywords):
            hints.append(cat)

    return list(set(hints))
