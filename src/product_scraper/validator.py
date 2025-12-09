"""Data quality validation helpers for scraped product records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Dict, List


def validate_records(records: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """
    Analyze a collection of record dictionaries and return a summary dict.

    Returns a mapping with total_records, fields, and missing_counts.
    """
    all_fields: set[str] = set()
    records_list: List[Mapping[str, Any]] = []

    for record in records:
        records_list.append(record)
        all_fields.update(record.keys())

    total_records = len(records_list)

    if total_records == 0:
        return {
            "total_records": 0,
            "fields": [],
            "missing_counts": {},
        }

    fields_sorted = sorted(all_fields)
    missing_counts: Dict[str, int] = {field: 0 for field in fields_sorted}

    for record in records_list:
        for field in fields_sorted:
            value = record.get(field, None)
            if value is None or value == "":
                missing_counts[field] += 1

    return {
        "total_records": total_records,
        "fields": fields_sorted,
        "missing_counts": missing_counts,
    }


def format_quality_report(summary: Mapping[str, Any]) -> str:
    """
    Render a human-readable quality report from the validate_records summary.
    """
    lines = [
        f"total_records: {summary.get('total_records', 0)}",
        f"fields: {', '.join(summary.get('fields', []))}",
        "missing_counts:",
    ]

    missing_counts = summary.get("missing_counts", {}) or {}
    for field, count in missing_counts.items():
        lines.append(f"  {field}: {count}")

    return "\n".join(lines)
