# Architecture
This document explains the internal architecture of the Product List Scraper Template: how configuration is loaded, how pages are fetched and parsed, how records are normalized and validated, and how output is produced.

The design goals are:
- Config-driven reuse: adapt to new sites by editing YAML.
- Two-mode scraping: list-only (single-page extraction) and detail-follow (list → detail pages).
- Operational reliability: retries for transient failures, optional backoff knobs, structured logging.
- Traceability: records carry source URLs (`source_list_url`, `detail_url`).
- Data robustness: CSV export uses a stable union-of-keys across records.

---

## High-level pipeline
This section describes the runtime flow and modes.

At runtime, the CLI loads:
1) Targets config (`config/targets.yml` or `config/targets.example.yml`).
2) Settings config (`config/settings.yml` or `config/settings.example.yml`).
3) Runs the pipeline for a selected target.

Two target modes determine which parser path is used:
- List-only mode: parse repeated item cards directly from the list page.
- Detail-follow mode: extract detail links from list page, then parse each detail page.

### Flow diagram
This subsection visualizes the data flow.

```mermaid
flowchart TD
  A[CLI] --> B[Load settings.yml (optional)]
  A --> C[Load targets.yml]
  C --> D{Validate + Select target}
  D -->|List-only| E[Fetch list_url]
  D -->|Detail-follow| F[Fetch list_url]
  E --> G[ListItemsParser: parse_items]
  F --> H[ListPageParser: parse_links]
  H --> I[Fetch each detail_url]
  I --> J[DetailPageParser: parse_detail]
  G --> K[Normalize *_url fields]
  J --> K[Normalize *_url fields]
  K --> L[Add trace fields: source_list_url / detail_url]
  L --> M[Optional validation + quality report]
  M --> N[Export: CSV (union-of-keys), JSON, Excel]
```

---

## Core modules and responsibilities
This section lists each module and its role.

### src/product_scraper/cli.py
This subsection covers orchestration.

- Parse CLI args (`--config`, `--output`, `--limit`, `--target-name`, `--dry-run`, etc.).
- Load `.env` if present.
- Load settings + targets, validate targets, select target(s).
- Choose pipeline mode based on target shape:
  - List-only: `item_selector` + `item_fields`.
  - Detail-follow: `link_selector` + `detail_selectors`.
- Normalize URL-like fields (`*_url`) to absolute URLs when possible.
- Add traceability fields (`source_list_url`, and `detail_url` for detail-follow).
- Call exporter to write output (unless `--dry-run`).

### src/product_scraper/config.py
This subsection covers configuration parsing.

- Loads YAML safely.
- Validates target schema: name required, non-empty, unique; list_url required.
- Enforces either list-only mode requirements or detail-follow mode requirements.
- Raises `ConfigError` for actionable error messages.

### src/product_scraper/fetcher.py
This subsection describes HTTP fetching.

- Uses a session for connection reuse.
- Applies timeout, headers (for example, User-Agent), and retry policy.
- Retry policy: retry on HTTP 429 and HTTP 5xx; do not retry on other 4xx by default.
- Optional backoff knobs: `retry_backoff_seconds`, `retry_backoff_multiplier`, `retry_jitter_seconds`.
- Emits `FetchError` with status and URL context.

### src/product_scraper/parser.py
This subsection explains HTML parsing.

- `ListPageParser` (detail-follow mode): extracts detail page links from list HTML using `link_selector`.
- `DetailPageParser` (detail-follow mode): extracts fields from a detail page using `detail_selectors` mapping.
- `ListItemsParser` (list-only mode): extracts repeated item records from a list page using `item_selector` for cards and `item_fields` mapping for per-item extraction.
- Selector extraction supports a selector-spec syntax described below.

### src/product_scraper/validator.py
This subsection covers validation.

- Record-level validation and quality reporting.
- Checks field coverage (missing/empty counts) and produces a summary.
- Can be toggled via settings (for example, `validation.enabled`).

### src/product_scraper/exporter.py
This subsection describes output serialization.

- CSV export: computes headers as a stable union-of-keys across all records; header order uses keys from the first record (in insertion order) then newly-seen keys appended in encounter order.
- JSON export: writes records as a list of objects.
- Excel export (optional): requires the optional dependency group (for example, `pip install ".[excel]"`).

---

## Target schema and mode selection
This section outlines how targets are defined and interpreted.

Targets are loaded from YAML under `targets:`.

### List-only mode target (shape)
This subsection shows required fields for list-only mode.

Required keys:
- `name` (unique)
- `list_url`
- `item_selector`
- `item_fields` (non-empty mapping)

Example:

```yaml
targets:
  - name: laptops-demo
    list_url: "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"
    item_selector: "div.thumbnail"
    item_fields:
      title: "a.title@title"
      price: "h4.price"
      image_url: "img@src"
      product_url: "a.title@href"
```

### Detail-follow mode target (shape)
This subsection shows required fields for detail-follow mode.

Required keys:
- `name` (unique)
- `list_url`
- `link_selector`
- `detail_selectors` (non-empty mapping)

Example:

```yaml
targets:
  - name: my-shop
    list_url: "https://example.com/products"
    link_selector: "a.product-link"
    detail_selectors:
      title: "h1.product-title"
      price: ".price"
      image_url: "img.product-image@src"
```

### Mode selection
This subsection explains how mode is chosen.

The CLI treats a target as list-only mode if it includes list-only keys (for example, `item_selector` / `item_fields`). Otherwise, it is interpreted as detail-follow mode.

---

## Selector spec: extraction contract
This section explains selector-spec behavior.

Selector specs control how values are extracted from HTML.

Text extraction:
- `"h4.price"`: selects an element and extracts `get_text(strip=True)`.
- `"a.title::text"`: explicit text extraction.

Attribute extraction (two equivalent syntaxes):
- `"a.title@title"`
- `"a.title::attr(title)"`

General examples:
- `"img@src"`
- `"a@href"`

If the element is not found or the value is empty, extraction returns a missing value.

---

## Data contract: records, traceability, and URL normalization
This section covers the fields added and URL handling.

Traceability fields:
- `source_list_url`: always present (both modes).
- `detail_url`: present in detail-follow mode (the resolved absolute URL actually fetched).

URL normalization:
- For any field name ending with `_url` (for example, `image_url`, `product_url`, `detail_url`), if the extracted value is relative, it is resolved to an absolute URL using `urljoin()`.
- Base URL depends on mode:
  - List-only: base is `list_url`.
  - Detail-follow: base for detail fields is `detail_url`.
- Naming a field `*_url` signals “this should be treated as a URL.”

---

## Error handling and failure modes
This section describes expected failures.

- Configuration errors: invalid YAML, missing keys, empty selectors, duplicate target names, etc. result in `ConfigError`; the CLI terminates with a clear message.
- Fetch errors: `FetchError` is raised for non-success responses or request exceptions; retry behavior applies only to retryable cases (commonly 429 and 5xx), based on settings.
- Parse errors: HTML structure changes typically produce missing fields rather than hard failures; quality reporting helps detect regressions (spikes in missing counts).
- Dry-run mode: when `--dry-run` is set, no output file is written; the CLI logs a count and may log a sample record.

---

## Export architecture (CSV union-of-keys)
This section explains how heterogeneous records are handled.

Real-world targets often produce heterogeneous records (for example, missing images, extra attributes, category-specific fields). To avoid losing columns, CSV export computes headers as:

- Keys of the first record (in insertion order).
- Newly discovered keys from later records appended in encounter order.

This yields a stable, predictable header order while ensuring all fields are represented.

---

## Extensibility points (how to adapt for clients)
This section lists common extension options.

- Custom parsers: add site-specific parsing logic (pagination, embedded JSON, tables).
- Storage layer: add a persistence layer (SQLite/Postgres/S3) for scheduled jobs.
- Scheduling: integrate cron, GitHub Actions, Airflow, or a lightweight scheduler.
- Notifications: send Slack/email alerts on failures, empty runs, or quality regressions.
- Anti-bot strategies (compliance-first): introduce slower pacing, caching, and headers; consider official APIs when available.

---

## Security and compliance reminder
This section reinforces responsible usage.

This architecture supports responsible scraping (timeouts, delays, retries), but compliance is a product requirement, not just a code feature. See `docs/SECURITY_AND_LEGAL.md` for concrete guidance on:

- Terms of Service review.
- robots.txt handling.
- Rate limiting.
- Data minimization and privacy.
- Operational risk management.

---

_Last updated: 2025-12-12_
