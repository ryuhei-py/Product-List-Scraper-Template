"""Command-line interface to run the scraping pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urljoin

from dotenv import load_dotenv

from product_scraper.config import (
    ConfigError,
    get_targets_from_config,
    load_settings_config,
    load_targets_config,
)
from product_scraper.exporter import export_to_csv
from product_scraper.fetcher import FetchError, Fetcher
from product_scraper.parser import DetailPageParser, ListPageParser
from product_scraper.validator import format_quality_report, validate_records


logger = logging.getLogger(__name__)


def configure_logging(settings: Mapping[str, Any] | None) -> None:
    """
    Configure basic logging according to settings['logging']['level'].

    - Default level is INFO when nothing is specified.
    - If the level string is invalid, fall back to INFO.
    """
    logging_config = (settings or {}).get("logging", {}) or {}
    level_name = str(logging_config.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level)


def run_pipeline(
    target_config: dict[str, Any],
    output_path: Path,
    limit: int | None = None,
    dry_run: bool = False,
    settings: Mapping[str, Any] | None = None,
) -> int:
    """Run the scraping pipeline for a single target config."""
    list_url = target_config.get("list_url")
    link_selector = target_config.get("link_selector")
    detail_selectors = target_config.get("detail_selectors") or {}

    if not list_url or not link_selector:
        print("Config must include list_url and link_selector.", file=sys.stderr)
        return 1

    http_settings = (settings or {}).get("http", {}) or {}
    timeout = float(http_settings.get("timeout", 10.0))
    max_retries = int(http_settings.get("max_retries", 3))
    user_agent = http_settings.get("user_agent")
    delay_seconds = float(http_settings.get("delay_seconds", 0.0))

    headers: dict[str, str] = {}
    if user_agent:
        headers["User-Agent"] = str(user_agent)

    fetcher = Fetcher(
        timeout=timeout,
        max_retries=max_retries,
        headers=headers or None,
    )
    list_parser = ListPageParser(link_selector=link_selector)
    detail_parser = DetailPageParser(selectors=detail_selectors)

    # 1) Fetch list page
    try:
        list_html = fetcher.get(list_url)
    except FetchError as exc:
        print(f"Failed to fetch list page: {exc}", file=sys.stderr)
        return 1

    # 2) Parse product URLs from list page
    product_urls = list_parser.parse_list(list_html)
    if limit is not None:
        product_urls = product_urls[:limit]

    logger.info("Found %s product URLs", len(product_urls))

    # 3) Fetch and parse each detail page
    records: list[dict[str, Any]] = []
    base_url = list_url
    for url in product_urls:
        normalized = url.strip()
        if not normalized:
            continue

        if normalized.lower().startswith("http"):
            full_url = normalized
        else:
            full_url = urljoin(base_url, normalized)

        try:
            detail_html = fetcher.get(full_url)
        except FetchError as exc:
            print(f"Skipping {url}: {exc}", file=sys.stderr)
            continue

        record = detail_parser.parse_detail(detail_html)
        records.append(record)
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    logger.info("Parsed %s records", len(records))

    if not records:
        print("No records parsed; aborting.", file=sys.stderr)
        return 1

    # 4) Export to CSV (unless dry-run)
    if not dry_run:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        export_to_csv(records, output_path)
        logger.info("Wrote CSV to %s", output_path)
    else:
        logger.info("Dry run enabled; skipping export.")

    # 5) Validate and print quality report
    validation_settings = (settings or {}).get("validation", {}) or {}
    validation_enabled = bool(validation_settings.get("enabled", True))

    if validation_enabled:
        summary = validate_records(records)
        report = format_quality_report(summary)
        print(report)
    else:
        logger.info("Validation disabled; skipping quality report.")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run product list scraper pipeline.")
    parser.add_argument(
        "--config",
        default="config/targets.example.yml",
        help="Path to YAML configuration file.",
    )
    parser.add_argument(
        "--output",
        default="sample_output/products.csv",
        help="Path to output CSV file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of product detail pages to process.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing CSV output.",
    )
    parser.add_argument(
        "--target-name",
        help="Optional name of the target in the config to run. If omitted, the first target is used.",
    )

    args = parser.parse_args(argv)

    load_dotenv()

    try:
        config = load_targets_config(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load config: {exc}", file=sys.stderr)
        return 1

    try:
        targets = get_targets_from_config(config)
    except ConfigError as exc:
        print(f"Invalid config: {exc}", file=sys.stderr)
        return 1

    target_name = args.target_name
    if target_name:
        matches = [t for t in targets if t.get("name") == target_name]
        if not matches:
            print(f"No target with name '{target_name}' found in config.", file=sys.stderr)
            return 1
        target = matches[0]
    else:
        target = targets[0]

    try:
        settings = load_settings_config("config/settings.yml")
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load settings: {exc}", file=sys.stderr)
        return 1

    configure_logging(settings)
    output_path = Path(args.output)

    return run_pipeline(
        target_config=target,
        output_path=output_path,
        limit=args.limit,
        dry_run=args.dry_run,
        settings=settings,
    )


if __name__ == "__main__":
    raise SystemExit(main())
