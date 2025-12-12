# Product List Scraper Template
This document explains the Product List Scraper Template, its use cases, and how to run it as a portfolio-ready, config-driven scraper.

[![CI](https://github.com/ryuhei-py/Product-List-Scraper-Template/actions/workflows/ci.yml/badge.svg)](https://github.com/ryuhei-py/Product-List-Scraper-Template/actions/workflows/ci.yml) ![Python](https://img.shields.io/badge/python-3.11%2B-blue) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Portfolio highlights
This section surfaces quick proof points for clients and hiring managers.

- Config-driven: new targets via YAML (list-only or detail-follow) with selector-spec text/attr extraction.
- Layered architecture: Fetcher, Parsers, Exporter, Validator, CLI; clean separation and testable boundaries.
- Validation and traceability: `source_list_url`/`detail_url`, `*_url` normalization, and quality reporting.
- CI and tests: pytest + Ruff linting; GitHub Actions workflow ready to run.
- Extensible: optional Excel export, reusable parser/extractor, and union-of-keys CSV for heterogeneous data.
- Compliance-aware posture: delays/retries/backoff knobs and clear guidance in docs.


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

## Example output
This section shows a representative CSV snippet (see `sample_output/products.sample.csv` and `sample_output/products.demo.csv`).

```csv
title,price,image_url,product_url,source_list_url,detail_url
Product One,$10.00,https://example.com/img1.jpg,https://example.com/p1,https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops,
Product Two,$20.00,https://example.com/img2.jpg,https://example.com/p2,https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops,
Demo Item,$9.99,file:///fixtures/images/product1.jpg,file:///fixtures/detail_1.html,file:///fixtures/list.html,file:///fixtures/detail_1.html
```

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
pip install -e ".[dev]"
```

### Optional (Excel export support)
This subsection explains how to enable Excel exports.

# Install Excel extras
```bash
pip install -e ".[excel]"
```

### First run (copy-paste)
This subsection shows a first dry-run using the example config.

# Run the CLI in dry-run mode with the example target (explicit output path)
```bash
product-scraper --config config/targets.example.yml --output output/products.csv --dry-run
```

# Or rely on settings.yml output defaults (directory + csv_filename)
```bash
product-scraper --config config/targets.example.yml --dry-run
```

### Demo (offline)
This subsection shows an offline demo that uses bundled fixtures.

# Run the offline demo with bundled HTML (no network needed)
```bash
python -m product_scraper.cli --demo --output sample_output/products.demo.csv
```

### Validate the setup (lint and tests)
This subsection verifies the environment with linting and tests.

# Lint the code
```bash
ruff check src tests
```

# Run the test suite
```bash
pytest
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

## Extensibility
This section gives a five-step guide to add a new target.

1) Copy example configs to runtime files:
```bash
cp config/targets.example.yml config/targets.yml
cp config/settings.example.yml config/settings.yml
```
2) Add a target under `targets:` with either list-only (`item_selector` + `item_fields`) or detail-follow (`link_selector` + `detail_selectors`) selectors.
3) Run a dry-run with a small limit to verify selectors:
```bash
product-scraper --config config/targets.yml --output output/products.csv --limit 10 --dry-run
```
4) Check the validation report and sample records (`*_url` normalization, required fields present).
5) Run the full export (remove `--dry-run` and adjust `--output` as needed).

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
