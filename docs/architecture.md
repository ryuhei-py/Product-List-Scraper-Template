# Architecture

This document explains the architecture of **Product-List-Scraper-Template**: its execution modes, core modules, configuration contracts, data flow, reliability controls, and extension points. The goal is to make the codebase easy to understand, verify, and adapt to new targets with minimal changes.

---

## Purpose and scope

### What this repository provides
A reusable, config-driven scraping template that extracts product data from:
- a **list page** (list-only mode), or
- a **list page + linked detail pages** (detail-follow mode),

and produces a consistent, traceable dataset (CSV via CLI).

### What this document covers
- System overview and design goals
- Component boundaries and responsibilities
- End-to-end data flow in both execution modes
- Configuration schema and validation rules
- Data contract (record shape, traceability, URL normalization)
- Error handling and exit behavior
- Reliability/politeness controls (timeouts, attempts, backoff, delays)
- Testing/CI strategy (deterministic, no live network calls)
- Extensibility roadmap (what to add next and where)

### Non-goals (explicit boundaries)
- **JavaScript-rendered scraping** (no Playwright/Selenium browser automation)
- **Built-in pagination** (single list URL per run unless extended)
- **Authentication/session orchestration** (cookies/login flows not implemented)
- **Anti-bot bypass techniques** (no fingerprinting, CAPTCHA solving, evasion tooling)
- **Multi-format CLI export** (CLI exports CSV; JSON/Excel helpers exist but are not wired to CLI flags)

---

## System overview

### High-level design goals
1. **Config-first adaptation**  
   New targets should be added primarily through YAML selectors, not code rewrites.

2. **Deterministic, portfolio-grade verification**  
   Tests and demo runs should not rely on live network calls, making results reproducible.

3. **Operational safety knobs**  
   Provide tunable settings for timeout, attempts, retry backoff/jitter, politeness delays, and user-agent.

4. **Traceability and correctness signals**  
   Each record should preserve where it came from, and runs should surface quality signals (missing-field counts).

### Key capabilities
- Two scraping modes:
  - **Mode A: List-only**
  - **Mode B: Detail-follow**
- Selector spec that supports:
  - text extraction (default / `::text`)
  - attribute extraction (`@attr` / `::attr(attr)`)
- URL normalization convention for keys ending in `*_url`
- Optional validation and a quality report (missing field counts)
- CSV export with a stable union-of-keys header strategy
- Offline demo mode using HTML fixtures (`--demo`)

---

## Architecture at a glance

### Component diagram
```mermaid
flowchart TB
  CLI[cli.py<br/>CLI / Orchestrator]
  CFG[config.py<br/>YAML loading & validation]
  FCH[fetcher.py<br/>HTTP fetch + retry/backoff<br/>FileFetcher for demo]
  PAR[parser.py<br/>Selector spec + parsers]
  VAL[validator.py<br/>Quality summary/report]
  EXP[exporter.py<br/>Export helpers]

  CLI --> CFG
  CLI --> FCH
  CLI --> PAR
  CLI --> VAL
  CLI --> EXP
````

### Execution modes

* **Mode A: List-only**

  * Fetch `list_url` once
  * Parse repeated item blocks via `item_selector`
  * Extract fields per item via `item_fields`

* **Mode B: Detail-follow**

  * Fetch `list_url`
  * Extract product links via `link_selector`
  * Fetch each detail page URL
  * Extract fields via `detail_selectors` (plus stable “core fields”)

---

## End-to-end data flow

### Mode A: List-only pipeline

```mermaid
flowchart LR
  A[Load .env (optional)] --> B[Load targets YAML]
  B --> C[Validate targets schema]
  C --> D[Load settings YAML (optional)]
  D --> E[Configure logging]
  E --> F[Resolve output path]
  F --> G[Fetch list_url]
  G --> H[Parse items from item_selector]
  H --> I[Extract item_fields per item]
  I --> J[Add source_list_url]
  J --> K[Normalize *_url (base=list_url)]
  K --> L[Quality report (optional)]
  L --> M{dry-run?}
  M -- No --> N[Export CSV]
  M -- Yes --> O[Skip export]
```

### Mode B: Detail-follow pipeline

```mermaid
flowchart LR
  A[Load .env (optional)] --> B[Load targets YAML]
  B --> C[Validate targets schema]
  C --> D[Load settings YAML (optional)]
  D --> E[Configure logging]
  E --> F[Resolve output path]
  F --> G[Fetch list_url]
  G --> H[Extract hrefs via link_selector]
  H --> I[Resolve hrefs to absolute URLs]
  I --> J[Loop: fetch each detail_url]
  J --> K[Parse detail fields via detail_selectors]
  K --> L[Add detail_url + source_list_url]
  L --> M[Normalize *_url (base=detail_url)]
  M --> N[Delay between detail requests (optional)]
  N --> O[Quality report (optional)]
  O --> P{dry-run?}
  P -- No --> Q[Export CSV]
  P -- Yes --> R[Skip export]
```

---

## Core modules and responsibilities

### `src/product_scraper/cli.py` — Orchestrator

Responsibilities:

* Defines the CLI interface:

  * `--config`, `--output`, `--limit`, `--dry-run`, `--target-name`, `--demo`
* Loads `.env` via `load_dotenv()` (supports standard proxy env vars)
* Loads and validates targets configuration
* Loads optional settings from `config/settings.yml`
* Configures logging from settings
* Resolves the output path with a strict precedence
* Executes the pipeline and returns a numeric exit code

Key implementation details:

* **`--dry-run` still fetches and parses** (it only skips exporting)
* In detail-follow mode, failed detail fetches are **skipped per item** (run succeeds if at least one record is parsed)

---

### `src/product_scraper/config.py` — Configuration contracts and validation

Responsibilities:

* Loads YAML using a safe loader
* Enforces the targets schema and mode requirements
* Loads optional settings YAML

Targets validation rules (summary):

* Top-level config must be a mapping with `targets` as a **non-empty list**
* Each target must be a mapping and include:

  * `name` (non-empty, **unique** across targets)
  * `list_url` (non-empty string)
* Mode selection and requirements:

  * **List-only** requires:

    * `item_selector` (non-empty string)
    * `item_fields` (non-empty mapping: field → selector spec)
  * **Detail-follow** requires:

    * `link_selector` (non-empty string)
    * `detail_selectors` (non-empty mapping: field → selector spec)
* All selector specs must be non-empty strings

Settings loading behavior:

* Missing file ⇒ `{}` (allowed)
* Empty file ⇒ `{}` (allowed)
* Non-mapping top-level ⇒ error

---

### `src/product_scraper/fetcher.py` — Fetching, retries/backoff, offline demo

Key classes:

* `Fetcher` (HTTP)
* `FileFetcher` (offline fixtures via file paths / `file://` URIs)
* `FetchError`

HTTP behavior:

* Timeout and user-agent are configurable via settings
* Attempts:

  * Configured as `http.max_retries` in settings, but treated as **total attempts**
* Retry conditions:

  * HTTP `429` and HTTP `5xx`
  * network exceptions from the HTTP client
* Optional exponential backoff and jitter:

  * enabled when backoff settings are provided

Politeness:

* Optional `delay_seconds` is applied between **detail page** requests (detail-follow mode)

---

### `src/product_scraper/parser.py` — Selector spec and parsers

Selector spec syntax supports:

* Text extraction:

  * `"css.selector"` or `"css.selector::text"`
* Attribute extraction:

  * `"css.selector@href"` or `"css.selector::attr(href)"`

Parsers:

* `ListItemsParser` (list-only)

  * Selects item blocks via `item_selector`
  * For each item block, extracts fields via selector specs
* `ListPageParser` (detail-follow)

  * Extracts hrefs from elements matching `link_selector`
* `DetailPageParser` (detail-follow)

  * Extracts fields from detail page HTML using `detail_selectors`
  * Includes stable “core fields” (`title`, `price`, `image_url`, `description`) as keys (with `None` if missing)

Extraction guarantees:

* If a selector finds no matching element, the extracted value is `None`
* Empty or whitespace-only extracted text becomes `None`

---

### `src/product_scraper/validator.py` — Validation and quality reporting

Responsibilities:

* Computes a missing-field summary across records
* Defines missing as `None` or `""`
* Formats a human-readable report (printed to stdout when enabled)

Important behavior:

* Validation/quality reporting can be disabled via `settings.validation.enabled`
* The report is useful for detecting HTML drift (increasing missing counts)

---

### `src/product_scraper/exporter.py` — Exporters

The CLI uses:

* `export_to_csv(records, output_path)`

CSV export contract:

* Header is a stable **union-of-keys**:

  * keys from the first record first
  * newly discovered keys appended as encountered
* Missing values are written as empty strings

Additional helpers (not wired into CLI flags by default):

* `export_to_json(...)`
* `export_to_excel(...)` (optional dependencies)

---

## Configuration contracts

### Targets configuration (`config/targets*.yml`)

Top-level:

* `targets: [ ... ]`

Per-target required keys:

* `name` (unique)
* `list_url`

Mode A (list-only) required keys:

* `item_selector`
* `item_fields`

Mode B (detail-follow) required keys:

* `link_selector`
* `detail_selectors`

---

### Settings configuration (`config/settings*.yml`)

Settings file path:

* Loaded from `config/settings.yml` (optional; missing file is allowed)

Recognized sections:

* `http`:

  * `user_agent`
  * `timeout`
  * `max_retries` (total attempts)
  * `delay_seconds` (detail-follow mode politeness delay)
  * `retry_backoff_seconds`
  * `retry_backoff_multiplier`
  * `retry_jitter_seconds`
* `output`:

  * `directory`
  * `csv_filename`
* `validation`:

  * `enabled`
* `logging`:

  * `level`

Output path precedence:

1. CLI `--output`
2. `settings.output.directory` + `settings.output.csv_filename`
3. Fallback:

   * standard run: `sample_output/products.csv`
   * demo run: `sample_output/products.demo.csv`

---

## Data contract

### Record shape

Records are dictionaries driven primarily by configuration selectors (plus pipeline-added fields).

Traceability fields:

* `source_list_url` (always present)
* `detail_url` (detail-follow mode only; the absolute URL actually fetched)

### URL normalization

Any key ending with `_url` is treated as URL-like and normalized to an absolute URL when possible:

* List-only mode: base is `list_url`
* Detail-follow mode: base for detail fields is `detail_url`

This convention is intentionally simple and resilient:

* Naming a field `*_url` means “treat this as a URL and normalize it.”

---

## Error handling and exit behavior

### Error categories

1. **Configuration errors**

   * invalid YAML
   * missing required keys
   * empty selectors / invalid mode shape
   * duplicate target names

2. **Fetch errors**

   * list page fetch failure is **fatal**
   * detail page fetch failure is **non-fatal per item** (item skipped)

3. **Parse drift (HTML changes)**

   * often manifests as missing fields (`None`/empty) rather than exceptions
   * quality reporting is the primary early-warning mechanism

4. **No data**

   * if no records are parsed, the run aborts (exit code 1)

### Exit codes

* `0`: success
* `1`: fatal failure (config invalid, fatal fetch failure, no records, unexpected exception)

---

## Reliability and politeness controls

### Timeouts

* Applied per HTTP request via settings (`http.timeout`)

### Attempts, retries, backoff, jitter

* Retryable:

  * HTTP 429
  * HTTP 5xx
  * request exceptions
* Optional backoff/jitter:

  * enabled when backoff settings are provided
* Non-retryable:

  * most 4xx errors (except 429)

### Delay

* Optional `http.delay_seconds` applied between detail page requests (detail-follow mode)
* Helps reduce load and improve operational stability

### User-Agent

* Configurable via settings (`http.user_agent`)
* Intended to support transparent and client-approved identification

---

## Observability

### Logging

* Logging level is configurable (`logging.level`, default INFO)
* Key signals:

  * run mode and target selection
  * number of records parsed
  * skipped detail URLs with error context
  * export path written

### Quality report (stdout)

When validation is enabled:

* Total records
* Fields observed
* Missing counts per field

This is a practical guardrail against silent regressions when site HTML changes.

---

## Demo mode and deterministic verification

### `--demo` (offline)

* Runs the pipeline without network calls using `fixtures/` HTML files
* Uses `FileFetcher` to read local HTML
* Produces a CSV in `sample_output/` by default (unless `--dry-run`)

### Deterministic tests

* Tests do not perform live scraping
* HTML parsing is validated using fixtures and synthetic HTML strings
* HTTP behavior is validated via mocked responses

This ensures reproducibility in CI and reduces risk during evaluation.

---

## Testing and CI strategy (architecture implications)

### What is covered

* Config validation rules
* Selector spec parsing and extraction behavior
* List-only parsing
* Detail-follow parsing
* Fetch retry logic for retryable vs non-retryable errors
* Exporter data contract (union-of-keys)
* CLI orchestration, including:

  * demo mode
  * dry-run behavior
  * output path precedence via settings

### CI gates

GitHub Actions runs:

* `ruff check src tests`
* `pytest`

A change that breaks the contract typically fails CI quickly and deterministically.

---

## Security, legal, and compliance posture

This template is designed to support responsible operation:

* Politeness knobs (delay, retries/backoff)
* Configurable User-Agent
* Deterministic tests/demos without live scraping
* Traceability fields to support auditability

Explicit boundaries:

* No anti-bot bypass mechanisms are included
* Operators should review ToS/robots and confirm authorization for the target and intended use
* Avoid personal data unless clearly authorized and necessary

For operational guidance, see `docs/SECURITY_AND_LEGAL.md`.

---

## Extensibility points

### Configuration-first adaptations

* Add a new target by authoring YAML selectors
* Iterate safely using:

  * `--dry-run` and small `--limit`
  * quality report review
  * then a full run with tuned delay/backoff

### Code-level extensions (recommended evolution paths)

* Pagination support (page discovery + max pages)
* Storage adapters (SQLite/Postgres), incremental runs and diffing
* Concurrency (bounded parallel detail fetch, maintaining politeness)
* Notifications (Slack/email) and structured run reports
* Stronger schema validation + type checking
* CLI `--format` to expose JSON/Excel exports using existing exporter helpers

---

## Repository layout (navigation)

```text
src/product_scraper/     Core implementation
config/                 Example targets and settings
docs/                   Architecture, config, operations, testing, legal guidance
fixtures/               Offline HTML for demo/tests
tests/                  Unit and orchestration tests
.github/workflows/       CI pipeline definition
sample_output/           Sample outputs for demonstration
```

---

## Appendix: Selector spec reference

### Text extraction (default)

* `"h4.price"`
* `"h4.price::text"`

Returns `element.get_text(strip=True)` (or `None` if missing/empty).

### Attribute extraction

* `"a.title@href"`
* `"a.title::attr(href)"`

Returns `element.get(attr)` (or `None` if missing/empty).

---

## Appendix: Operational quick reference

Recommended safe iteration loop:

1. Create runtime configs from examples:

   * `config/targets.example.yml` → `config/targets.yml`
   * `config/settings.example.yml` → `config/settings.yml`
2. Update selectors for the target site
3. Validate quickly:

   * run with `--dry-run` and a small `--limit`
4. Review:

   * missing-field report
   * sample parsed record in logs (dry-run)
5. Run the full scrape with tuned `delay_seconds`, timeouts, and attempts
6. Treat non-zero exit codes as failures in schedulers/CI and review logs