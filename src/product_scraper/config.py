"""Configuration loading helpers for the scraper CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigError(Exception):
    """Raised when the scraper configuration is invalid."""


def load_targets_config(path: str | Path) -> Dict[str, Any]:
    """Load YAML configuration describing scraping targets."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def load_settings_config(path: str | Path) -> Dict[str, Any]:
    """
    Load an optional YAML settings file.

    Returns an empty dict if the file does not exist or is empty.
    Raises ValueError if the top-level YAML object is not a mapping.
    """
    settings_path = Path(path)
    if not settings_path.exists():
        return {}
    with settings_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("Settings config must be a mapping at the top level.")
    return data


def get_targets_from_config(config: Dict[str, Any]) -> list[Dict[str, Any]]:
    """
    Validate the top-level config and return a non-empty list of target mappings.

    Requirements:
    - config must contain a "targets" key.
    - "targets" must be a non-empty list.
    - Each target must be a mapping.
    - Each target must have non-empty "list_url" and "link_selector" values.
    - "detail_selectors" must be a mapping (may be empty).
    """
    targets = config.get("targets")
    if not isinstance(targets, list) or not targets:
        raise ConfigError("Config must contain a non-empty 'targets' list.")
    validated: list[Dict[str, Any]] = []
    for index, target in enumerate(targets):
        if not isinstance(target, dict):
            raise ConfigError(f"Target at index {index} must be a mapping.")
        if not target.get("list_url") or not target.get("link_selector"):
            raise ConfigError(
                f"Target at index {index} is missing 'list_url' or 'link_selector'."
            )
        detail_selectors = target.get("detail_selectors") or {}
        if not isinstance(detail_selectors, dict):
            raise ConfigError(
                f"Target at index {index} has non-mapping 'detail_selectors'."
            )
        validated.append(target)
    return validated
