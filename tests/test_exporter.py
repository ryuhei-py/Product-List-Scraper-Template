import csv
import json

from product_scraper.exporter import export_to_csv, export_to_json


def test_export_to_csv_writes_records(tmp_path):
    output_path = tmp_path / "products.csv"
    records = [
        {"id": "p1", "title": "Item 1", "price": "100"},
        {"id": "p2", "title": "Item 2", "price": "200"},
    ]

    export_to_csv(records, output_path)

    assert output_path.exists()
    with output_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert rows[0] == ["id", "title", "price"]
    assert rows[1] == ["p1", "Item 1", "100"]
    assert rows[2] == ["p2", "Item 2", "200"]


def test_export_to_csv_handles_missing_field(tmp_path):
    output_path = tmp_path / "products.csv"
    records = [
        {"id": "p1", "title": "Item 1", "price": "100"},
        {"id": "p2", "title": "Item 2"},  # price missing
    ]

    export_to_csv(records, output_path)

    with output_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert rows[0] == ["id", "title", "price"]
    assert rows[1] == ["p1", "Item 1", "100"]
    assert rows[2] == ["p2", "Item 2", ""]


def test_export_to_csv_with_no_records_creates_empty_file(tmp_path):
    output_path = tmp_path / "products.csv"

    export_to_csv([], output_path)

    assert output_path.exists()
    assert output_path.stat().st_size == 0


def test_export_to_json_writes_records(tmp_path):
    output_path = tmp_path / "products.json"
    records = [
        {"id": "p1", "title": "Item 1", "price": "100"},
        {"id": "p2", "title": "Item 2", "price": "200"},
    ]

    export_to_json(records, output_path)

    assert output_path.exists()
    with output_path.open(encoding="utf-8") as f:
        data = json.load(f)

    assert data == records
