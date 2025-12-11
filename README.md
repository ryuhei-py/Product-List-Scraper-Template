# Product List Scraper Template
[![CI](https://github.com/ryuhei-py/Product-List-Scraper-Template/actions/workflows/ci.yml/badge.svg)](https://github.com/ryuhei-py/Product-List-Scraper-Template/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A reusable, configurable product / catalog list scraper template for Python.

This repository is designed as a **portfolio-ready, production-oriented template** that you can quickly adapt for real client projects (e.g., Upwork jobs) by changing configuration files instead of rewriting core code.

---

## What is this?

The Product List Scraper Template is a generic pipeline for:

- Fetching one or more product-list pages from an e-commerce or catalog site
- Extracting product detail URLs from those list pages
- Fetching each product detail page
- Parsing structured fields (title, price, image URL, description, etc.)
- Exporting the final dataset to CSV (and optionally JSON)
- Running basic data-quality validation and printing a quality report

It is **not tied to any specific site**. All site-specific details (URLs, selectors, pagination rules, limits, etc.) live in YAML config files.

---

## Why use this template?

Typical scraping projects repeat the same patterns:

- HTTP requests with retries and headers
- List-page parsing to discover item URLs
- Detail-page parsing for structured fields
- CSV / JSON exports and basic validation
- Operational notes (how to run, schedule, and monitor the job)

This template:

- Encapsulates those patterns into **well-separated modules**
- Uses a **config-driven** approach for new sites
- Comes with tests and documentation
- Makes your architecture and workflow **visible to clients** (great for portfolios)

You can fork this repository and adapt it to specific scraping jobs by:

- Copying and editing `config/targets.example.yml` into a project-specific `config/targets.yml`
- Optionally adding a `config/settings.yml` for HTTP, validation, and logging defaults
- Adjusting selectors and URLs for each site
- Extending or swapping modules as needed (e.g., new exporters, different fetchers)

---

## Features

- **Config-driven**:
  - Site-specific configuration in YAML (`config/targets.yml`, `config/settings.yml`)
  - No hard-coded selectors in the core logic
- **Layered architecture**:
  - `Fetcher` → `ListPageParser` → `DetailPageParser` → `Exporter` → `Validator` → `CLI`
  - Each layer has a clear responsibility
- **Multiple output formats**:
  - CSV (standard)
  - JSON (optional extension point)
- **Data validation**:
  - Per-field missing counts
  - Human-readable quality report (summary of record counts and missing data)
- **Operational hooks**:
  - Optional global settings via `config/settings.yml` (HTTP, validation, logging)
  - Environment variables loaded from `.env` (e.g., proxies, tokens) if present
- **CLI ergonomics**:
  - `--config` to select the YAML config file
  - `--output` to control the CSV output path
  - `--limit` to cap the number of detail pages processed
  - `--dry-run` to exercise the pipeline without writing output
  - `--target-name` (optional) to select a specific target by name
- **Tested**:
  - Pytest-based test suite for core components
- **Portfolio-ready**:
  - Clear project structure and documentation suitable for client review
  - Architecture and operational docs in `docs/`

For more details on components and their interactions, see `docs/architecture.md`.

---

## Quickstart

### Requirements

- Python 3.11+ (3.14 is also supported)
- `git`
- Recommended: a virtual environment (`venv`)

### Clone and set up

From a terminal, clone the repository and create the virtual environment:



```bash
git clone https://github.com/ryuhei-py/Product-List-Scraper-Template.git
cd Product-List-Scraper-Template

python -m venv .venv
# Windows:
#   ./.venv/Scripts/activate
# macOS / Linux:
#   source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

# Install the package in editable mode so "python -m product_scraper.cli"
# works from this clone.
pip install -e .
```

### Configure a target site (`config/targets.yml`)

Copy the example config and adapt it for your site:



```bash
# from project root

# Windows (PowerShell / cmd)
copy config/targets.example.yml config/targets.yml

# macOS / Linux
# cp config/targets.example.yml config/targets.yml
```

Then edit `config/targets.yml`. A minimal example:

yaml



```yaml
targets:
  - name: example-site
    list_url: "https://example.com/products"
    link_selector: "a.product-link"
    detail_selectors:
      title: "h1.product-title"
      price: ".price"
      image_url: "img.product-image"
      description: ".description"
```

`name` is an identifier for the target (used by `--target-name`).

`list_url` is the product list page.

`link_selector` is a CSS selector for links to product detail pages.

`detail_selectors` maps field names to CSS selectors on the detail page.

You can define multiple targets in the `targets` list and select them via `--target-name`. Advanced configuration options (pagination, extra selectors, limits, etc.) are described in `docs/CONFIG_GUIDE.md`.

### Optional: configure global settings (`config/settings.yml`)

Global operational settings (HTTP, validation, logging, etc.) can be configured in `config/settings.yml`.

Start with the example:



```bash
# from project root

# Windows
copy config/settings.example.yml config/settings.yml

# macOS / Linux
# cp config/settings.example.yml config/settings.yml
```

Then edit `config/settings.yml`. A typical structure is:

yaml



```yaml
http:
  user_agent: "Mozilla/5.0 (compatible; ProductScraper/1.0)"
  timeout: 10          # seconds
  max_retries: 3
  delay_seconds: 1.0   # delay between requests

output:
  directory: "sample_output"
  csv_filename: "products.csv"
  json_filename: "products.json"  # optional

validation:
  enabled: true

logging:
  level: "INFO"  # DEBUG / INFO / WARNING / ERROR
```

The core CLI uses:

- `http.*` to configure the Fetcher (timeout, retries, headers, delay)
- `validation.enabled` to decide whether to run and print the validation report
- `logging.level` to configure Python’s logging level

The `output.*` section shows a recommended schema for organizing output paths; you can extend the CLI or exporter to consume these values if needed. See `docs/CONFIG_GUIDE.md` for details.

### Optional: environment variables (`.env`)

If a `.env` file exists in the project root, environment variables will be loaded before the scraper runs. Typical uses:

- HTTP proxies (`HTTP_PROXY`, `HTTPS_PROXY`)
- Authentication tokens or other secrets
- Override-style variables for custom extensions

The template does not require any environment variables by default.

### Run a sample scrape

Run the CLI module with configuration and output paths:



```bash
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products.csv
```

This will:

- Load `config/targets.yml`
- Load `config/settings.yml` if present (for HTTP, validation, and logging)
- Fetch the list page(s)
- Extract product URLs
- Fetch and parse product detail pages
- Export records to `sample_output/products.csv`
- Run validation and print a quality report to stdout

You can further control the run with:



```bash
# Limit the number of products for a quick test
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products.csv \
  --limit 50

# Select a specific target by name (if multiple are defined)
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products.csv \
  --target-name example-site

# Dry run (no CSV is written; useful for debugging selectors)
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products.csv \
  --dry-run
```

On success, you should see a CSV file under `sample_output/` and a small data-quality report printed to stdout. A non-zero exit code indicates an error (e.g., config issues or fetch failures).

---

## Configuration overview

The template uses two main YAML configuration files:

- `config/targets.yml` (required)  
  Describes what to scrape:
  - `targets` list (one or more scraping targets)
  - For each target:
    - `name` (identifier)
    - `list_url`
    - `link_selector`
    - `detail_selectors` (field → CSS selector)
    - Optional advanced fields (pagination, extra selectors, limits, etc.)
- `config/settings.yml` (optional)  
  Describes global operational settings:
  - `http` (timeout, retries, headers, delay)
  - `validation` (on/off)
  - `logging` (log level)
  - `output` (recommended structure for file locations)

See `docs/CONFIG_GUIDE.md` for full field descriptions and advanced patterns.

---

## Project layout

text



```text
Product-List-Scraper-Template/
├─ src/
│  └─ product_scraper/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ fetcher.py
│     ├─ parser.py
│     ├─ exporter.py
│     ├─ validator.py
│     └─ cli.py
├─ config/
│  ├─ targets.example.yml
│  └─ settings.example.yml
├─ sample_output/
│  └─ products.sample.csv
├─ docs/
│  ├─ architecture.md
│  ├─ operations.md
│  ├─ testing.md
│  ├─ CONFIG_GUIDE.md
│  └─ SECURITY_AND_LEGAL.md
├─ tests/
│  ├─ conftest.py
│  ├─ test_fetcher.py
│  ├─ test_parser.py
│  ├─ test_exporter.py
│  └─ test_validator.py
├─ .github/
│  └─ workflows/
│     └─ ci.yml
├─ .env.example
├─ .gitignore
├─ pyproject.toml
├─ requirements.txt
├─ LICENSE
└─ README.md
```

---

## Development and testing

Install development dependencies (already included in `requirements.txt`), then run the test suite:



```bash
# from project root, with venv activated
pytest
```

Run the full test suite:



```bash
pytest
```

If you have `ruff` installed (either globally or in your venv), you can lint the code:



```bash
ruff src tests
```

The CI workflow (`.github/workflows/ci.yml`) runs linting and tests automatically on pushes and pull requests.

---

## License

This template is provided under the MIT License. See `LICENSE` for full terms.
