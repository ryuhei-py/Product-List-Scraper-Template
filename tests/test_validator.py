from product_scraper.validator import format_quality_report, validate_records


def test_validate_records_basic_missing_fields():
    records = [
        {"id": "p1", "title": "Item 1", "price": "100"},
        {"id": "p2", "title": "Item 2", "price": None},
        {"id": "p3", "title": "Item 3"},  # price missing
    ]

    summary = validate_records(records)

    assert summary["total_records"] == 3
    assert summary["fields"] == ["id", "price", "title"]
    assert summary["missing_counts"]["id"] == 0
    assert summary["missing_counts"]["title"] == 0
    assert summary["missing_counts"]["price"] == 2


def test_validate_records_all_fields_present():
    records = [
        {"id": "p1", "title": "A", "price": "10"},
        {"id": "p2", "title": "B", "price": "20"},
    ]

    summary = validate_records(records)

    assert summary["total_records"] == 2
    assert summary["fields"] == ["id", "price", "title"]
    assert all(count == 0 for count in summary["missing_counts"].values())


def test_validate_records_empty():
    summary = validate_records([])

    assert summary["total_records"] == 0
    assert summary["fields"] == []
    assert summary["missing_counts"] == {}


def test_format_quality_report_contains_expected_text():
    records = [
        {"id": "p1", "title": "Item 1"},
        {"id": "p2", "title": "Item 2", "price": ""},
    ]
    summary = validate_records(records)

    report = format_quality_report(summary)

    assert isinstance(report, str)
    assert "total_records" in report
    assert "fields" in report
    assert "missing_counts" in report
    assert "price" in report
    assert "2" in report  # price missing count should be 2
