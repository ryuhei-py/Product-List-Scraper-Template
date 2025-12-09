"""Command-line interface to run the scraping pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

from product_scraper.config import load_targets_config
from product_scraper.exporter import export_to_csv
from product_scraper.fetcher import FetchError, Fetcher
from product_scraper.parser import DetailPageParser, ListPageParser
from product_scraper.validator import format_quality_report, validate_records


def run_pipeline(
    target_config: dict[str, Any],
    output_path: Path,
    limit: int | None = None,
    dry_run: bool = False,
) -> int:
    list_url = target_config.get("list_url")
    link_selector = target_config.get("link_selector")
    detail_selectors = target_config.get("detail_selectors") or {}

    if not list_url or not link_selector:
        print("Config must include list_url and link_selector.", file=sys.stderr)
        return 1

    fetcher = Fetcher()
    list_parser = ListPageParser(link_selector=link_selector)
    detail_parser = DetailPageParser(selectors=detail_selectors)

    try:
        list_html = fetcher.get(list_url)
    except FetchError as exc:
        print(f"Failed to fetch list page: {exc}", file=sys.stderr)
        return 1

    product_urls = list_parser.parse_list(list_html)
    if limit is not None:
        product_urls = product_urls[:limit]

    print(f"Found {len(product_urls)} product URLs")

    records: list[dict[str, Any]] = []
    for url in product_urls:
        try:
            detail_html = fetcher.get(url)
        except FetchError as exc:
            print(f"Skipping {url}: {exc}", file=sys.stderr)
            continue

        record = detail_parser.parse_detail(detail_html)
        records.append(record)

    print(f"Parsed {len(records)} records")

    if not records:
        print("No records parsed; aborting.", file=sys.stderr)
        return 1

    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        export_to_csv(records, output_path)
        print(f"Wrote CSV to {output_path}")
    else:
        print("Dry run enabled; skipping export.")

    summary = validate_records(records)
    report = format_quality_report(summary)
    print(report)

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

    args = parser.parse_args(argv)

    try:
        config = load_targets_config(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load config: {exc}", file=sys.stderr)
        return 1

    targets = config.get("targets")
    if not targets or not isinstance(targets, list):
        print("Config must contain a 'targets' list.", file=sys.stderr)
        return 1

    target = targets[0]
    output_path = Path(args.output)

    return run_pipeline(
        target_config=target,
        output_path=output_path,
        limit=args.limit,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
