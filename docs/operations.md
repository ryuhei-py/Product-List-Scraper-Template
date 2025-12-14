# Operations Guide

This document explains how to install, run, observe, schedule, and maintain **Product-List-Scraper-Template** safely and reliably. It is written to be practical for real delivery work and suitable for publishing as-is on GitHub.

---

## Contents

- [Scope and related docs](#scope-and-related-docs)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Runtime configuration](#runtime-configuration)
- [Run commands](#run-commands)
- [Output management](#output-management)
- [HTTP behavior and politeness controls](#http-behavior-and-politeness-controls)
- [Validation and quality reporting](#validation-and-quality-reporting)
- [Logging and observability](#logging-and-observability)
- [Exit codes and failure semantics](#exit-codes-and-failure-semantics)
- [Scheduling](#scheduling)
- [Maintenance workflow](#maintenance-workflow)
- [Troubleshooting](#troubleshooting)
- [Security, legal, and compliance reminders](#security-legal-and-compliance-reminders)
- [Delivery checklist](#delivery-checklist)
- [Appendix: Minimal configuration examples](#appendix-minimal-configuration-examples)

---

## Scope and related docs

This guide covers:

- installing the package and setting up a runtime environment
- configuring targets and operational settings
- running the CLI safely (including “safe iteration” patterns)
- output handling, logging, and failure handling
- scheduling and maintenance over time

Related documentation:

- Target schemas, selector syntax, and configuration validation rules → `docs/CONFIG_GUIDE.md`
- Architecture, data flow, and component responsibilities → `docs/architecture.md`
- Testing approach and how to run tests locally/CI → `docs/testing.md`
- Security/legal posture and responsible scraping guidelines → `docs/SECURITY_AND_LEGAL.md`

---

## Prerequisites

- Python **3.11+**
- pip (bundled with Python)

Recommended:

- A virtual environment (`venv`) per clone
- Git (for cloning and updates)

Supported operating systems:

- Windows / macOS / Linux

---

## Installation

### Recommended: editable install (best for iteration)

Create and activate a virtual environment, then install the project in editable mode.

#### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
````

#### macOS / Linux (bash/zsh)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

This installs:

* runtime dependencies
* development tooling (`ruff`, `pytest`, etc.)

### Runtime-only install (minimal)

If the environment is strictly “run-only” and you do not need lint/tests:

```bash
pip install -e .
```

### Optional: Excel export support

The CLI exports **CSV**. The codebase also includes an Excel exporter helper (not wired into the CLI by default) that requires optional dependencies.

Install Excel extras:

```bash
pip install -e ".[excel]"
```

---

## Runtime configuration

This template is designed so most adaptation happens in YAML, not in Python code.

### Files at a glance

Committed examples:

* `config/targets.example.yml`
* `config/settings.example.yml`
* `.env.example`

Recommended runtime files (local / client-specific):

* `config/targets.yml`
* `config/settings.yml`
* `.env` (optional)

Create runtime files from the examples:

#### Windows (PowerShell)

```powershell
copy config\targets.example.yml config\targets.yml
copy config\settings.example.yml config\settings.yml
copy .env.example .env
```

#### macOS / Linux

```bash
cp config/targets.example.yml config/targets.yml
cp config/settings.example.yml config/settings.yml
cp .env.example .env
```

### Targets configuration (`--config`)

The CLI loads targets from the path passed to `--config`.

* If you **do not** pass `--config`, it defaults to `config/targets.example.yml`.
* If multiple targets exist, you can select one by name using `--target-name`.

Targets support two modes:

1. **List-only mode**

   * Fetch the list page once and parse repeated items using:

     * `item_selector`
     * `item_fields` (field → selector spec)

2. **Detail-follow mode**

   * Fetch the list page, extract links with:

     * `link_selector`
   * Fetch each detail page and extract fields with:

     * `detail_selectors` (field → selector spec)

See `docs/CONFIG_GUIDE.md` for the exact schemas and selector spec syntax (text vs attribute extraction).

### Settings configuration (`config/settings.yml`)

Operational settings are loaded from:

* `config/settings.yml` (fixed path)

Notes:

* If `config/settings.yml` does **not** exist, the run still works (settings fall back to defaults).
* If the file exists, it must parse to a top-level YAML mapping (object).

Supported settings (from the example file):

* `http.*`: User-Agent, timeout, attempts, delay, backoff/jitter
* `output.*`: default output directory and filename (used if `--output` is omitted)
* `validation.enabled`: enable/disable quality reporting
* `logging.level`: logging verbosity

### Environment variables and `.env`

The CLI loads `.env` automatically (via `python-dotenv`).

Common operational environment variables:

* `HTTP_PROXY`
* `HTTPS_PROXY`

Guidance:

* Do not commit secrets into `.env`.
* Prefer environment-specific secret injection (CI secrets, OS-level env vars, secret managers).
* If using proxies, ensure authorization and compliance with the target site and your client scope.

---

## Run commands

### Help

```bash
product-scraper --help
```

### Basic run (writes a CSV)

```bash
product-scraper --config config/targets.yml --output output/runs/products.csv
```

If `--target-name` is omitted, the **first** target in the config is used.

### Dry run (safe iteration)

Dry-run still **fetches and parses** pages, and still prints the quality report (unless disabled), but it **does not write** the CSV output.

```bash
product-scraper --config config/targets.yml --dry-run --limit 10
```

Use dry-run when:

* tuning selectors
* validating config changes
* checking whether a target has drifted (HTML changed)

### Limit for faster iteration and lower load

In list-only mode, the limit caps the number of parsed items.
In detail-follow mode, the limit caps the number of detail links processed.

```bash
product-scraper --config config/targets.yml --limit 20 --dry-run
```

### Select a target by name

```bash
product-scraper --config config/targets.yml --target-name my-shop --dry-run --limit 20
```

### Demo mode (offline, deterministic)

Demo mode runs using local HTML fixtures in `fixtures/` and does not use network access.

```bash
product-scraper --demo
```

Demo mode is useful for:

* deterministic pipeline demonstration
* validating installation and wiring without relying on external websites
* portfolio-safe runs in restricted environments

---

## Output management

### Output path precedence (deterministic)

The output path is resolved in the following order:

1. `--output` CLI argument
2. `config/settings.yml` → `output.directory` + `output.csv_filename`
3. Fallback:

   * normal runs: `sample_output/products.csv`
   * demo runs: `sample_output/products.demo.csv`

### Output data contract and traceability

The pipeline adds traceability fields:

* `source_list_url` is always present (both modes)
* `detail_url` is present in detail-follow mode (the resolved URL fetched)

### URL normalization (`*_url` convention)

Any field name ending with `_url` is treated as URL-like and normalized to an absolute URL using `urljoin()` when possible.

* List-only mode uses `list_url` as the base.
* Detail-follow mode uses the current `detail_url` as the base for detail fields.

Operational tip: use `_url` suffix consistently (e.g., `image_url`, `product_url`) so normalization is applied.

### Output hygiene for scheduled runs

Recommended practices:

* Write outputs outside the repository root or into a dedicated run directory (e.g., `output/runs/`).
* Use timestamped filenames to keep runs auditable and avoid accidental overwrites.
* Apply a retention policy (e.g., keep last 30–90 runs depending on requirements).

Example timestamped output:

```bash
ts=$(date +"%Y%m%d_%H%M%S")
product-scraper --config config/targets.yml --output "output/runs/products_${ts}.csv"
```

---

## HTTP behavior and politeness controls

HTTP behavior is configured under `http:` in `config/settings.yml`.

### User-Agent

Set a descriptive User-Agent:

```yaml
http:
  user_agent: "Mozilla/5.0 (compatible; ProductListScraper/1.0)"
```

### Timeout

```yaml
http:
  timeout: 10
```

Tune based on target responsiveness and scheduler expectations.

### Attempts, retries, and backoff

Key settings:

```yaml
http:
  max_retries: 3
  retry_backoff_seconds: 0.0
  retry_backoff_multiplier: 2.0
  retry_jitter_seconds: 0.0
```

Important semantics:

* `max_retries` is the maximum **attempts total** (attempts 1..max_retries).
* Retried conditions:

  * HTTP `429`
  * HTTP `5xx`
  * transient request exceptions
* Most other `4xx` responses are not retried.

Backoff behavior:

* If `retry_backoff_seconds > 0`, backoff grows by multiplier per attempt and can include jitter.

### Delay (politeness / rate limiting)

```yaml
http:
  delay_seconds: 1.0
```

Nuance:

* `delay_seconds` is applied **between detail page fetches** in detail-follow mode.
* List-only mode does not apply inter-request delay because it fetches only the list page once.

### Proxies

If you need a proxy, use environment variables:

* `HTTP_PROXY`
* `HTTPS_PROXY`

Only use proxies if authorized and consistent with the target’s policies and client scope.

---

## Validation and quality reporting

Validation is enabled by default (see `config/settings.example.yml`):

```yaml
validation:
  enabled: true
```

When enabled, the run prints a report including:

* total records
* set of fields observed
* missing counts per field (None/empty string)

How to use the report operationally:

* A spike in missing counts often indicates selector drift or HTML changes.
* A drop in record count often indicates list parsing problems, blocking, or site changes.

You can disable validation (not recommended unless you have stronger external monitoring):

```yaml
validation:
  enabled: false
```

---

## Logging and observability

### Logging level

```yaml
logging:
  level: "INFO"
```

Supported levels include `DEBUG`, `INFO`, `WARNING`, `ERROR`.

### Output streams (practical notes)

Operationally relevant conventions:

* Quality report is printed to stdout (via `print`).
* Many errors and skip messages are printed to stderr.
* Python logging typically emits to stderr by default.

Recommendation:

* In schedulers, capture both stdout and stderr.
* Store logs alongside outputs for auditing.

### Minimal monitoring signals (recommended)

For scheduled runs, treat these as primary signals:

* non-zero exit code
* “No records parsed” failure
* repeated 429/5xx or increasing retries
* sustained high missing counts or sudden record-count drops

---

## Exit codes and failure semantics

### Exit codes

* `0`: success
* `1`: failure (configuration errors, fatal fetch errors, zero records parsed, or unexpected exceptions)

### Fatal vs non-fatal behavior (detail-follow mode)

Fatal:

* invalid config
* list page fetch failure
* settings load failure (malformed settings file)
* no records produced after processing

Non-fatal in detail-follow mode:

* individual detail page fetch failures are **skipped**
* the run can still succeed if at least one record is produced

Operational implication:

* If your requirements demand “all details must be fetched,” enforce this in downstream checks or extend the pipeline to fail on any detail failure.

---

## Scheduling

### Linux/macOS cron (example)

Nightly run with timestamped output and combined log capture:

```bash
0 2 * * * cd /path/to/repo && \
  . .venv/bin/activate && \
  ts=$(date +"%Y%m%d_%H%M%S") && \
  product-scraper --config config/targets.yml --output "output/runs/products_${ts}.csv" \
  >> "output/logs/run_${ts}.log" 2>&1
```

Ensure directories exist:

```bash
mkdir -p output/runs output/logs
```

### Windows Task Scheduler (PowerShell pattern)

Example command pattern (adjust paths to your environment):

```powershell
-Command "cd C:\path\to\repo; .\.venv\Scripts\Activate.ps1; `
$ts=Get-Date -Format 'yyyyMMdd_HHmmss'; `
New-Item -ItemType Directory -Force -Path output\runs, output\logs | Out-Null; `
product-scraper --config config\targets.yml --output output\runs\products_$ts.csv *> output\logs\run_$ts.log"
```

### CI-based scheduled runs (when appropriate)

CI scheduling can be appropriate for lightweight jobs when:

* credentials and environment variables are handled securely
* output storage is defined (artifact upload, external storage, or database)
* network access is allowed and compliant for the use case

Avoid using CI schedules if:

* you cannot control IP reputation or network policy requirements
* outputs must be persisted long-term but artifacts are insufficient

---

## Maintenance workflow

Web pages change. Operational success depends on a tight drift-response loop.

### Standard response when a target breaks

1. Run a safe diagnostic:

```bash
product-scraper --config config/targets.yml --target-name <NAME> --dry-run --limit 10
```

2. If record count drops or missing counts spike:

* inspect current HTML structure (minimize data collection)
* update selectors in `config/targets.yml`
* re-run dry-run
* run a full run when stable

3. Commit changes in small, reviewable diffs:

* update only the selectors you need
* keep target configs readable and well-scoped

### Selector drift minimization tips

Prefer selectors that are stable over time:

* `data-*` attributes intended for automation/testing
* stable IDs
* stable class names (avoid brittle deep DOM paths)

---

## Troubleshooting

### Configuration validation errors

Common causes:

* missing required keys for the selected mode
* empty selector strings
* duplicate target names

Fix:

* validate your YAML against `docs/CONFIG_GUIDE.md`
* use `--dry-run --limit 1` after changes

### “It runs but returns empty records”

Most often: selector mismatch or HTML drift.

Steps:

1. Dry-run with a small limit:

```bash
product-scraper --config config/targets.yml --dry-run --limit 10
```

2. Confirm selectors against current HTML.

### Relative URLs appear in output

Ensure the field name ends with `_url` (e.g., `product_url`, `image_url`).
The pipeline normalizes `*_url` fields to absolute URLs when possible.

### 403 / 429 / 5xx responses

* Confirm authorization and policy constraints for the target.
* Increase politeness:

  * raise `delay_seconds`
  * add backoff/jitter
* Avoid aggressive behavior.

### Timeouts

* Increase `http.timeout`.
* Reduce load while debugging with `--limit`.

### Output write errors

* Ensure output directories exist and have permissions.
* Use an explicit `--output` path to avoid ambiguity.

### What to collect before escalation

When escalating an issue, capture:

* the exact command used (redact sensitive values)
* target name and list URL
* relevant settings (redacted)
* stderr/log excerpts around the failure
* a minimal HTML snippet if permitted and necessary

---

## Security, legal, and compliance reminders

This template is intentionally conservative: it provides operational controls (delay, retries, UA) and avoids bypass tooling. Operate responsibly:

* follow Terms of Service and site policies
* respect robots.txt expectations where applicable
* minimize load and data collection
* avoid collecting personal data unless explicitly authorized and necessary
* do not attempt to bypass access controls or anti-bot protections

See the canonical guidance: `docs/SECURITY_AND_LEGAL.md`.

---

## Delivery checklist

Before presenting this repository as a finished deliverable:

* [ ] CLI runs on a clean machine following README/Docs
* [ ] `config/targets.yml` validates and selects the intended mode
* [ ] `--dry-run --limit N` works for fast iteration
* [ ] `*_url` fields normalize as expected
* [ ] Output path precedence is understood and documented in your runbook
* [ ] `delay_seconds`, retries, and timeouts are tuned for the target
* [ ] Logs are captured in scheduled runs (stdout + stderr)
* [ ] Non-zero exit codes are treated as failures in automation
* [ ] Compliance posture is acknowledged (ToS/robots/data minimization)

---

## Appendix: Minimal configuration examples

These examples are intentionally minimal. For full schema rules and selector spec syntax, see `docs/CONFIG_GUIDE.md`.

### List-only target (minimal)

```yaml
targets:
  - name: example-list
    list_url: "https://example.com/products"
    item_selector: "div.product-card"
    item_fields:
      title: "a.title@title"
      price: ".price"
      product_url: "a.title@href"
      image_url: "img@src"
```

### Detail-follow target (minimal)

```yaml
targets:
  - name: example-detail
    list_url: "https://example.com/products"
    link_selector: "a.product-link"
    detail_selectors:
      title: "h1"
      price: ".price"
      description: ".description"
      image_url: "img@src"
```

### Settings (minimal)

```yaml
http:
  user_agent: "Mozilla/5.0 (compatible; ProductListScraper/1.0)"
  timeout: 10
  max_retries: 3
  delay_seconds: 1.0
  retry_backoff_seconds: 0.0
  retry_backoff_multiplier: 2.0
  retry_jitter_seconds: 0.0

output:
  directory: "output/runs"
  csv_filename: "products.csv"

validation:
  enabled: true

logging:
  level: "INFO"
```
