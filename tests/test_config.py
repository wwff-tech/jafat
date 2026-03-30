"""Tests for jafat.config."""

import tomllib
from pathlib import Path

import pytest

from jafat import config


def test_defaults_returned_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.toml")
    cfg = config.load()
    assert cfg["model"] == "composer-2-fast"
    assert cfg["trust"] is True
    assert cfg["verbose"] is False


def test_file_values_override_defaults(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[defaults]\nmodel = "composer-2"\nverbose = true\n')
    monkeypatch.setattr(config, "CONFIG_PATH", cfg_path)
    cfg = config.load()
    assert cfg["model"] == "composer-2"
    assert cfg["verbose"] is True
    assert cfg["trust"] is True  # still default


def test_write_default_creates_file(tmp_path, monkeypatch):
    cfg_path = tmp_path / "jafat" / "config.toml"
    monkeypatch.setattr(config, "CONFIG_PATH", cfg_path)
    config.write_default()
    assert cfg_path.exists()
    with open(cfg_path, "rb") as f:
        parsed = tomllib.load(f)
    assert "defaults" in parsed


def test_write_default_does_not_overwrite(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text("[defaults]\nmodel = \"custom\"\n")
    monkeypatch.setattr(config, "CONFIG_PATH", cfg_path)
    config.write_default()
    assert "custom" in cfg_path.read_text()
