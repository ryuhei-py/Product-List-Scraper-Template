# Testing - Product List Scraper Template

This document outlines the testing strategy and how to run and extend the tests.

---

## 1. Testing goals

This section states what the test suite is meant to ensure.

The test suite aims to ensure:

- **Correctness** of core behavior:
  - HTTP fetching and retry behavior
  - HTML parsing for list and detail pages
  - CSV and JSON exports
  - Data validation logic
- **Stability** of the template:
  - Changes to one component do not break others
  - Refactoring remains safe
- **Confidence for clients**:
  - The presence of tests demonstrates engineering discipline and quality

---

## 2. Test suite structure

This section describes how tests are organized.

The tests live under `tests/`:

```text
tests/
├─ conftest.py
├─ test_fetcher.py
├─ test_parser.py
├─ test_exporter.py
└─ test_validator.py
```

### 2.1 test_fetcher.py

Covers:

- Successful HTTP requests
- Retry behavior on transient errors (e.g., 5xx)
- No retry on 4xx client errors
- Proper exception (`FetchError`) on final failure
- Uses mocking to avoid real network calls.

### 2.2 test_parser.py

Covers:

ListPageParser:

- Extracting product URLs from list-page HTML
- Handling cases with no matching links gracefully

DetailPageParser:

- Extracting fields like title, price, image_url, description
- Handling missing fields (e.g., returning None or empty values)
- Ensuring changes in selectors are easy to test

HTML snippets are kept small and deterministic.

### 2.3 test_exporter.py

Covers:

CSV export:

- Proper header ordering
- Handling missing keys (empty cells)
- Behavior when no records are present

JSON export:

- Round-trip correctness: dumping and loading returns the same list structure

Temporary directories (e.g., `tmp_path` fixture) are used to avoid polluting the repository.

### 2.4 test_validator.py

Covers:

`validate_records`:

- Correct totals and missing counts across different scenarios
- Handling of empty record lists

`format_quality_report`:

- Produces a readable multi-line string
- Includes key indicators like total record count and missing counts

---

## 3. Running tests

This section explains how to run the tests.

From the project root, with your virtual environment activated:

```bash
pytest
```

Common variations:

Quiet mode:

```bash
pytest -q
```

Run a single test file:

```bash
pytest tests/test_parser.py
```

Run a specific test function:

```bash
pytest tests/test_parser.py::test_list_parser_basic
```

---

## 4. Adding new tests

This section provides guidelines for adding tests.

When you extend the template (e.g. new modules, new features), follow these guidelines:

- Mirror the module structure:  
  For a new module `src/product_scraper/something.py`, create `tests/test_something.py`.
- Keep tests focused and deterministic:  
  Mock network calls and external services. Use small, fixed HTML or JSON fixtures where necessary.
- Test the public API:  
  Prefer testing public functions and classes. Avoid relying on private implementation details.
- Document intent:  
  Use clear test names and docstrings or comments when the behavior is non-obvious.

---

## 5. CI integration

This section notes how CI runs the tests.

A basic GitHub Actions workflow (`.github/workflows/ci.yml`) can run the test suite on every push and pull request.

Typical steps:

- Check out the repository
- Set up Python
- Install dependencies
- Run pytest

This ensures that:

- New changes are automatically validated
- Clients can view the CI status as an additional quality signal
