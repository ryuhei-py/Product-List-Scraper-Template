# Testing guide
This document explains the testing strategy for the Product List Scraper Template, how to run tests locally, and how to extend the test suite safely when adapting the template for client work.

Goals:
- Ensure correctness of parsing, config validation, exporting, and CLI orchestration.
- Keep tests deterministic and fast (no live network calls).
- Provide confidence that config-only changes will not break core behavior.

---

## Test philosophy
This section outlines the testing approach.

- Unit tests validate small, pure components (parsers, exporter logic, config validation).
- CLI tests validate orchestration and integration boundaries using mocked fetchers.
- No live scraping in tests to avoid flaky failures and accidental policy violations.

The guiding principle is: tests should fail only when behavior changes, not when the internet changes.

---

## Running tests locally
This section explains how to run checks.

### Install dev dependencies

# Install the package in editable mode
```bash
pip install -e .
```

### Run linting and tests

# Lint the code
```bash
ruff check src tests
```

# Run the test suite
```bash
pytest
```

### Optional Excel support during development

# Install Excel extras
```bash
pip install -e ".[excel]"
```

---

## What is covered by tests
This section lists coverage per test module.

### `tests/test_config.py`
- Validates configuration parsing and schema rules, including:
  - Target list structure (`targets:` must be a list).
  - Required keys (`name`, `list_url`).
  - Mode detection and mode-specific requirements:
    - List-only mode requires `item_selector` and non-empty `item_fields`.
    - Detail-follow mode requires `link_selector` and non-empty `detail_selectors`.
  - Selector strings must be non-empty.
  - Target names must be unique.
- These tests should catch most “bad YAML” issues before runtime.

### `tests/test_parser.py`
- Validates HTML parsing behavior for:
  - Selector spec syntax (plain text, `@attr`, `::attr(name)`, `::text`).
  - List-only parsing (`ListItemsParser.parse_items`).
  - Detail-follow parsing (`ListPageParser.parse_links` and `DetailPageParser.parse_detail`).
- All parser tests use static HTML snippets embedded in the test.

### `tests/test_fetcher.py`
- Validates the HTTP layer without real network calls, typically by mocking:
  - Success responses.
  - Retryable failures (for example, 429 and 5xx).
  - Non-retryable failures (for example, other 4xx).
  - Session usage / call paths (depending on implementation).
- The test suite ensures:
  - Retry counts are respected.
  - Exceptions are converted into `FetchError` with URL/status context.
  - No test sleeps (defaults should avoid backoff delays).

### `tests/test_exporter.py`
- Validates output serialization, especially:
  - CSV export and the stable union-of-keys header policy.
  - Correct mapping of missing keys to empty cells.
- Optional:
  - If JSON export has helpers, tests may validate JSON shape.
  - Excel export is usually tested lightly (or behind optional dependencies) to keep CI stable.

### `tests/test_cli.py`
- Validates CLI orchestration using mocked fetchers and temporary output paths:
  - `--dry-run` produces no output file and exits cleanly.
  - `--limit` limits record count.
  - Mode behaviors:
    - List-only mode parses items and normalizes `*_url` fields against `list_url`.
    - Detail-follow mode adds `detail_url` and normalizes URL fields appropriately.
  - Configuration errors cause non-zero exit codes and helpful messages.

---

## No live network calls
This section emphasizes keeping tests offline.

Tests must never hit real targets. This is both a reliability practice and a compliance/safety practice. When you need to test scraping behavior:

- Copy a representative HTML snippet into a fixture or string.
- Validate selectors against that snippet.
- Mock the fetcher to return that HTML.

---

## Extending tests when adding a new client target
This section describes extending coverage for new targets.

When adapting this template for a specific site, you typically change `config/targets.yml`, selectors, and output field names. Recommended steps:

- Add or update HTML fixtures (small snippets) that reflect the target’s structure.
- Add a parser unit test that validates the selectors you plan to ship.
- Add a CLI test that:
  - Mocks list HTML (and detail HTML if detail-follow).
  - Runs the CLI in dry-run or temp-output mode.
  - Asserts record keys and a few values.

This approach is faster than repeated manual scraping runs and prevents regressions.

---

## Debugging failing tests
This section lists common failure types and fixes.

Ruff failures  
Run: `ruff check src tests`  
Typical causes: unused imports, formatting/style issues, inconsistent typing. Fix style issues before interpreting logic failures.

Parser failures  
Common causes: selector specs changed; HTML fixtures no longer match parser behavior; attr/text mode interpretation changed. Fix by confirming selector specs (`@attr`, `::attr()`, `::text`) and verifying the fixture HTML; adjust tests only when behavior changes intentionally.

CLI failures  
Common causes: CLI flag changes; output behavior changed (for example, union-of-keys headers or new trace fields); mode detection logic changed. Fix by keeping CLI options backward compatible where possible; updating tests to match intended behavior; ensuring `--dry-run` and `--limit` remain stable.

Fetcher failures  
Common causes: patch target changed (for example, `requests.get` vs `session.get`); retry policy expanded (for example, include 429/5xx). Fix by patching the correct call site and asserting behavior rather than internal implementation details.

---

## CI expectations
This section describes CI checks.

CI should run:

# Lint the code
```bash
ruff check src tests
```

# Run tests
```bash
pytest
```

All tests should pass without network access, on a clean environment, with minimal optional dependencies (Excel deps should be optional).

---

## Recommended developer workflow
This section lists a suggested workflow.

Before committing:

# Lint and test
```bash
ruff check src tests
pytest
```

Before opening a PR:
- Ensure you added tests for any new parsing logic or schema changes.
- Ensure your config examples still validate.
- If you changed exporter behavior, update tests accordingly.

---

## Where to go next
This section links to related docs.

- `docs/CONFIG_GUIDE.md` for config + selector syntax.
- `docs/architecture.md` for module boundaries and data contracts.
- `docs/operations.md` for runtime tuning and troubleshooting.
- `docs/SECURITY_AND_LEGAL.md` for compliance and safe scraping practices.

---

_Last updated: 2025-12-12_
