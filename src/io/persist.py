from dataclasses import fields as dc_fields
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import TypeVar

import pandas as pd

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
        case set():
            return ",".join(sorted(value)) if value else ""
        case bool():
            return str(value).lower()
        case _:
            return str(value)


def _to_date(s: str) -> date | None:
    """Decode date from ISO string."""
    if not s or s.isspace():
        return None
    return pd.to_datetime(s).date()


def _to_decimal(s: str) -> Decimal | None:
    """Decode Decimal from string."""
    if not s or s.isspace():
        return None
    return Decimal(s)


def _to_set(s: str) -> set[str]:
    """Decode set from comma-separated string."""
    if not s or s.isspace():
        return set()
    return set(s.split(","))


def _to_bool(s: str) -> bool:
    """Decode bool from string."""
    return s.lower() in ("true", "1", "yes") if s else False


def _to_int(s: str) -> int | None:
    """Decode int from string."""
    if not s or s.isspace():
        return None
    return int(float(s))


def _to_float(s: str) -> float | None:
    """Decode float from string."""
    if not s or s.isspace():
        return None
    return float(s)


def _deserialize(value: str, field_type: type) -> object:
    """Reconstruct typed value from CSV string using explicit codecs."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    value = str(value).strip()

    match field_type:
        case _ if field_type is date:
            return _to_date(value)
        case _ if field_type is Decimal:
            return _to_decimal(value)
        case _ if field_type is set or str(field_type).startswith("set"):
            return _to_set(value)
        case _ if field_type is bool:
            return _to_bool(value)
        case _ if field_type is int:
            return _to_int(value)
        case _ if field_type is float:
            return _to_float(value)
        case _ if field_type is str or field_type is type(None):
            return value if value else None
        case _:
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

    if model.__name__ == "Transaction" and "category" in df.columns and "cats" not in df.columns:
        df = df.rename(columns={"category": "cats"})

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
