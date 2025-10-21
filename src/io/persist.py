from dataclasses import fields as dc_fields
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import TypeVar, get_args, get_origin

import pandas as pd

from src.core.models import Money

T = TypeVar("T")


def _serialize(value: object) -> str:
    """Convert any value to CSV-friendly string."""
    match value:
        case None:
            return ""
        case date():
            return value.isoformat()
        case Decimal():
            return str(value)
        case Money():
            return f"{value.amount}|{value.currency}"
        case set():
            return ",".join(sorted(value)) if value else ""
        case bool():
            return str(value).lower()
        case _:
            return str(value)


def _deserialize(value: str, field_type: type) -> object:
    """Reconstruct typed value from CSV string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    value = str(value).strip()
    if not value:
        origin = get_origin(field_type)
        if origin is set or field_type is set:
            return set()
        return None

    origin = get_origin(field_type)
    args = get_args(field_type)

    if field_type is date:
        return pd.to_datetime(value).date()
    if field_type is Decimal:
        return Decimal(value)
    if field_type is Money:
        parts = value.split("|")
        if len(parts) != 2:
            raise ValueError(f"Invalid Money format: {value}")
        return Money(Decimal(parts[0]), parts[1])
    if (
        field_type is set
        or origin is set
        or (args and (get_origin(args[0]) is set or args[0] is set))
    ):
        return set(value.split(",")) if value else set()
    if field_type is bool:
        return value.lower() in ("true", "1", "yes")
    if field_type is int:
        return int(value)
    if field_type is str:
        return str(value)
    return value


def to_csv(objects: list[T], path: str | Path, model_type: type | None = None) -> None:
    """Write any frozen dataclass list to CSV."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    if not objects:
        if model_type is None:
            pd.DataFrame().to_csv(path, index=False)
        else:
            cols = [f.name for f in dc_fields(model_type)]
            pd.DataFrame(columns=cols).to_csv(path, index=False)
        return

    obj_type = type(objects[0])
    cols = [f.name for f in dc_fields(obj_type)]

    data = []
    for obj in objects:
        row = {}
        for field in dc_fields(obj_type):
            val = getattr(obj, field.name)
            row[field.name] = _serialize(val)
        data.append(row)

    df = pd.DataFrame(data, columns=cols)
    df.to_csv(path, index=False)


def from_csv(path: str | Path, model: type[T]) -> list[T]:
    """Read CSV back to frozen dataclass list."""
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return []

    if df.empty:
        return []

    objs = []
    type_map = {f.name: f.type for f in dc_fields(model)}

    for _, row in df.iterrows():
        kwargs = {}
        for field in dc_fields(model):
            raw = row[field.name]
            kwargs[field.name] = _deserialize(raw, type_map[field.name])

        objs.append(model(**kwargs))

    return objs


def dicts_to_csv(items: list[dict], path: str | Path) -> None:
    """Write dict list to CSV (for weights, summary)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(items)
    df.to_csv(path, index=False)


def dicts_from_csv(path: str | Path) -> list[dict]:
    """Read CSV to dict list."""
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return []
    return df.to_dict("records") if not df.empty else []


def weights_to_csv(weights: dict[str, Decimal], path: str | Path) -> None:
    """Write weights to CSV."""
    dicts_to_csv([{"category": k, "weight": str(v)} for k, v in weights.items()], path)


def weights_from_csv(path: str | Path) -> dict[str, Decimal]:
    """Read weights from CSV."""
    dicts = dicts_from_csv(path)
    return {d["category"]: Decimal(str(d["weight"])) for d in dicts}
