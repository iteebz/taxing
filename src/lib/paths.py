from pathlib import Path


def data_root(base_dir: str | Path) -> Path:
    """Root data directory."""
    return Path(base_dir) / "data"


def data_raw(base_dir: str | Path) -> Path:
    """Raw input data directory."""
    return data_root(base_dir) / "raw"


def data_raw_fy(base_dir: str | Path, fy: int) -> Path:
    """Raw data directory for a fiscal year."""
    return data_raw(base_dir) / f"fy{fy}"


def data_raw_fy_person(base_dir: str | Path, fy: int, person: str) -> Path:
    """Raw data directory for a person in a fiscal year."""
    return data_raw_fy(base_dir, fy) / person


def transactions_csv(base_dir: str | Path) -> Path:
    """Unified transactions CSV."""
    return data_root(base_dir) / "transactions.csv"


def deductions_csv(base_dir: str | Path) -> Path:
    """Unified deductions CSV."""
    return data_root(base_dir) / "deductions.csv"


def trades_csv(base_dir: str | Path) -> Path:
    """Unified trades CSV (normalized list, all people/years)."""
    return data_root(base_dir) / "trades.csv"


def gains_csv(base_dir: str | Path) -> Path:
    """Capital gains CSV (derived from trades, for tax reporting)."""
    return data_root(base_dir) / "gains.csv"
