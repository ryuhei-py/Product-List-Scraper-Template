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
    - Each target must be a mapping with a non-empty "name".
    - Names must be unique across targets.
    - Supports two modes:
      * Detail-follow mode (default): requires non-empty "list_url", "link_selector",
        and non-empty mapping "detail_selectors".
      * List-only mode: triggered if "item_selector" or "item_fields" is present.
        Requires non-empty "list_url", non-empty "item_selector", and non-empty
        mapping "item_fields".
    - Selector mappings must contain non-empty string values.
    """
    targets = config.get("targets")
    if not isinstance(targets, list) or not targets:
        raise ConfigError("Config must contain a non-empty 'targets' list.")
    seen_names: set[str] = set()
    validated: list[Dict[str, Any]] = []
    for index, target in enumerate(targets):
        if not isinstance(target, dict):
            raise ConfigError(f"Target at index {index} must be a mapping.")
        name = target.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError(f"Target at index {index} must have a non-empty 'name'.")
        if name in seen_names:
            raise ConfigError(f"Duplicate target name '{name}' found.")
        seen_names.add(name)

        list_url = target.get("list_url")
        if not isinstance(list_url, str) or not list_url.strip():
            raise ConfigError(
                f"Target at index {index} is missing a non-empty 'list_url'."
            )

        has_item_mode = ("item_selector" in target) or ("item_fields" in target)
        if has_item_mode:
            item_selector = target.get("item_selector")
            item_fields = target.get("item_fields") or {}
            if not isinstance(item_selector, str) or not item_selector.strip():
                raise ConfigError(
                    f"Target at index {index} is missing a non-empty 'item_selector'."
                )
            if not isinstance(item_fields, dict) or not item_fields:
                raise ConfigError(
                    f"Target at index {index} has invalid or empty 'item_fields'."
                )
            for key, selector in item_fields.items():
                if not isinstance(selector, str) or not selector.strip():
                    raise ConfigError(
                        f"Target at index {index} has empty selector for field '{key}'."
                    )
        else:
            link_selector = target.get("link_selector")
            detail_selectors = target.get("detail_selectors") or {}
            if not isinstance(link_selector, str) or not link_selector.strip():
                raise ConfigError(
                    f"Target at index {index} is missing a non-empty 'link_selector'."
                )
            if not isinstance(detail_selectors, dict) or not detail_selectors:
                raise ConfigError(
                    f"Target at index {index} has invalid or empty 'detail_selectors'."
                )
            for key, selector in detail_selectors.items():
                if not isinstance(selector, str) or not selector.strip():
                    raise ConfigError(
                        f"Target at index {index} has empty selector for field '{key}'."
                    )
        validated.append(target)
    return validated
