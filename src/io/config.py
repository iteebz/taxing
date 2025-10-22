import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

TAX_BRACKETS_FY25 = [
    (0, Decimal("0")),
    (45000, Decimal("0.16")),
    (135000, Decimal("0.30")),
    (190000, Decimal("0.37")),
    (float("inf"), Decimal("0.45")),
]

MEDICARE_LEVY = Decimal("0.02")


@dataclass
class Config:
    """Configuration for tax pipeline (immutable)."""

    fy: str
    persons: list[str]
    base_dir: str | Path

    @classmethod
    def from_env(cls, config_file: str | Path | None = None) -> "Config":
        """
        Load config from environment variables, fallback to file.

        Env vars (optional):
        - FY: Financial year (e.g., 'fy25')
        - PERSONS: Comma-separated person names

        File format (one person per line):
        fy/person

        Args:
            config_file: Path to config file (default: ./config)

        Returns:
            Config instance
        """
        fy = os.getenv("FY")
        persons_str = os.getenv("PERSONS")

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

        return cls(
            fy=fy,
            persons=persons,
            base_dir=fy,
        )
