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
from product_scraper.fetcher import FetchError, Fetcher, FileFetcher
from product_scraper.parser import DetailPageParser, ListItemsParser, ListPageParser
from product_scraper.validator import format_quality_report, validate_records


logger = logging.getLogger(__name__)


def _resolve_output_path(
    arg_output: str | None,
    settings: Mapping[str, Any] | None,
    fallback: str,
) -> Path:
    """
    Resolve output path using CLI arg first, then settings.output, then fallback.
    """
    if arg_output:
        return Path(arg_output)

    output_settings = (settings or {}).get("output", {}) or {}
    directory = output_settings.get("directory")
    csv_filename = output_settings.get("csv_filename")

    if directory or csv_filename:
        filename = csv_filename or Path(fallback).name
        if directory:
            return Path(directory) / filename
        return Path(filename)

    return Path(fallback)


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
    fetcher_class: type[Fetcher] | None = None,
) -> int:
    """Run the scraping pipeline for a single target config."""
    list_url = target_config.get("list_url")
    link_selector = target_config.get("link_selector")
    detail_selectors = target_config.get("detail_selectors") or {}
    item_selector = target_config.get("item_selector")
    item_fields = target_config.get("item_fields") or {}

    if not list_url:
        print("Config must include list_url.", file=sys.stderr)
        return 1

    list_only_mode = bool(item_selector or item_fields)
    if list_only_mode:
        if not item_selector or not item_fields:
            print(
                "List-only mode requires item_selector and item_fields.",
                file=sys.stderr,
            )
            return 1
    else:
        if not link_selector:
            print("Config must include link_selector.", file=sys.stderr)
            return 1

    http_settings = (settings or {}).get("http", {}) or {}
    timeout = float(http_settings.get("timeout", 10.0))
    max_retries = int(http_settings.get("max_retries", 3))
    user_agent = http_settings.get("user_agent")
    delay_seconds = float(http_settings.get("delay_seconds", 0.0))
    retry_backoff_seconds = float(http_settings.get("retry_backoff_seconds", 0.0))
    retry_backoff_multiplier = float(http_settings.get("retry_backoff_multiplier", 2.0))
    retry_jitter_seconds = float(http_settings.get("retry_jitter_seconds", 0.0))

    headers: dict[str, str] = {}
    if user_agent:
        headers["User-Agent"] = str(user_agent)

    fetcher_cls = fetcher_class or Fetcher
    fetcher = fetcher_cls(
        timeout=timeout,
        max_retries=max_retries,
        headers=headers or None,
        retry_backoff_seconds=retry_backoff_seconds,
        retry_backoff_multiplier=retry_backoff_multiplier,
        retry_jitter_seconds=retry_jitter_seconds,
    )
    list_parser = (
        ListPageParser(link_selector=link_selector) if not list_only_mode else None
    )
    detail_parser = (
        DetailPageParser(selectors=detail_selectors) if not list_only_mode else None
    )
    list_items_parser = (
        ListItemsParser(item_selector=item_selector, field_selectors=item_fields)
        if list_only_mode
        else None
    )

    # 1) Fetch list page
    try:
        list_html = fetcher.get(list_url)
    except FetchError as exc:
        print(f"Failed to fetch list page: {exc}", file=sys.stderr)
        return 1

    records: list[dict[str, Any]] = []

    if list_only_mode and list_items_parser is not None:
        items = list_items_parser.parse_items(list_html)
        if limit is not None:
            items = items[:limit]
        for record in items:
            record["source_list_url"] = list_url
            for key, value in list(record.items()):
                if key.endswith("_url") and isinstance(value, str) and value:
                    record[key] = urljoin(list_url, value)
        records = items
        logger.info("Parsed %s list-only records", len(records))
    else:
        # 2) Parse product URLs from list page
        product_urls = list_parser.parse_list(list_html)
        if limit is not None:
            product_urls = product_urls[:limit]

        logger.info("Found %s product URLs", len(product_urls))

        # 3) Fetch and parse each detail page
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
            record["detail_url"] = full_url
            record["source_list_url"] = list_url
            for key, value in list(record.items()):
                if not key.endswith("_url"):
                    continue
                if isinstance(value, str) and value:
                    record[key] = urljoin(full_url, value)
            records.append(record)
            if delay_seconds > 0:
                time.sleep(delay_seconds)

        logger.info("Parsed %s records", len(records))

    if not records:
        print("No records parsed; aborting.", file=sys.stderr)
        return 1

    # 4) Export to CSV (unless dry-run)
    validation_settings = (settings or {}).get("validation", {}) or {}
    validation_enabled = bool(validation_settings.get("enabled", True))

    if validation_enabled:
        summary = validate_records(records)
        report = format_quality_report(summary)
        print(report)
    else:
        logger.info("Validation disabled; skipping quality report.")

    if not dry_run:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        export_to_csv(records, output_path)
        logger.info("Wrote CSV to %s", output_path)
    else:
        logger.info("Dry run enabled; skipping export.")
        logger.info(
            "Parsed %s records (sample: %s)",
            len(records),
            records[0] if records else {},
        )

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
        default=None,
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
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in offline demo mode using bundled HTML fixtures.",
    )

    args = parser.parse_args(argv)

    load_dotenv()

    if args.demo:
        repo_root = Path(__file__).resolve().parent.parent.parent
        fixtures_dir = repo_root / "fixtures"
        output_default = "sample_output/products.demo.csv"
        settings: Mapping[str, Any] | None = {}
        demo_target = {
            "name": "demo",
            "list_url": (fixtures_dir / "list.html").as_uri(),
            "link_selector": "a.product-link",
            "detail_selectors": {
                "title": "h1.product-title",
                "price": ".price",
                "image_url": "img.product-image",
                "description": ".description",
            },
        }
        output_path = _resolve_output_path(args.output, settings, output_default)
        configure_logging(settings)
        return run_pipeline(
            target_config=demo_target,
            output_path=output_path,
            limit=args.limit,
            dry_run=args.dry_run,
            settings=settings,
            fetcher_class=FileFetcher,
        )

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
            print(
                f"No target with name '{target_name}' found in config.", file=sys.stderr
            )
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
    output_path = _resolve_output_path(
        args.output,
        settings,
        fallback="sample_output/products.csv",
    )

    return run_pipeline(
        target_config=target,
        output_path=output_path,
        limit=args.limit,
        dry_run=args.dry_run,
        settings=settings,
    )


if __name__ == "__main__":
    raise SystemExit(main())
