import tempfile
from pathlib import Path

import pytest

from src.io.config import Config


def test_from_env(monkeypatch):
    monkeypatch.setenv("FY", "fy25")
    monkeypatch.setenv("PERSONS", "tyson,jaynice")
    monkeypatch.setenv("BEEM_USERNAMES", '{"tyson": "tysonchan"}')

    cfg = Config.from_env()

    assert cfg.fy == "fy25"
    assert cfg.persons == ["tyson", "jaynice"]
    assert cfg.beem_usernames == {"tyson": "tysonchan"}


def test_from_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config"
        config_file.write_text("fy25/tyson\n")

        cfg = Config.from_env(config_file)

        assert cfg.fy == "fy25"
        assert cfg.persons == ["tyson"]


def test_env_overrides_file(monkeypatch):
    monkeypatch.setenv("FY", "fy26")
    monkeypatch.setenv("PERSONS", "tyson,janice")

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config"
        config_file.write_text("fy25/tyson\n")

        cfg = Config.from_env(config_file)

        assert cfg.fy == "fy26"
        assert cfg.persons == ["tyson", "janice"]


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        Config.from_env(Path("/nonexistent/config"))


def test_empty_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config"
        config_file.write_text("")

        with pytest.raises(ValueError):
            Config.from_env(config_file)


def test_default_beem_usernames():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config"
        config_file.write_text("fy25/tyson\n")

        cfg = Config.from_env(config_file)

        assert cfg.beem_usernames == {}
