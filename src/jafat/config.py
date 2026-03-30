"""Config loading from ~/.config/jafat/config.toml."""

import logging
import tomllib
from pathlib import Path

log = logging.getLogger(__name__)

CONFIG_PATH = Path.home() / ".config" / "jafat" / "config.toml"

DEFAULTS: dict = {
    "model": "composer-2-fast",
    "trust": True,
    "verbose": False,
    "force": False,
    "partial": True,  # stream-partial-output by default
}


def load() -> dict:
    """Load config, merging file over defaults. Never raises."""
    cfg = DEFAULTS.copy()
    if not CONFIG_PATH.exists():
        return cfg
    try:
        with open(CONFIG_PATH, "rb") as f:
            file_cfg = tomllib.load(f)
        cfg.update(file_cfg.get("defaults", {}))
    except Exception as e:
        log.warning("Could not parse config %s: %s", CONFIG_PATH, e)
    return cfg


def write_default() -> None:
    """Write a default config file if none exists."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        return
    CONFIG_PATH.write_text(
        """\
[defaults]
model = "composer-2-fast"
trust = true
verbose = false
force = false
partial = true  # stream-partial-output for incremental rendering
"""
    )
