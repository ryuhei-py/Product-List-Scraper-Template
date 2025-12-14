# Configuration Guide

This document explains how to configure **Product-List-Scraper-Template** using YAML files and optional environment variables. The configuration model is designed to keep most “site adaptation” changes in configuration rather than code, while preserving reproducibility, operational safety knobs, and clear failure modes.

---

## Table of contents

- [Configuration model](#configuration-model)
- [Files and recommended workflow](#files-and-recommended-workflow)
- [Quickstart](#quickstart)
- [Targets configuration (`targets*.yml`)](#targets-configuration-targetsyml)
  - [Top-level schema](#top-level-schema)
  - [Target selection](#target-selection)
  - [Mode A: List-only scraping](#mode-a-list-only-scraping)
  - [Mode B: Detail-follow scraping](#mode-b-detail-follow-scraping)
  - [Selector spec syntax](#selector-spec-syntax)
  - [URL normalization rules (`*_url`)](#url-normalization-rules-_url)
  - [Target validation rules](#target-validation-rules)
- [Settings configuration (`settings*.yml`)](#settings-configuration-settingsyml)
  - [How settings are loaded](#how-settings-are-loaded)
  - [Settings schema](#settings-schema)
  - [HTTP retry and backoff behavior](#http-retry-and-backoff-behavior)
  - [Rate limiting / politeness delay](#rate-limiting--politeness-delay)
  - [Output path resolution](#output-path-resolution)
  - [Validation and quality report](#validation-and-quality-report)
  - [Logging](#logging)
- [Environment variables and `.env`](#environment-variables-and-env)
- [Practical usage patterns](#practical-usage-patterns)
- [Common mistakes and fixes](#common-mistakes-and-fixes)
- [Reference configurations](#reference-configurations)
- [Where to go next](#where-to-go-next)

---

## Configuration model

The scraper combines three inputs:

1. **Targets config (required)**  
   Defines *what pages to scrape* and *how to extract fields*.  
   - Provided via `--config`  
   - Default: `config/targets.example.yml`

2. **Settings config (optional)**  
   Defines *runtime behavior*: HTTP knobs, default output location, validation, and logging.  
   - Loaded from `config/settings.yml`  
   - If missing, the scraper proceeds using defaults

3. **Environment variables (optional)**  
   Loaded via `.env` (if present) and the process environment.  
   - Typical use: `HTTP_PROXY` / `HTTPS_PROXY`

---

## Files and recommended workflow

### Tracked vs runtime configuration files

**Tracked (committed) examples**
- `config/targets.example.yml`
- `config/settings.example.yml`
- `.env.example`

**Runtime configuration (recommended for actual runs)**
- `config/targets.yml`
- `config/settings.yml`
- `.env`

### Create runtime configs from examples

```bash
cp config/targets.example.yml config/targets.yml
cp config/settings.example.yml config/settings.yml
cp .env.example .env
````

---

## Quickstart

### 1) Prepare runtime configs

```bash
cp config/targets.example.yml config/targets.yml
cp config/settings.example.yml config/settings.yml
```

### 2) Edit `config/targets.yml`

Choose one of the two target modes per target:

* **List-only**: parse repeated “cards/tiles” from the list page
* **Detail-follow**: extract product links from list page, then fetch and parse each detail page

### 3) Validate quickly with a safe iteration loop

```bash
# NOTE: --dry-run still fetches and parses URLs; it only skips writing the CSV.
product-scraper --config config/targets.yml --dry-run --limit 10
```

### 4) Run and write CSV output

```bash
product-scraper --config config/targets.yml --output output/products.csv
```

---

## Targets configuration (`targets*.yml`)

Targets are YAML-defined “scrape recipes.” One targets file can contain multiple targets.

### Top-level schema

```yml
targets:
  - name: example-target
    list_url: "https://example.com/products"
    # mode-specific keys below...
```

#### Required fields (all targets)

* `name` (string, non-empty, **unique** across targets)
* `list_url` (string, non-empty)

---

### Target selection

If multiple targets exist:

* `--target-name` selects a target by exact `name`
* if omitted, the **first** target in the list is used

```bash
product-scraper --config config/targets.yml --target-name laptops-detail --dry-run --limit 10
```

---

## Mode A: List-only scraping

Use this mode when the list page already contains the fields you need in repeated item blocks.

### Required keys (in addition to `name`, `list_url`)

* `item_selector` (CSS selector matching each product card/tile)
* `item_fields` (mapping: output field → selector spec)

### Example

```yml
targets:
  - name: laptops-list
    list_url: "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"
    item_selector: "div.thumbnail"
    item_fields:
      title: "a.title@title"
      price: "h4.price"
      description: "p.description"
      image_url: "img@src"
      product_url: "a.title@href"
```

### Output contract (list-only)

* The pipeline adds `source_list_url` to every record.
* The pipeline normalizes fields whose names end with `*_url` using `list_url` as the base (see [URL normalization rules (`*_url`)](#url-normalization-rules-_url)).

---

## Mode B: Detail-follow scraping

Use this mode when key fields are only available (or more reliable) on product detail pages.

### Required keys (in addition to `name`, `list_url`)

* `link_selector` (CSS selector for product links on the list page)
* `detail_selectors` (mapping: output field → selector spec)

### Example

```yml
targets:
  - name: laptops-detail
    list_url: "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"
    link_selector: "a.title"
    detail_selectors:
      title: "h4:not(.price)"
      price: "h4.price"
      description: "p.description"
      image_url: "img@src"
```

### Output contract (detail-follow)

* The pipeline adds:

  * `source_list_url` (always)
  * `detail_url` (the resolved URL actually fetched)
* Fields ending with `*_url` are normalized using `detail_url` as the base.
* If some detail pages fail to fetch, they are **skipped**; the run can still succeed if at least one record is produced.

---

## Selector spec syntax

Selector specs define how values are extracted from HTML. They support **text extraction** and **attribute extraction**.

### Text extraction (default)

* `"h4.price"`
  Selects the element and extracts `.get_text(strip=True)`.

* `"h4.price::text"`
  Explicit text mode (same behavior).

Examples:

```yml
price: "h4.price"
description: "p.description::text"
```

### Attribute extraction

Two equivalent forms are supported:

* `"a.title@href"`
* `"a.title::attr(href)"`

Examples:

```yml
product_url: "a.title@href"
image_url: "img@src"
```

### Extraction behavior and edge cases

* If no matching element is found, the value becomes missing (`null` / `None`).
* If extracted text is empty or whitespace, it is treated as missing.
* If you want URL normalization, ensure the output field name ends with `*_url`.

---

## URL normalization rules (`*_url`)

The pipeline treats any field whose name ends in `*_url` as “URL-like.”

* If the value is a relative URL (e.g., `/p/123`), it is resolved to an absolute URL via `urljoin`.
* If the value is already absolute, it is preserved.
* If the value is empty or missing, it stays missing.

Base URL used for normalization:

* **List-only** mode: base = `list_url`
* **Detail-follow** mode: base = `detail_url` (per record)

Recommended URL field names:

* `product_url`
* `detail_url` (added automatically in detail-follow mode)
* `image_url`
* any other link field that should become absolute (e.g., `reviews_url`, `brand_url`)

---

## Target validation rules

Targets are validated **before** the scraper runs. Validation failures are treated as fatal errors.

Validation rules enforced include:

* The YAML root must be a mapping.
* `targets` must exist and be a **non-empty list**.
* Each target must be a mapping.
* Each target must include non-empty `name` and `list_url`.
* Target `name` values must be unique.

Mode-specific rules:

### List-only mode validation

Triggered when `item_selector` or `item_fields` is present.

* `item_selector` must be a non-empty string.
* `item_fields` must be a non-empty mapping.
* Each selector spec in `item_fields` must be a non-empty string.

### Detail-follow mode validation

Used otherwise.

* `link_selector` must be a non-empty string.
* `detail_selectors` must be a non-empty mapping.
* Each selector spec in `detail_selectors` must be a non-empty string.

---

## Settings configuration (`settings*.yml`)

Settings provide runtime controls and defaults. They are optional.

### How settings are loaded

Settings are loaded from:

* `config/settings.yml`

Behavior:

* If the file does not exist → settings are treated as `{}` and the run continues.
* If the file exists but is empty → settings are treated as `{}`.
* If the file’s root is not a mapping → the run fails.

---

## Settings schema

The following top-level keys are supported:

* `http`
* `output`
* `validation`
* `logging`

### Example `config/settings.yml`

```yml
http:
  user_agent: "Mozilla/5.0 (compatible; ProductScraper/1.0)"
  timeout: 10
  max_retries: 3
  delay_seconds: 1.0
  retry_backoff_seconds: 0.0
  retry_backoff_multiplier: 2.0
  retry_jitter_seconds: 0.0

output:
  directory: "sample_output"
  csv_filename: "products.csv"

validation:
  enabled: true

logging:
  level: "INFO"
```

---

## HTTP retry and backoff behavior

The fetcher supports controlled resilience for transient issues.

### `http.timeout`

Per-request timeout in seconds.

### `http.max_retries` (attempt semantics)

This value controls the maximum number of **attempts** per URL.

* The fetch loop runs attempts `1..max_retries`.
* Example: `max_retries: 3` means up to **3 attempts total**.

### Retry conditions

Requests are retried on:

* HTTP `429`
* HTTP `5xx`
* network-level request exceptions

Requests are not retried on other `4xx` statuses.

### Backoff / jitter controls

Backoff and jitter are optional knobs:

* `retry_backoff_seconds`
* `retry_backoff_multiplier`
* `retry_jitter_seconds`

When enabled, backoff generally increases with each attempt and may include random jitter to reduce coordinated retry bursts.

---

## Rate limiting / politeness delay

### `http.delay_seconds`

This delay is applied **between detail page fetches** in detail-follow mode.

Notes:

* List-only mode fetches only the list page once, so it does not apply per-item delays.
* This is a basic politeness control; you may need stronger throttling depending on target rules and load constraints.

---

## Output path resolution

The CLI writes **CSV** output. The output path is resolved in this order:

1. `--output` CLI flag (highest priority)
2. `settings.output.directory` + `settings.output.csv_filename`
3. Fallback:

   * normal run: `sample_output/products.csv`
   * demo run: `sample_output/products.demo.csv`

Practical examples:

```bash
# Highest priority: explicit output flag
product-scraper --config config/targets.yml --output output/run.csv

# Settings-based default output (when --output is omitted)
product-scraper --config config/targets.yml
```

---

## Validation and quality report

The scraper can print a “quality report” summarizing missing fields across records.

### `validation.enabled`

* `true` (default behavior): prints missing-field counts per field
* `false`: skips the quality report

The report is useful for detecting selector drift when HTML changes.

---

## Logging

### `logging.level`

Controls Python logging verbosity. Typical values:

* `DEBUG`
* `INFO`
* `WARNING`
* `ERROR`

If an invalid value is provided, logging falls back to `INFO`.

---

## Environment variables and `.env`

The CLI loads `.env` (if present) using `python-dotenv`. Environment variables are optional, but useful for runtime-only values.

### Proxy variables (common)

Standard proxy environment variables are supported:

```env
HTTP_PROXY=
HTTPS_PROXY=
```

If you use proxies, prefer keeping them in `.env` (not committed) and supply `.env.example` placeholders.

---

## Practical usage patterns

### Safe iteration loop (recommended)

```bash
# Validate selectors and output shape without writing CSV
# NOTE: still performs HTTP fetches.
product-scraper --config config/targets.yml --dry-run --limit 10
```

### Run list-only target

```bash
product-scraper \
  --config config/targets.yml \
  --target-name laptops-list \
  --limit 50 \
  --output output/laptops_list.csv
```

### Run detail-follow target

```bash
product-scraper \
  --config config/targets.yml \
  --target-name laptops-detail \
  --limit 50 \
  --output output/laptops_detail.csv
```

### Demo mode (offline)

Demo mode scrapes local fixtures using `FileFetcher` and can be used to verify behavior without any network access.

```bash
product-scraper --demo --output output/demo.csv
```

---

## Common mistakes and fixes

### “Dry-run failed because the URL is invalid or returned 404”

`--dry-run` still fetches the target URL. Use a real list URL or run `--demo` for offline verification.

### “I get zero records”

* Confirm `item_selector` (list-only) or `link_selector` (detail-follow) matches the real HTML.
* Start with `--limit 10` and refine selectors incrementally.
* Use the quality report to spot missing fields.

### “Some URLs are still relative”

URL normalization only applies to fields named with `*_url`. Rename fields accordingly (e.g., `product_url`, `image_url`).

### “Output went somewhere unexpected”

Remember the precedence:

1. `--output`
2. `settings.output.directory` + `settings.output.csv_filename`
3. fallback defaults

### “Detail pages intermittently fail”

* Increase `http.timeout`
* Adjust `http.max_retries`
* Use `retry_backoff_seconds` (and optionally jitter)
* Add a polite `delay_seconds` between detail fetches

---

## Reference configurations

### Reference A — List-only target

```yml
targets:
  - name: example-list
    list_url: "https://example.com/products"
    item_selector: "div.product"
    item_fields:
      title: "a.title@title"
      price: "span.price"
      product_url: "a.title@href"
      image_url: "img@src"
      source_brand: "span.brand"
```

### Reference B — Detail-follow target

```yml
targets:
  - name: example-detail
    list_url: "https://example.com/products"
    link_selector: "a.product-link"
    detail_selectors:
      title: "h1"
      price: "span.price"
      description: "div.description"
      image_url: "img.main@src"
      add_to_cart_url: "form.add-to-cart@action"
```

---

## Where to go next

* System overview and data flow: `docs/architecture.md`
* Operational guidance (scheduling, failure handling): `docs/operations.md`
* Test approach and fixtures usage: `docs/testing.md`
* Security, legal, and responsible scraping guidance: `docs/SECURITY_AND_LEGAL.md`