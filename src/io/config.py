import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from src.core.models import AUD, Money

TAX_BRACKETS_FY25 = [
    (0, Money(Decimal("0"), AUD)),
    (45000, Money(Decimal("0.16"), AUD)),
    (135000, Money(Decimal("0.30"), AUD)),
    (190000, Money(Decimal("0.37"), AUD)),
    (float("inf"), Money(Decimal("0.45"), AUD)),
]

MEDICARE_LEVY = Decimal("0.02")


@dataclass
class Config:
    """Configuration for tax pipeline (immutable)."""

    fy: str
    persons: list[str]
    base_dir: str | Path
    beem_usernames: dict[str, str]

    @classmethod
    def from_env(cls, config_file: str | Path | None = None) -> "Config":
        """
        Load config from environment variables, fallback to file.

        Env vars (optional):
        - FY: Financial year (e.g., 'fy25')
        - PERSONS: Comma-separated person names
        - BEEM_USERNAMES: JSON dict of person -> beem username

        File format (one person per line):
        fy/person

        Args:
            config_file: Path to config file (default: ./config)

        Returns:
            Config instance
        """
        fy = os.getenv("FY")
        persons_str = os.getenv("PERSONS")
        beem_json = os.getenv("BEEM_USERNAMES", "{}")

        if not fy or not persons_str:
            if not config_file:
                config_file = Path("config")
            if not Path(config_file).exists():
                raise FileNotFoundError(f"No config file at {config_file}")

            with open(config_file) as f:
                lines = [line.strip() for line in f if line.strip()]

            if not lines:
                raise ValueError("Empty config file")

            first = lines[0].split("/")
            fy = fy or first[0]
            persons_str = persons_str or first[1] if len(first) > 1 else ""

            if not persons_str:
                raise ValueError("Cannot determine persons from config")

        persons = [p.strip() for p in persons_str.split(",")]

        import json

        try:
            beem_usernames = json.loads(beem_json)
        except json.JSONDecodeError:
            beem_usernames = {}

        return cls(
            fy=fy,
            persons=persons,
            base_dir=fy,
            beem_usernames=beem_usernames,
        )
