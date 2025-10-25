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


def search_description(
    description: str,
    cache: dict[str, list[dict]],
    cache_path: Path,
    max_results: int = 3,
) -> list[dict]:
    """Search sanitized description, return top results with title + snippet."""
    if description in cache:
        return cache[description]

    try:
        results = DDGS().text(description, max_results=max_results)
        results_data = [{"title": r.get("title", ""), "body": r.get("body", "")} for r in results]
        cache[description] = results_data
        save_cache(cache, cache_path)
        return results_data
    except Exception:
        return []
