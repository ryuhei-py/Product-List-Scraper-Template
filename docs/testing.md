# Testing Guide

This document explains how testing is structured in this repository, how to run tests locally and in CI, what the suite proves, and how to extend coverage safely when adapting this template to a new target.

---

## Why this repository emphasizes testing

Web scraping projects fail most often due to:
- configuration drift (invalid YAML, wrong mode shape, empty selectors)
- HTML structure changes that silently break extraction
- fragile network behavior (timeouts, retries, overload)
- unstable output schemas that break downstream consumers

This template addresses these risks with a deterministic, layered test suite that validates the pipeline end-to-end without relying on live third-party sites.

---

## Testing principles

### Deterministic by default (no live network)
The test suite intentionally avoids scraping real websites. All parsing and orchestration tests use:
- local HTML fixtures (`fixtures/`)
- inline HTML strings
- fake fetchers and dummy HTTP responses

This keeps tests:
- reproducible across machines
- stable in CI
- safe to run without unintentionally hitting external services

### Layered coverage (unit + orchestration)
Coverage is split into:
- **Unit tests** for modules (config, parser, fetcher, exporter, validator)
- **CLI tests** that validate orchestration wiring and pipeline behavior using fakes (still offline)

This structure makes it easy to identify failures and isolate regressions.

---

## Quickstart

### Install development dependencies
From the repository root:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
````

### Run lint and tests

```bash
python -m ruff check src tests
python -m pytest
```

### Optional: Excel export dependencies

The CLI exports CSV. An Excel exporter helper exists and is available via optional dependencies:

```bash
python -m pip install -e ".[excel]"
```

---

## Test suite overview

The `tests/` directory is organized by module responsibilities:

* `test_config.py` — configuration loading and schema validation
* `test_parser.py` — selector spec behavior and HTML parsing correctness
* `test_fetcher.py` — HTTP fetching logic, retry rules, and failure handling
* `test_exporter.py` — CSV/JSON export correctness and schema stability
* `test_validator.py` — quality report (missing field counts) correctness
* `test_cli.py` — offline pipeline/orchestration validation, demo behavior, and output path precedence

The suite is designed so that a clean `pytest` run provides high confidence that:

* config validation prevents common misruns
* parser logic matches the selector contract
* fetch retry rules are correct and not overly aggressive
* exports are stable and downstream-friendly
* CLI wiring behaves as documented

---

## What each test module verifies

### `tests/test_config.py` — configuration loading and validation

This module verifies the contract enforced by `product_scraper.config`:

* The top-level targets file must be a mapping and include a non-empty `targets` list.
* Each target must be a mapping with:

  * non-empty `name`
  * non-empty `list_url`
  * unique names across targets
* **List-only mode** requires:

  * `item_selector` (non-empty)
  * `item_fields` (non-empty mapping)
* **Detail-follow mode** requires:

  * `link_selector` (non-empty)
  * `detail_selectors` (non-empty mapping)
* Selector mappings must contain non-empty strings.
* Settings loading behavior:

  * missing settings file → empty dict
  * empty settings file → empty dict
  * non-mapping settings YAML → error

Why it matters:

* Most client-facing scraping failures start as configuration mistakes. Strict schema checks prevent silent failures and reduce debugging time.

---

### `tests/test_parser.py` — selector spec and parsing correctness

This module validates `product_scraper.parser`:

* List page link extraction (detail-follow mode) returns expected links.
* Detail page extraction returns expected field values.
* Missing selectors or missing elements produce `None` safely (no hard crashes).
* Extra selectors can be extracted and included.
* Selector spec behavior:

  * default text extraction
  * explicit `::text`
  * attribute extraction via `@attr` and `::attr(attr)`
* List-only parsing extracts multiple repeated items correctly.

Why it matters:

* HTML changes typically degrade data quality first (missing fields). Parser tests provide a fast regression signal using stable fixtures.

---

### `tests/test_fetcher.py` — HTTP behavior and retry rules

This module verifies `product_scraper.fetcher`:

* Successful GET returns response text.
* Retries occur on retryable server conditions and can succeed after recovery.
* Non-retryable 4xx are not retried (by design).
* Failure after exhausting attempts raises `FetchError`.

Key retry rules implemented:

* Retry on `429` and `5xx`.
* Do not retry other `4xx`.
* Backoff/jitter behavior is controlled by settings.

Why it matters:

* Correct retry behavior improves reliability while reducing the risk of overloading targets or creating “runaway” request loops.

---

### `tests/test_exporter.py` — export correctness and schema stability

This module verifies `product_scraper.exporter` behavior:

* CSV export writes correct rows.
* Missing fields are filled with empty strings (CSV-friendly).
* Export with no records creates an empty file.
* JSON exporter helper writes valid JSON output.
* CSV header stability is enforced via union-of-keys logic:

  * header begins with keys from the first record (preserving order)
  * newly discovered keys are appended as encountered

Why it matters:

* Downstream pipelines (spreadsheets, databases, BI tools) depend on stable schemas. A predictable header strategy prevents subtle breakage.

---

### `tests/test_validator.py` — quality report correctness

This module validates the quality-reporting utilities in `product_scraper.validator`:

* Missing-field counting across records
* All-fields-present case
* Empty input handling
* Report formatting includes the expected signals and values

Why it matters:

* Quality reports are an operational safety net. They surface regressions caused by HTML changes (e.g., sudden spikes in missing counts).

---

### `tests/test_cli.py` — orchestration and pipeline wiring (offline)

This module verifies `product_scraper.cli` end-to-end behavior without live network access:

* Pipeline smoke test using a fake fetcher
* URL normalization for any `*_url` fields
* Demo mode writes CSV using local fixtures
* List-only dry-run behavior
* Output path precedence when `--output` is omitted (settings-based defaults)

Why it matters:

* Orchestration issues often occur at boundaries between modules. CLI tests ensure the complete pipeline behavior matches documentation and remains safe to execute in CI.

---

## Fixtures and test doubles

### HTML fixtures (`fixtures/`)

This repo includes representative HTML under `fixtures/`, used for deterministic parsing and demo runs:

* `fixtures/list.html`
* `fixtures/detail_*.html`

Fixtures are intentionally small and focused on the elements being parsed.

### Fakes and dummy responses

* CLI tests use fake fetchers that return controlled HTML per URL.
* Fetcher tests use dummy response objects to simulate status codes and failures.

This approach validates logic without relying on external sites or unstable network conditions.

---

## Running tests effectively

### Common workflows

```bash
# Run the full suite
python -m pytest

# Run a single test module
python -m pytest tests/test_parser.py

# Run tests matching a substring
python -m pytest -k selector_spec

# Verbose output
python -m pytest -vv
```

### Linting

```bash
python -m ruff check src tests
```

---

## CI behavior

Continuous Integration runs the same checks as the recommended local workflow:

* Ruff linting (`ruff check src tests`)
* Pytest (`pytest`)

See `.github/workflows/ci.yml` for the exact CI definition.

Operational note:

* Local runs should match CI commands to avoid “works on my machine” drift.

---

## Extending tests when adding a new target

When adapting this template to a new client site, extend tests before relying on live runs.

### Recommended workflow

1. Capture representative HTML snapshots (list page and 1–2 detail pages), with permission where required.
2. Store them as fixtures or inline HTML in tests.
3. Configure a new target in your runtime targets file and validate locally using:

   * `--dry-run` and a small `--limit`
4. Add/extend parser tests to assert:

   * required fields are extracted correctly
   * link discovery works (detail-follow mode)
5. Add/extend CLI tests only if you changed orchestration or output schema.

### Rules of thumb

* Keep fixtures minimal and focused on what you parse.
* Avoid including sensitive or personal data in fixtures.
* Prefer deterministic assertions (exact strings, stable counts, stable headers).

---

## Troubleshooting

### “It runs but returns empty values”

* Verify selectors match the target HTML structure.
* Confirm selector spec usage:

  * use `@href`, `@src`, or `::attr(...)` for attributes
  * use default or `::text` for text nodes
* Use `--dry-run` with a small `--limit` to iterate quickly.

### “Config validation fails”

* Confirm the target matches the intended mode:

  * list-only requires `item_selector` + `item_fields`
  * detail-follow requires `link_selector` + `detail_selectors`
* Ensure selector mappings are non-empty strings.
* Ensure target `name` values are unique.

### “Fetcher retry tests fail”

* Confirm retryable status codes (429 and 5xx by design).
* Confirm “max retries” semantics align with the implemented attempt loop (bounded number of attempts).

### “CSV schema mismatch”

* Review union-of-keys behavior:

  * header starts with the first record’s keys
  * new keys are appended as encountered
* Ensure downstream expectations match this contract.

---

## Safety and compliance note for testing

* Tests and CI intentionally avoid live scraping of third-party sites.
* If you introduce live integration checks:

  * keep them opt-in (never run by default in CI)
  * ensure permission and ToS alignment
  * respect rate limits, delays, and operational safeguards
  * never commit secrets or sensitive data

---

## Related documentation

* `docs/architecture.md` — system design, data flow, failure modes
* `docs/CONFIG_GUIDE.md` — config schema, selector spec, validation rules
* `docs/operations.md` — scheduling, observability, runtime knobs
* `docs/SECURITY_AND_LEGAL.md` — responsible use and compliance guidance