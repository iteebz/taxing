"""Load category hierarchy from cats.yaml."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

Level1 = Literal[
    "home_office", "vehicle", "meals", "health", "donations", "income", "transfers"
]


@dataclass(frozen=True)
class Cat:
    """Category metadata."""

    level2: str
    level1: Level1 | None
    deductible: bool


def _load_hierarchy() -> dict[str, Cat]:
    """Load category hierarchy from cats.yaml."""
    cats_path = Path(__file__).parent.parent.parent / "cats.yaml"
    with open(cats_path) as f:
        data = yaml.safe_load(f)

    result = {}

    for l1_name, l1_data in data["level1"].items():
        for l2_name, cats_list in l1_data["level2"].items():
            for cat_name in cats_list:
                result[cat_name] = Cat(
                    level2=l2_name,
                    level1=l1_name,
                    deductible=True,
                )

    for l2_name, cats_list in data["non_deductible"]["level2"].items():
        for cat_name in cats_list:
            result[cat_name] = Cat(
                level2=l2_name,
                level1=None,
                deductible=False,
            )

    return result


_CATS = _load_hierarchy()


def get(cat: str) -> Cat | None:
    """Get category metadata."""
    return _CATS.get(cat)


def level2(cat: str) -> str | None:
    """Get level2 category."""
    meta = get(cat)
    return meta.level2 if meta else None


def level1(cat: str) -> Level1 | None:
    """Get level1 deduction group."""
    meta = get(cat)
    return meta.level1 if meta else None


def is_deductible(cat: str) -> bool:
    """Check if category is deductible."""
    meta = get(cat)
    return meta.deductible if meta else False
