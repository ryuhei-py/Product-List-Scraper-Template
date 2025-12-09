# Architecture - Product List Scraper Template

This document describes the internal architecture of the Product List Scraper Template: its main components, data flow, and how the layers interact.

---

## 1. Goals

This section explains the goals of the architecture.

- Separate **site-specific configuration** from **generic scraping logic**
- Keep components focused and testable
- Make it easy to **add new sites** by editing YAML
- Provide a clear structure that clients can review and understand

---

## 2. Component overview

This section outlines the main components and their responsibilities.

- **Config layer** (`config.py`, `config/*.yml`)
  - Loads and validates YAML configurations
  - Provides structured access to:
    - list page URLs
    - selectors for list and detail pages
    - optional pagination and HTTP settings
- **Fetcher** (`fetcher.py`)
  - Handles HTTP GET requests with:
    - headers (user-agent, etc.)
    - timeouts
    - retry logic for transient failures
  - Returns raw HTML as text
- **Parsers** (`parser.py`)
  - `ListPageParser`
    - Parses list pages to extract product and detail URLs
  - `DetailPageParser`
    - Parses detail pages to extract structured fields:
      - title, price, image URL, description, etc.
  - Both are driven by selectors defined in YAML
- **Exporter** (`exporter.py`)
  - Writes lists of record dictionaries to:
    - CSV
    - JSON (optional)
  - Handles header generation and missing fields
- **Validator** (`validator.py`)
  - Computes per-field missing counts
  - Produces a summary dictionary
  - Formats a human-readable quality report
- **CLI** (`cli.py`)
  - Wires everything together into a single pipeline
  - Parses command-line arguments
  - Orchestrates config -> fetch -> parse -> export -> validate
  - Provides a clean entrypoint for users and schedulers

---

## 3. Layered architecture

This section shows the layered flow of the scraper.

```text
YAML config
    |
Config loader (config.py)
    |
Fetcher (fetcher.py)
    |
ListPageParser (parser.py)
    |
DetailPageParser (parser.py)
    |
Records (in-memory list[dict])
    |
Exporter (exporter.py)
    |
Validator (validator.py)
    |
CLI / Output (cli.py)
```

Each layer has a single responsibility:

- Config: What should we scrape?
- Fetcher: How do we retrieve the HTML?
- Parsers: How do we turn HTML into structured records?
- Exporter: How do we persist records?
- Validator: How good is the data we collected?
- CLI: How do we run the whole thing from the command line?

---

## 4. Data flow

This section describes how data moves through the system.

### 4.1 High-level flow

```mermaid
flowchart TD
    A[targets.yml] --> B[Config loader]
    B --> C[Fetcher]
    C --> D[ListPageParser]
    D --> E[Product URLs]
    E --> F[DetailPageFetcher/Parser]
    F --> G[Records (list of dict)]
    G --> H[Exporter (CSV/JSON)]
    G --> I[Validator]
    I --> J[Quality report]
```

Config loader

Reads `config/targets.yml`

Extracts:

- list page URLs
- link selector for product URLs
- detail selectors for fields

Fetcher

Fetches HTML for each list page

ListPageParser

Parses list pages, extracts product and detail URLs

DetailPageFetcher + Parser

Fetches each product URL

Parses detail page HTML into a record dict

Exporter

Writes all records to CSV or JSON

Validator

Computes missing counts and prints a quality report

---

## 5. Key modules

This section lists the key modules and their duties.

### 5.1 config.py

Encapsulates YAML loading.

May provide functions like:

- `load_targets_config(path: Path) -> TargetsConfig`
- Optionally: `load_settings_config(path: Path) -> SettingsConfig`

Handles basic validation (required fields, correct types).

### 5.2 fetcher.py

Provides a Fetcher class that:

- Accepts settings (timeout, retries, headers)
- Provides a `get(url: str) -> str` method
- Retries on network errors and 5xx responses
- Is easily mockable for tests

### 5.3 parser.py

Responsible for HTML and data extraction:

ListPageParser

- `parse_list(html: str) -> list[str]` (product URLs)

DetailPageParser

- `parse_detail(html: str) -> dict[str, Any]`

Uses BeautifulSoup (or similar) internally.

Driven by selectors from config (no hard-coded site logic).

### 5.4 exporter.py

Functions:

- `export_to_csv(records, path)`
- `export_to_json(records, path)`

Normalizes headers and writes UTF-8 files.

Handles missing keys gracefully.

### 5.5 validator.py

Functions:

- `validate_records(records) -> dict`
- `format_quality_report(summary) -> str`

Computes:

- total records
- fields present
- missing counts per field

Provides a multi-line, human-readable summary.

### 5.6 cli.py

CLI entrypoint:

```bash
python -m product_scraper.cli --config config/targets.yml --output sample_output/products.csv
```

Responsibilities:

- Parse CLI arguments
- Load configuration
- Run the scrape pipeline
- Export results
- Print validation report

---

## 6. Extensibility

This section highlights ways to extend the architecture.

New sites:

- Add a new config file with different URLs and selectors
- Reuse the same core code

New output formats:

- Extend `exporter.py` (e.g., Excel, database, API)

Advanced features:

- Add login, cookies, headless browser support by swapping the Fetcher implementation
- Add rate-limiting and advanced scheduling via external tools

Because responsibilities are separated, you can replace or extend individual layers without rewriting the whole system.
