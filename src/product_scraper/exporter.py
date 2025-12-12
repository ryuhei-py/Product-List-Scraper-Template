"""Helpers to export scraped product records to CSV or JSON."""

from __future__ import annotations

import csv
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable, Mapping


def export_to_csv(records: Iterable[Mapping[str, Any]], path: str | Path) -> None:
    """Export records to CSV using a stable union of keys across all records."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    iterator = iter(records)
    try:
        first = next(iterator)
    except StopIteration:
        with output_path.open("w", newline="", encoding="utf-8"):
            pass
        return

    ordered_keys: "OrderedDict[str, None]" = OrderedDict()
    for key in first.keys():
        ordered_keys[key] = None

    buffered_records = [first]
    for record in iterator:
        buffered_records.append(record)
        for key in record.keys():
            if key not in ordered_keys:
                ordered_keys[key] = None

    headers = list(ordered_keys.keys())
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for record in buffered_records:
            writer.writerow({key: record.get(key, "") for key in headers})


def export_to_json(records: Iterable[Mapping[str, Any]], path: str | Path) -> None:
    """Export records to a JSON array."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = list(records)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_to_excel(
    records: Iterable[Mapping[str, Any]],
    path: str | Path,
    sheet_name: str = "products",
) -> None:
    """Export records to an Excel file."""
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - defensive
        raise ImportError(
            "pandas is required for export_to_excel; please install it via 'pip install .[excel]'"
        ) from exc

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(list(records))
    df.to_excel(output_path, index=False, sheet_name=sheet_name)


if __name__ == "__main__":
    sample_records = [
        {"id": "p1", "title": "Sample Product", "price": "9.99"},
        {"id": "p2", "title": "Another Product", "price": "14.99"},
    ]
    export_to_csv(sample_records, Path("sample_output") / "products.sample.csv")
