from dataclasses import dataclass, field
from decimal import Decimal
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
    actual_cost_categories: dict[str, list[str]] = field(default_factory=dict)
    fixed_rates: dict[str, Decimal] = field(default_factory=dict)


def _resolve_year(fy: int) -> int:
    return fy if fy >= 1900 else 2000 + fy


def _parse_surcharge(
    surcharge_data: dict[str, object] | None,
) -> MedicareSurchargeConfig | None:
    if not surcharge_data:
        return None

    dep_increment = int(surcharge_data.get("dependent_increment", 0))

    def parse_tiers(key: Literal["single", "family"]) -> list[MedicareSurchargeTier]:
        tiers_raw = surcharge_data.get(key, []) or []
        tiers = sorted(
            (
                MedicareSurchargeTier(
                    threshold=int(tier["threshold"]),
                    rate=Decimal(str(tier["rate"])),
                )
                for tier in tiers_raw
            ),
            key=lambda t: t.threshold,
        )
        return tiers

    return MedicareSurchargeConfig(
        dependent_increment=dep_increment,
        single=parse_tiers("single"),
        family=parse_tiers("family"),
    )


def load_config(fy: int, config_path: Path | None = None) -> FYConfig:
    """Load financial year config, with fallback to closest year."""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config.yaml"

    with open(config_path) as f:
        full_config = yaml.safe_load(f)

    if not full_config:
        raise ValueError("Config file is empty or malformed.")

    resolved_fy = _resolve_year(fy)
    available_fys = {int(k.split("_")[1]) for k in full_config}
    target_fy_key = f"fy_{resolved_fy}"

    if target_fy_key not in full_config:
        closest_fy = min(available_fys, key=lambda y: abs(y - resolved_fy))
        target_fy_key = f"fy_{closest_fy}"

    fy_data = full_config[target_fy_key]

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
        raise ValueError(f"Medicare configuration missing for {target_fy_key}")

    medicare = MedicareConfig(
        base_rate=Decimal(str(medicare_raw["base_rate"])),
        low_income_threshold_single=int(medicare_raw["low_income_threshold_single"]),
        phase_in_rate_single=Decimal(str(medicare_raw["phase_in_rate_single"])),
        low_income_threshold_family=int(medicare_raw["low_income_threshold_family"]),
        phase_in_rate_family=Decimal(str(medicare_raw["phase_in_rate_family"])),
        dependent_increment=int(medicare_raw["dependent_increment"]),
        surcharge=_parse_surcharge(medicare_raw.get("surcharge")),
    )

    actual_cost = fy_data.get("actual_cost_categories", {})
    fixed_rates = {
        key: Decimal(str(value)) for key, value in fy_data.get("fixed_rates", {}).items()
    }

    return FYConfig(
        brackets=brackets,
        medicare=medicare,
        actual_cost_categories=actual_cost,
        fixed_rates=fixed_rates,
    )
