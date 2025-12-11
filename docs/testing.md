# Testing ? Product List Scraper Template

This document outlines the **testing strategy**, how to **run** the tests, and how to **extend** them when you add features or adapt the template for new projects.

The test suite is meant to give both you and your clients confidence that the scraper behaves correctly and can evolve safely over time.

---

## Testing goals

The test suite is designed to ensure:

1. **Correctness of core behavior**
   - HTTP fetching and retry behavior.
   - HTML parsing for list and detail pages.
   - CSV (and optional JSON) exports.
   - Data validation logic and quality reporting.
   - Basic CLI orchestration (end-to-end smoke tests).
   - Configuration loading and validation.
2. **Stability of the template**
   - Changes to one component do not unintentionally break others.
   - Refactoring (e.g., internal cleanup or performance tweaks) remains safe.
   - Regression bugs can be detected early.
3. **Confidence for clients and reviewers**
   - The presence of tests demonstrates engineering discipline and quality.
   - It is easy to show that behavior is verified under small, deterministic scenarios.
   - CI status is visible on GitHub as an additional quality signal.

---

## Test suite structure

All tests live under the `tests/` directory:

```text
tests/
├─ conftest.py
├─ test_fetcher.py
├─ test_parser.py
├─ test_exporter.py
├─ test_validator.py
├─ test_config.py
└─ test_cli.py
```

Each file focuses on a specific part of the system.

### test_fetcher.py

#### Scope

Covers the Fetcher class in `src/product_scraper/fetcher.py`.

#### Typical behaviors tested

- Successful HTTP requests (happy path).
- Retry behavior on transient errors (e.g., 5xx or connection errors).
- No retry on non-retryable errors (e.g., certain 4xx responses), depending on policy.
- Correct raising of `FetchError` when retries are exhausted.
- Proper handling of timeouts.

#### Implementation notes

- Network calls are not performed against real endpoints.
- Tests use mocking / monkeypatching of the underlying HTTP client.
- Timeouts and retries are tested with synthetic scenarios to keep tests fast and deterministic.

### test_parser.py

#### Scope

Covers `ListPageParser` and `DetailPageParser` in `src/product_scraper/parser.py`.

#### ListPageParser

Tests focus on:

- Extracting product URLs from list-page HTML using `link_selector`.
- Handling pages with:
  - Multiple links.
  - No matching links (result should be an empty list).
- Robustness against minor HTML irregularities.
- Ensuring the parser returns raw href strings; URL normalization is done in the CLI.

#### DetailPageParser

Tests focus on:

- Extracting core fields:
  - `title`, `price`, `image_url`, `description`.
- Ensuring missing selectors or missing elements yield `None` values in the result.
- Supporting extra fields:
  - When `detail_selectors` includes additional keys (e.g., `sku`, `category`), those fields are also extracted.
- Image URL extraction behavior:
  - Prefer the `src` attribute when present.
  - Fall back to element text if `src` is missing.

HTML snippets in tests are:

- Small and self-contained.
- Deterministic (no network or external dependencies).
- Easy to modify when page structures change.

### test_exporter.py

#### Scope

Covers CSV (and optional JSON) export functions in `src/product_scraper/exporter.py`.

#### Typical behaviors tested

- CSV export:
  - Column ordering derived from the first record.
  - Correct handling of:
    - Missing keys (empty cells or `None`).
    - Mixed records with different sets of fields.
  - Behavior when the records list is empty (e.g., creating a file with only headers or not creating a file, depending on design).
- JSON export (if implemented):
  - Round-trip correctness:
    - Dumping a list of dicts to JSON and loading it back yields the same structure.
  - Handling of `None` / empty values.

#### Implementation notes

- Tests use temporary directories via `tmp_path` or similar fixtures.
- No files are written into the repository itself during testing.
- After each export, tests assert that:
  - The expected files exist.
  - Their contents follow the expected format (e.g., correct headers, number of lines).

### test_validator.py

#### Scope

Covers validation logic in `src/product_scraper/validator.py`.

#### Typical behaviors tested

- Validation of a list of records:
  - Correct counting of total records.
  - Correct counting of missing values per field.
  - Handling of an empty record list (should not crash).
- Quality report formatting:
  - `format_quality_report` (or equivalent function) produces a human-readable multi-line string.
  - The report includes:
    - Total record count.
    - Per-field missing counts.
    - Any relevant indicators used in operations (e.g., percentages, warnings).

Tests are designed to ensure that changes in record structure or validation thresholds are easy to reason about and do not accidentally break the report format.

### test_config.py

#### Scope

Covers configuration loading and validation functions in `src/product_scraper/config.py`.

#### Typical behaviors tested

- `load_targets_config`:
  - Successful loading of a valid YAML file.
  - Handling of empty files or missing keys gracefully, when appropriate.
- `get_targets_from_config` and any config validation helpers:
  - Reject configs without a `targets` key.
  - Reject configs where `targets` is not a non-empty list.
  - Reject targets that:
    - Are not mappings (dict-like).
    - Lack required fields (`list_url`, `link_selector`).
    - Have `detail_selectors` not defined as a mapping.
  - Accept valid configs and return a normalized list of targets.
- `load_settings_config`:
  - Returns an empty dict when the file does not exist.
  - Loads a mapping when the file exists.
  - Raises an error when the top-level YAML structure is not a mapping (for safety).

These tests protect you against subtle config regressions that might otherwise only be caught at runtime in production.

### test_cli.py

#### Scope

Covers high-level CLI behavior in `src/product_scraper/cli.py`.

#### Typical behaviors tested

- A “smoke test” for `run_pipeline` with:
  - A fake Fetcher (via monkeypatch).
  - Small, deterministic HTML for list and detail pages.
  - An in-memory target configuration.
  - A temporary output path.
- Running the pipeline end-to-end for a simple target:
  - Ensuring that:
    - Exit code is 0 on success.
    - The output CSV file is created and non-empty (when not in `--dry-run` mode).
- Verifying that `--dry-run`-equivalent behavior:
  - Skips writing the output file.
  - Still runs parsing and (optionally) validation.
- Ensuring that config validation errors:
  - Produce a non-zero exit code.
  - Print a clear error message to stderr.

#### Implementation notes

- Tests avoid actual network calls and disk side-effects beyond the temporary directory.
- The CLI is exercised via its public functions (e.g., `run_pipeline`), not via actual subprocess calls.
- This keeps tests fast, deterministic, and easy to run repeatedly.

---

## Running tests

### Basic usage

From the project root, with your virtual environment activated, run the full test suite:



```bash
pytest
```

This will:

- Discover all tests under `tests/`.
- Run them with the default pytest configuration supplied by `pyproject.toml`.

### Common variations

Run tests in quiet mode:



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

Run with verbose output and show names of all tests:



```bash
pytest -v
```

### Integration with tooling

If you use additional tools (e.g., `ruff`, coverage plugins, or IDE integrations):

- Configure them to use the same virtual environment.
- Keep the main invocation (`pytest`) simple; advanced options can be specified in `pyproject.toml` or tool-specific config files.

---

## Adding new tests

When you extend the template (e.g., new modules, new features), follow these guidelines.

### Mirror the module structure

For a new module:

- `src/product_scraper/something.py`

Create a corresponding test module:

- `tests/test_something.py`

This simple rule keeps the test suite navigable and helps future contributors find relevant tests quickly.

### Keep tests focused and deterministic

- Avoid real network calls:
  - Use mocking or monkeypatching for HTTP clients.
  - Provide small HTML/JSON strings directly in tests, or load them from static fixtures if needed.
- Avoid slow tests:
  - Do not introduce actual sleep calls; simulate delays via configuration or mocks.
- Avoid non-deterministic behavior:
  - Randomness should be either mocked or seeded.
  - External services or APIs should always be replaced with predictable stubs.

### Test the public API

Prefer testing public functions and classes exposed by the package.

Avoid relying on private implementation details (e.g., helper functions with leading underscores) unless you have strong reasons and document them clearly.

This approach allows internals to be refactored without breaking the tests.

### Document the intent

- Use clear test names (e.g., `test_list_parser_ignores_links_without_href`).
- Add docstrings or inline comments when behavior is not obvious.
- When fixing a bug, consider adding a test that would have failed before the fix.

This makes the test suite act as executable documentation of the system’s behavior.

---

## Test data and fixtures

### HTML snippets

For parser tests, use:

- Small, self-contained HTML strings.
- Only the minimal markup needed for the behavior you are testing.
- Clear structure so that CSS selectors are easy to verify and update.

If you find yourself copying large HTML documents, consider:

- Extracting only the relevant parts.
- Using separate fixture files if some complexity is genuinely needed.

### Temporary files and directories

Use pytest fixtures like `tmp_path`:

- To create temporary directories and files for exporter tests.
- To avoid writing into the repository tree.
- To ensure that each test runs in isolation.

### Shared fixtures (`conftest.py`)

The `tests/conftest.py` file can:

- Define shared fixtures (e.g., sample HTML for parsers, pre-configured target dictionaries).
- Provide reusable mocks or helper functions.
- Configure pytest options globally (if needed).

Keep `conftest.py` small and focused; avoid complex logic that makes tests harder to read.

---

## CI integration

A basic GitHub Actions workflow (`.github/workflows/ci.yml`) is set up to:

- Check out the repository.
- Set up a suitable Python version.
- Install dependencies (from `requirements.txt`).
- Optionally run linters (e.g., `ruff`).
- Run the test suite with `pytest`.

This ensures that:

- Every push and pull request is automatically validated.
- Test failures are detected early.
- The CI badge on the README provides an at-a-glance indication of project health for clients and reviewers.

If you extend the project (e.g., add new dependencies, new commands), remember to update the CI workflow as needed.

---

## Recommended workflows

### During development

Write or update tests first when adding or changing behavior.

Run:



```bash
pytest
```

frequently (or a subset via `pytest tests/test_xxx.py`).

Fix failing tests or adjust them if expected behavior changes (aligned with design decisions).

### Before committing

Run `pytest` locally and ensure all tests pass.

Optionally, run linting tools such as `ruff`:



```bash
ruff src tests
```

Check for obvious formatting or style issues.

### Before release / when presenting to a client

Run the full test suite in a clean environment (e.g., new virtualenv).

Confirm that CI is green for the branch or commit you want to present.

Be prepared to point to:

- The test coverage of critical components.
- How failures would be detected and addressed.

---

## Summary

The test suite of the Product List Scraper Template is built to be:

- Comprehensive enough to protect core functionality.
- Lightweight enough to run quickly during development and in CI.
- Structured enough to be easily extended as you adapt the template to new projects.

By mirroring the module structure, keeping tests deterministic, and integrating them into CI, you maintain a strong quality signal for both your own work and for clients who review this repository as part of your portfolio.
