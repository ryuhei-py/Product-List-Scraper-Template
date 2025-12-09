# Product List Scraper Template

[![CI](https://github.com/ryuhei-py/Product-List-Scraper-Template/actions/workflows/ci.yml/badge.svg)](https://github.com/ryuhei-py/Product-List-Scraper-Template/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A reusable, configurable product / catalog list scraper template for Python.

This repository is designed as a **portfolio-ready, production-oriented template** you can quickly adapt for real client projects (e.g., Upwork jobs) by changing only the configuration files, not the core code.

---

## 1. What is this?

The Product List Scraper Template is a generic pipeline for:

- Fetching one or more product-list pages from an e-commerce or catalog site
- Extracting product detail URLs from those list pages
- Fetching each product detail page
- Parsing structured fields (title, price, image URL, description, etc.)
- Exporting the final dataset to CSV / JSON
- Running basic data-quality validation

It is **not tied to any specific site**.  
All site-specific details (URLs, selectors, pagination) live in YAML config files.

---

## 2. Why use this template?

Typical scraping projects repeat the same patterns:

- HTTP requests with retry & headers
- List-page parsing to discover item URLs
- Detail-page parsing for structured fields
- CSV / Excel exports
- Basic validation, logging, and operational notes

This template:

- Encapsulates those patterns into well-separated modules
- Uses a **config-driven** approach for new sites
- Comes with tests and documentation
- Shows a clear **architecture and development workflow** to clients

You can fork this repository and adapt it to specific scraping jobs by:

- Copying and editing `config/targets.example.yml` into a new `config/targets.yml`
- Adjusting selectors and URLs
- Extending or swapping modules as needed

---

## 3. Features

- **Config-driven**:
  - Targets and selectors defined in YAML (no hard-coded site logic)
- **Layered architecture**:
  - `Fetcher` → `ListPageParser` → `DetailPageParser` → `Exporter` → `Validator` → `CLI`
- **Multiple output formats**:
  - CSV (standard), JSON (optional)
- **Data validation**:
  - Per-field missing counts and a human-readable quality report
- **Tested**:
  - Pytest-based test suite for core components
- **Portfolio-ready**:
  - Clear project structure and documentation suitable for client review

For more details on components and their interactions, see  
[`docs/architecture.md`](docs/architecture.md).

---

## 4. Quickstart

### 4.1 Requirements

- Python 3.11+ (3.14 also supported)
- `git`
- Recommended: a virtual environment (`venv`)

### 4.2 Clone and set up

Run these environment setup commands from the project root:

```bash
git clone https://github.com/ryuhei-py/Product-List-Scraper-Template.git
cd Product-List-Scraper-Template

python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4.3 Configure a target site

Copy the example config and adapt it:

```bash
# from project root
copy config/targets.example.yml config/targets.yml       # Windows
# or:
cp config/targets.example.yml config/targets.yml         # macOS / Linux
```

Then edit `config/targets.yml`:

- Set the list page URL(s) for the site.
- Set the CSS selector for product links on the list page.
- Set the CSS selectors for each detail field (title, price, etc.).
- Optionally adjust pagination and other options if supported.

See `docs/CONFIG_GUIDE.md` for the full config specification.

### 4.4 Run a sample scrape

The main entrypoint is the CLI module:

```bash
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products.csv
```

This will:

- Load the config
- Fetch list page(s)
- Extract product URLs
- Fetch and parse product detail pages
- Export records to `sample_output/products.csv`
- Run validation and print a quality report to stdout

If scraping succeeds, you should see the CSV file and a short summary report.

## 5. Configuration overview

The template uses two main YAML configs:

- `config/targets.yml`  
  Site-specific scraping configuration:
  - list page URLs
  - selectors for list pages and detail pages
  - optional pagination information

- `config/settings.yml` (optional)  
  Global operational settings:
  - HTTP timeout, retry count, delay between requests
  - default output directory and filename
  - validation / logging toggles

See `docs/CONFIG_GUIDE.md` for details on all fields.

## 6. Project layout

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
│
├─ config/
│  ├─ targets.example.yml
│  └─ settings.example.yml
│
├─ sample_output/
│  └─ products.sample.csv
│
├─ docs/
│  ├─ architecture.md
│  ├─ operations.md
│  ├─ testing.md
│  ├─ CONFIG_GUIDE.md
│  └─ SECURITY_AND_LEGAL.md
│
├─ tests/
│  ├─ conftest.py
│  ├─ test_fetcher.py
│  ├─ test_parser.py
│  ├─ test_exporter.py
│  └─ test_validator.py
│
├─ .github/
│  └─ workflows/
│     └─ ci.yml
│
├─ .env.example
├─ .gitignore
├─ pyproject.toml
├─ requirements.txt
├─ LICENSE
└─ README.md
```

## 7. Development & testing

Install dev dependencies (already in `requirements.txt`):

```bash
pytest
```

Run the full test suite:

```bash
pytest
```

Code style and linting can be integrated via `ruff` or other tools through CI (see `.github/workflows/ci.yml`).

## 8. License

This template is provided under the MIT License.  
See `LICENSE` for details.
