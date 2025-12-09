"""Configuration loading helpers for the scraper CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_targets_config(path: str | Path) -> Dict[str, Any]:
    """Load YAML configuration describing scraping targets."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data
