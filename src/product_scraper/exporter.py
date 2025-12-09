"""Helpers to export scraped product records to CSV or JSON."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def export_to_csv(records: Iterable[Mapping[str, Any]], path: str | Path) -> None:
    """Export records to CSV.

    Writes an empty file when no records are provided.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    iterator = iter(records)
    try:
        first = next(iterator)
    except StopIteration:
        # Create zero-length file.
        with output_path.open("w", newline="", encoding="utf-8"):
            pass
        return

    headers = list(first.keys())
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        def write_row(record: Mapping[str, Any]) -> None:
            row = [record.get(key, "") for key in headers]
            writer.writerow(row)

        write_row(first)
        for record in iterator:
            write_row(record)


def export_to_json(records: Iterable[Mapping[str, Any]], path: str | Path) -> None:
    """Export records to a JSON array."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = list(records)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    sample_records = [
        {"id": "p1", "title": "Sample Product", "price": "9.99"},
        {"id": "p2", "title": "Another Product", "price": "14.99"},
    ]
    export_to_csv(sample_records, Path("sample_output") / "products.sample.csv")
