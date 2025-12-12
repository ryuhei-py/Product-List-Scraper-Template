# Product List Scraper Template
This document explains the Product List Scraper Template, its use cases, and how to run it as a portfolio-ready, config-driven scraper.

[![CI](https://github.com/ryuhei-py/Product-List-Scraper-Template/actions/workflows/ci.yml/badge.svg)](https://github.com/ryuhei-py/Product-List-Scraper-Template/actions/workflows/ci.yml) ![Python](https://img.shields.io/badge/python-3.11%2B-blue) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Portfolio highlights
This section lists the key traits of the template.

- Template-first design: add new targets by editing YAML instead of rewriting code.
- Two scraping modes: list-only (single request) and detail-follow (list → detail pages).
- Selector spec support: extract text or attributes via `@attr`, `::attr(name)`, and `::text`.
- Traceable datasets: records include `source_list_url`, plus `detail_url` in detail-follow mode; `*_url` fields are normalized when possible.
- Reliable exports: CSV headers are the stable union-of-keys across all records (handles heterogeneous records).
- Engineering signals: automated tests + linting, CI-ready workflow, and dedicated docs for architecture, ops, testing, and compliance.

---

## Overview and use cases
This section describes what the project solves and typical outputs.

This project solves the “repeatable scraping pipeline” problem: you need to scrape product/catalog data from one or many sites, enforce basic quality rules, and export a dataset in a predictable format.

Typical use cases:
- Scrape e-commerce product lists (title/price/image/product URL) into CSV for analysis.
- Build a client-ready scraper where the only per-client change is the config (selectors + URLs).
- Prototype a new data source quickly, then harden it with tests and operational settings.

Output:
- Primary output: CSV.
- Optional helpers: JSON / Excel (Excel requires optional deps; see “Tech stack” / “Quickstart”).

---

## Architecture at a glance
This section summarizes the pipeline and modules.

Core flow: **Config (targets + settings)** → **Fetch** → **Parse** → **Validate / Quality Report** → **Export**

Key modules (high-level):
- `Fetcher`: HTTP GET with retries/session reuse (settings-driven).
- `Parser(s)`: list-page parsing and field extraction (text/attr selector specs).
- `Validator`: basic record-quality checks (coverage, required fields, etc.).
- `Exporter`: CSV (union-of-keys header), plus optional JSON/Excel helpers.
- `CLI`: orchestrates modes, logging, limits, dry-run, and output.

See: `docs/architecture.md`.

---

## Tech stack
This section lists languages and tools used.

- Language: Python 3.11+.
- Core libraries: `requests`, `beautifulsoup4`, `PyYAML`, `python-dotenv`.
- Tooling: `pytest`, `ruff`, GitHub Actions (CI).

---

## Quickstart (install and first run)
This section describes setup and a first dry-run.

### Prerequisites
This subsection lists required tools.

- Python 3.11+
- `git`

### Install
This subsection shows installation commands.

# Clone the repository and create a virtual environment
```bash
git clone <YOUR_REPO_URL>
cd Product-List-Scraper-Template

python -m venv .venv
# Windows:
#   .\.venv\Scripts\activate
# macOS/Linux:
#   source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e .
```

### Optional (Excel export support)
This subsection explains how to enable Excel exports.

# Install Excel extras
```bash
pip install -e ".[excel]"
```

### First run (copy-paste)
This subsection shows a first dry-run using the example config.

# Run the CLI in dry-run mode with the example target
```bash
product-scraper --config config/targets.example.yml --output output/products.csv --dry-run
```

---

## Configuration (high-level)
This section explains the configuration layers.

This template is driven by three configuration layers:

1) `.env` (optional): environment-specific values not stored in YAML or Git; start from `.env.example` if needed.
2) `config/settings.yml` (runtime; typically gitignored): operational controls (timeouts, retries, optional backoff, logging, validation toggles, request delay, etc.). Recommended workflow: copy from `config/settings.example.yml` to `config/settings.yml`; keep `config/settings.yml` out of Git.
3) `config/targets.yml` (runtime; typically gitignored): defines scraping targets (URLs + selectors), choosing between list-only mode (`item_selector` + `item_fields`) or detail-follow mode (`link_selector` + `detail_selectors`). See `docs/CONFIG_GUIDE.md`.

---

## Usage examples
This section provides common CLI invocations.

1) Basic run (write CSV)

# Run a full scrape and write output
```bash
product-scraper --config config/targets.yml --output output/products.csv
```

2) Dry-run (no output file)

# Run without writing output
```bash
product-scraper --config config/targets.yml --output output/products.csv --dry-run
```

3) Limit records (fast iteration)

# Run with a limit for quicker testing
```bash
product-scraper --config config/targets.yml --output output/products.csv --limit 25
```

4) Select a target by name (multi-target config)

# Run a specific target
```bash
product-scraper --config config/targets.yml --output output/products.csv --target-name laptops-demo
```

---

## Extensibility and customization
This section outlines how to adapt the template.

Add a new site/target (recommended path):

1) Copy example configs (runtime files):

# Copy example configs
```bash
cp config/targets.example.yml config/targets.yml
cp config/settings.example.yml config/settings.yml
```

2) Add a new target entry under `targets:` in `config/targets.yml` and choose a mode:

- Option A: list-only mode (fast + stable). Use when the list page contains all required fields.

```yaml
targets:
  - name: my-target
    list_url: "https://example.com/catalog"
    item_selector: ".product-card"
    item_fields:
      title: ".title"
      price: ".price"
      image_url: "img@src"
      product_url: "a@href"
```

- Option B: detail-follow mode (richer fields). Use when you must visit each product page.

```yaml
targets:
  - name: my-target
    list_url: "https://example.com/catalog"
    link_selector: "a.product-link"
    detail_selectors:
      title: "h1"
      price: ".price"
      image_url: "img@src"
      description: ".description"
```

Update selector specs as needed:

- Text extraction: `.price` or `.price::text`
- Attribute extraction: `a@href` or `a::attr(href)`

Add or adjust tests:

- Parser behavior: `tests/test_parser.py`
- Config validation: `tests/test_config.py`
- CLI behavior: `tests/test_cli.py`

---

## Quality and reliability (tests / CI)
This section covers quality checks.

Run locally:

# Lint the code
```bash
ruff check src tests
```

# Run tests
```bash
pytest
```

CI (if enabled) should run `ruff check` and `pytest`. See `docs/testing.md`.

---

## Operations and production use
This section lists operational practices.

- Run via scheduler (cron / Task Scheduler / CI runner) with explicit config paths.
- Capture logs (stdout + structured logging if enabled).
- Use `--dry-run` to validate config changes safely.
- Store outputs outside the repo (for example, `output/`) and version datasets only when intended.
- See `docs/operations.md`.

---

## Security, legal, and compliance
This section reminds you of responsibilities.

You are responsible for scraping ethically and lawfully:

- Follow site Terms of Service and applicable laws.
- Respect rate limits and use polite access patterns.
- Avoid collecting personal data unless explicitly authorized.
- See `docs/SECURITY_AND_LEGAL.md`.

---

## Project structure
This section shows the repository layout.

```text
.
├── config/
│   ├── targets.example.yml
│   └── settings.example.yml
├── docs/
│   ├── architecture.md
│   ├── operations.md
│   ├── testing.md
│   ├── CONFIG_GUIDE.md
│   └── SECURITY_AND_LEGAL.md
├── sample_output/
│   └── products.sample.csv
├── src/
│   └── product_scraper/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── exporter.py
│       ├── fetcher.py
│       ├── parser.py
│       └── validator.py
└── tests/
    ├── test_cli.py
    ├── test_config.py
    ├── test_exporter.py
    ├── test_fetcher.py
    ├── test_parser.py
    └── test_validator.py
```

---

## Documentation index
This section links to related docs.

- Architecture: `docs/architecture.md`
- Operations: `docs/operations.md`
- Testing: `docs/testing.md`
- Configuration guide: `docs/CONFIG_GUIDE.md`
- Security / Legal: `docs/SECURITY_AND_LEGAL.md`

---

## Roadmap / possible improvements
This section lists future ideas.

- Pagination support (page discovery + max-pages + cursor-based APIs).
- Storage adapters (SQLite/Postgres) and incremental “diff” runs.
- Concurrency controls (bounded parallel detail fetch with politeness).
- Notifications (Slack/email) and structured run reports.
- Type checking (mypy) and richer schema validation.

---

## License
This section states the license.

MIT. See `LICENSE`.

---

## Author and contact
This section lists author information.

Ryuhei (ryuhei-py) – Python engineer focused on compliant scraping, automation, and data pipelines.

GitHub: ryuhei-py

---

_Last updated: 2025-12-12_
