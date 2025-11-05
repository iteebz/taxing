from dataclasses import dataclass, field
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml


@dataclass(frozen=True)
class Bracket:
    rate: Decimal
    from_val: int
    to_val: int


@dataclass(frozen=True)
class MedicareSurchargeTier:
    threshold: int
    rate: Decimal


@dataclass(frozen=True)
class MedicareSurchargeConfig:
    dependent_increment: int
    single: list[MedicareSurchargeTier] = field(default_factory=list)
    family: list[MedicareSurchargeTier] = field(default_factory=list)


@dataclass(frozen=True)
class MedicareConfig:
    base_rate: Decimal
    low_income_threshold_single: int
    phase_in_rate_single: Decimal
    low_income_threshold_family: int
    phase_in_rate_family: Decimal
    dependent_increment: int
    surcharge: MedicareSurchargeConfig | None = None


@dataclass(frozen=True)
class FYConfig:
    brackets: list[Bracket]
    medicare: MedicareConfig


@dataclass(frozen=True)
class ConfigRegistry:
    """Single source of truth for all configuration."""

    fy_configs: dict[int, FYConfig]
    deduction_groups: dict[str, list[str]]
    rate_basis_map: dict[str, str]


def _resolve_year(fy: int) -> int:
    return fy if fy >= 1900 else 2000 + fy


def _get_default_config_path() -> Path:
    """Get default config.yaml path."""
    return Path(__file__).parent.parent.parent / "config.yaml"


@lru_cache(maxsize=1)
def _load_registry(config_path: Path) -> ConfigRegistry:
    """Load and parse entire config registry (cached).

    Returns frozen ConfigRegistry with all FY configs, deduction groups, and rate basis map.
    Single source of truth for all configuration.
    """
    with open(config_path) as f:
        raw = yaml.safe_load(f)
    if not raw:
        raise ValueError(f"Config file {config_path} is empty or malformed.")

    # Parse all FY configs
    fy_configs = {}
    for key, fy_data in raw.items():
        if not key.startswith("fy_"):
            continue
        fy = int(key.split("_")[1])
        fy_configs[fy] = _parse_fy_config(key, fy_data, raw)

    # Extract deduction groups and rate basis map
    deduction_groups = raw.get("deductions", {})
    rate_basis_map = raw.get("rate_basis", {})

    return ConfigRegistry(
        fy_configs=fy_configs,
        deduction_groups=deduction_groups,
        rate_basis_map=rate_basis_map,
    )


def _parse_surcharge(
    surcharge_data: dict[str, object] | None,
) -> MedicareSurchargeConfig | None:
    if not surcharge_data:
        return None

    dep_increment = int(surcharge_data.get("dependent_increment", 0))

    def parse_tiers(key: Literal["single", "family"]) -> list[MedicareSurchargeTier]:
        tiers_raw = surcharge_data.get(key, []) or []
        return sorted(
            (
                MedicareSurchargeTier(
                    threshold=int(tier["threshold"]),
                    rate=Decimal(str(tier["rate"])),
                )
                for tier in tiers_raw
            ),
            key=lambda t: t.threshold,
        )

    return MedicareSurchargeConfig(
        dependent_increment=dep_increment,
        single=parse_tiers("single"),
        family=parse_tiers("family"),
    )


def _parse_fy_config(fy_key: str, fy_data: dict, full_config: dict) -> FYConfig:
    """Parse a single FY config from raw YAML data."""
    brackets = [
        Bracket(
            rate=Decimal(str(bracket["rate"])),
            from_val=int(bracket["from"]),
            to_val=int(bracket["to"]),
        )
        for bracket in fy_data.get("brackets", [])
    ]

    medicare_raw = fy_data.get("medicare")
    if not medicare_raw:
        raise ValueError(f"Medicare configuration missing for {fy_key}")

    medicare = MedicareConfig(
        base_rate=Decimal(str(medicare_raw["base_rate"])),
        low_income_threshold_single=int(medicare_raw["low_income_threshold_single"]),
        phase_in_rate_single=Decimal(str(medicare_raw["phase_in_rate_single"])),
        low_income_threshold_family=int(medicare_raw["low_income_threshold_family"]),
        phase_in_rate_family=Decimal(str(medicare_raw["phase_in_rate_family"])),
        dependent_increment=int(medicare_raw["dependent_increment"]),
        surcharge=_parse_surcharge(medicare_raw.get("surcharge")),
    )

    return FYConfig(brackets=brackets, medicare=medicare)


def load_config(fy: int, config_path: Path | None = None) -> FYConfig:
    """Load financial year config."""
    if config_path is None:
        config_path = _get_default_config_path()

    registry = _load_registry(config_path)
    resolved_fy = _resolve_year(fy)

    if resolved_fy not in registry.fy_configs:
        available = sorted(registry.fy_configs.keys())
        raise ValueError(
            f"FY{resolved_fy} configuration not found in config.yaml. " f"Available: {available}"
        )

    return registry.fy_configs[resolved_fy]


def get_deduction_groups(config_path: Path | None = None) -> dict[str, list[str]]:
    """Load deduction groupings from config."""
    if config_path is None:
        config_path = _get_default_config_path()

    registry = _load_registry(config_path)
    return registry.deduction_groups


def get_rate_basis_map(config_path: Path | None = None) -> dict[str, str]:
    """Load rate basis mapping from config."""
    if config_path is None:
        config_path = _get_default_config_path()

    registry = _load_registry(config_path)
    return registry.rate_basis_map
