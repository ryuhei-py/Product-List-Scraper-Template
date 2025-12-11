# Operations

This document describes how to **run, schedule, monitor, and troubleshoot** the Product List Scraper Template in real environments.

It assumes that:

- You have already cloned the repository and can run Python 3.11+.
- You are familiar with basic command-line operations on your platform.
- You have read the high-level architecture overview in [`architecture.md`](architecture.md).

For legal and compliance aspects, see [`SECURITY_AND_LEGAL.md`](SECURITY_AND_LEGAL.md).

---

## Scope and responsibilities

This document is written for:

- Developers who will adapt this template to a specific client site.
- Operators (or yourself in the future) who will run and monitor the scraper on a schedule.

It covers:

- Environment setup and configuration management.
- Running the scraper manually.
- Scheduling periodic runs on Linux/macOS (cron) and Windows (Task Scheduler).
- Monitoring results (logs, exit codes, validation reports).
- Common troubleshooting patterns.
- Operational checklists.

It does **not** cover:

- Site-specific selector tuning (see `CONFIG_GUIDE.md`).
- Legal constraints on scraping (see `SECURITY_AND_LEGAL.md`).
- Advanced data pipelines (e.g., pushing to data warehouses), although this template can be embedded into such pipelines.

---

## Environment and prerequisites

### System requirements

- **Python**: 3.11 or higher (3.14 is also supported).
- **Git**: to clone the repository.
- **Network access**: outbound HTTP/HTTPS access to the target site(s).
- **Disk space**: enough to store CSV output and logs (typically small).

Recommended:

- A dedicated virtual environment per project (e.g., Python `venv`).
- Basic familiarity with your OS’s scheduler:
  - `cron` on Linux / macOS.
  - Task Scheduler on Windows.

### Repository layout (operational view)

For day-to-day operations, the most relevant paths are:

```text
Product-List-Scraper-Template/
├─ config/
│  ├─ targets.yml          # main targets configuration (copied from targets.example.yml)
│  └─ settings.yml         # optional global settings (copied from settings.example.yml)
├─ sample_output/
│  └─ products.sample.csv  # example output format
├─ src/
│  └─ product_scraper/
│     └─ cli.py            # main CLI entrypoint
├─ tests/                  # unit tests
├─ .env                    # optional, not committed (for secrets / proxies)
├─ .env.example            # example environment variables
├─ pyproject.toml
├─ requirements.txt
└─ README.md
```

The core operational artifacts are:

- `config/targets.yml` (required).
- `config/settings.yml` (optional but recommended).
- Output CSV/JSON files (in your chosen directory).
- Optional logs if you redirect stdout/stderr to files.

---

## First-time setup

The steps below assume a fresh clone on a machine where you want to run the scraper.

### Clone and create a virtual environment

From a terminal or PowerShell, clone the repository and set up the virtual environment:



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

# Install the package in editable mode so "python -m product_scraper.cli" works.
pip install -e .
```

You only need to create and activate the virtual environment once per machine. For subsequent runs, you just need to activate the venv and invoke the CLI.

### Create and edit config/targets.yml

Copy the example configuration:



```bash
# From repository root

# Windows
copy config/targets.example.yml config/targets.yml

# macOS / Linux
# cp config/targets.example.yml config/targets.yml
```

Then open `config/targets.yml` in your editor and:

- Set name for each target (e.g., "example-site").
- Set `list_url` to the site’s product list page.
- Set `link_selector` to the CSS selector for product links.
- Adjust `detail_selectors` to match the detail page structure.

See `CONFIG_GUIDE.md` for more details on configuration patterns.

### Optional: create and edit config/settings.yml

Copy the example:



```bash
# From repository root

# Windows
copy config/settings.example.yml config/settings.yml

# macOS / Linux
# cp config/settings.example.yml config/settings.yml
```

Then adjust values (e.g., timeouts, retries, logging):



```yaml
http:
  user_agent: "Mozilla/5.0 (compatible; ProductScraper/1.0)"
  timeout: 10
  max_retries: 3
  delay_seconds: 1.0

validation:
  enabled: true

logging:
  level: "INFO"
```

If `config/settings.yml` is absent, the scraper falls back to reasonable defaults.

### Optional: .env for secrets and proxies

If you need proxies or tokens, create `.env` in the project root (same directory as `pyproject.toml`):



```bash
# From repository root
copy .env.example .env
# or: cp .env.example .env
```

Edit `.env` and add any environment variables you need, for example:



```bash
HTTP_PROXY=http://user:pass@proxy.example.com:8080
HTTPS_PROXY=http://user:pass@proxy.example.com:8080
```

The CLI will automatically call `load_dotenv()` so these variables are available to the process.

---

## Running the scraper manually

### CLI entrypoint

Run the CLI module:



```bash
python -m product_scraper.cli
```

You must specify at least:

- `--config`: path to the targets YAML file.
- `--output`: path to the output CSV file.

Typical command from project root:



```bash
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products.csv
```

### CLI flags (summary)

| Flag | Required | Description | Example |
|------|----------|-------------|---------|
| `--config` | Yes | Path to the targets configuration YAML. | `--config config/targets.yml` |
| `--output` | Yes | Path to the output CSV file. | `--output sample_output/products.csv` |
| `--limit` | No | Maximum number of products to process (for quick tests). | `--limit 50` |
| `--dry-run` | No | If set, runs the pipeline but does not write the output file. | `--dry-run` |
| `--target-name` | No | Name of the target in `targets.yml` to run. If omitted, the first target is used. | `--target-name example-site` |

The CLI also automatically:

- Looks for `config/settings.yml` (optional).
- Loads environment variables from `.env` (optional).

### Typical usage patterns

#### Quick sanity check (dry-run & limit)

Use this when developing/selecting selectors:



```bash
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products.csv \
  --limit 20 \
  --dry-run
```

What happens:

- The scraper fetches list and detail pages for up to 20 products.
- It parses data and runs validation.
- It prints a quality report to stdout.
- No output file is written (dry-run).

This is ideal to confirm that:

- Selectors are correct.
- Requests succeed.
- Parsing yields reasonable values.

#### Full run for a single target

Once configuration is stable:



```bash
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products.csv
```

If your config defines multiple targets and you want a specific one:



```bash
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products_example.csv \
  --target-name example-site
```

#### Capturing logs and output

For operational runs, it’s common to capture stdout and stderr:



```bash
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products.csv \
  > logs/run_$(date +%Y%m%d_%H%M%S).log 2>&1
```

On Windows (PowerShell):



```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
python -m product_scraper.cli `
  --config config/targets.yml `
  --output sample_output/products.csv `
  *> "logs/run_$timestamp.log"
```

---

## Scheduling

### Linux / macOS: cron

Ensure:

- The repository path is fixed (e.g., `/opt/product-list-scraper`).
- The Python virtual environment is available.
- The config and settings files are configured and tested.

Edit the crontab:



```bash
crontab -e
```

Add an entry, for example to run every night at 03:30:



```bash
30 3 * * * cd /opt/product-list-scraper && \
  /opt/product-list-scraper/.venv/bin/python -m product_scraper.cli \
    --config config/targets.yml \
    --output data/products_$(date +\%Y\%m\%d).csv \
    >> logs/cron.log 2>&1
```

Notes:

- Use absolute paths for reliability.
- Combine date in the output filename to keep history.
- Append logs to `logs/cron.log` for review.

### Windows: Task Scheduler

Ensure:

- The repository is cloned at a stable path, e.g., `C:/scrapers/Product-List-Scraper-Template`.
- The virtual environment `.venv` is created inside the repo or in a known location.
- You can run the CLI successfully from PowerShell.

Create a basic scheduled task:

- Open “Task Scheduler”.
- Create a new task:
  - Trigger: e.g., daily at 03:30.
  - Action: "Start a program".
  - Program/script: `powershell.exe`

Arguments (example):



```powershell
-ExecutionPolicy Bypass -Command "
cd 'C:/scrapers/Product-List-Scraper-Template';
./.venv/Scripts/Activate.ps1;
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss';
python -m product_scraper.cli `
  --config config/targets.yml `
  --output 'sample_output/products_' + $timestamp + '.csv' `
  *> 'logs/run_' + $timestamp + '.log'
"
```

Start in: `C:/scrapers/Product-List-Scraper-Template`

Test the task manually (“Run” from Task Scheduler) and verify:

- A new CSV is generated under `sample_output`.
- A new log file appears under `logs`.
- Exit code 0 (success) is shown in the “Last Run Result”.

---

## Monitoring and health checks

### Exit codes

The CLI uses exit codes to signal overall success/failure:

- `0`: success.
- Non-0: failure (configuration error, fetch problem considered fatal, unexpected exception).

When integrating into schedulers or CI, always check the exit code.

### Logging

Logging is configured in the CLI. Logging level is determined by:

- `logging.level` in `config/settings.yml`, if present.
- Default: `INFO` when not specified.

Messages are emitted via Python’s logging module. Typical messages include:

- Start and end of runs.
- Number of product URLs discovered.
- Number of records exported.
- Warnings about skipped URLs or parse anomalies.

Operational recommendations:

- Redirect stdout/stderr to log files for scheduled runs.
- Use log rotation (either by filename pattern or external tools such as `logrotate`).

### Validation report

If `validation.enabled` is true in `settings.yml` (or not set at all), the scraper:

- Performs simple data-quality checks at the end of the run.
- Prints a text report to stdout:
  - Total number of records.
  - Missing values per field.

You can incorporate this report into your monitoring routine:

- Manually inspect after a change in configuration.
- For automation:
  - Parse the report from the log file and trigger alerts if missing rates exceed thresholds (outside this template’s scope).

---

## Troubleshooting

This section lists common issues and suggested steps.

### “Module not found” or import errors

Symptoms:

- `ModuleNotFoundError: No module named 'product_scraper'`
- CLI fails immediately.

Checks:

- Did you run `pip install -e .` inside the repository (with venv activated)?
- Is your virtual environment activated?
- Are you running `python -m product_scraper.cli` from within the environment where the package is installed?

Fix:

Re-activate the venv and run:



```bash
pip install -e .
```

### YAML parse errors

Symptoms:

- Error messages about invalid YAML when loading `config/targets.yml` or `config/settings.yml`.

Checks:

- Validate indentation and colons.
- Ensure lists are indicated with `-`.
- Confirm that the file is saved as UTF-8 without BOM.

Fix:

- Compare your file with the example (`targets.example.yml`, `settings.example.yml`).
- Use an online YAML validator if necessary.

### Config validation errors (ConfigError)

Symptoms:

- CLI prints messages like:
  - `Invalid config: Config must contain a non-empty 'targets' list.`
  - `Invalid config: Target at index 0 is missing 'list_url' or 'link_selector'.`

Checks:

- Open `config/targets.yml`.
- Ensure:
  - `targets` exists and is a non-empty list.
  - Each target is a mapping with `list_url`, `link_selector`, and `detail_selectors` (mapping).
  - Confirm that the target name passed via `--target-name` actually matches one defined in the config.

Fix:

- Update the YAML file to satisfy these requirements.
- Re-run the CLI.

### Network / fetch errors

Symptoms:

- Errors mentioning `FetchError` or HTTP status codes.
- Runs terminate early or skip many URLs.

Checks:

- Verify that the machine has network access to the target site.
- Check for firewalls or VPN/proxy requirements.
- Confirm that the target site is up and reachable in a browser.
- If using proxies, verify `HTTP_PROXY` / `HTTPS_PROXY` in `.env`.

Fix:

- Adjust HTTP settings in `config/settings.yml`:
  - Increase `timeout` or `max_retries` cautiously.
  - Add a specific `user_agent`.
  - Set `delay_seconds` to a small positive value to reduce load on the server.
- If appropriate and legal, configure proxies via `.env`.

### Selector / parsing issues

Symptoms:

- CSV is created but many fields are empty.
- Validation report shows high missing counts for key fields.

Checks:

- Inspect a sample detail page in your browser.
- Confirm that CSS selectors in `detail_selectors` match the structure.
- Check that `link_selector` actually points to the correct detail link elements.

Fix:

- Update `config/targets.yml` with correct selectors.
- Re-run in `--dry-run` mode with a small `--limit` and review the validation report.

### Output and file permissions

Symptoms:

- Errors when writing CSV (permission denied, path not found).
- Output file not created.

Checks:

- Ensure the directory of `--output` exists and is writable.
- On Windows, confirm that another program (e.g., Excel) does not lock the file from a previous run.

Fix:

- Create the output directory beforehand (e.g., `mkdir data`).
- Close any open CSV viewer or editor and re-run.

---

## Operational checklists

### Before first production run

- Confirm Python environment and dependencies are installed.
- Run pytest and ensure all tests pass:



```bash
pytest
```

- Configure `config/targets.yml` and verify selectors.
- Optionally configure `config/settings.yml`.
- Perform a small dry-run:



```bash
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products.csv \
  --limit 20 \
  --dry-run
```

- Review logs and validation report for obvious issues.

### Before enabling a scheduler

- Run the scraper manually with full configuration (no `--dry-run`).
- Confirm that CSV is created as expected.
- Verify that the logs (stdout/stderr) are captured and readable.
- Ensure absolute paths are used in cron or Task Scheduler.
- Verify that the scheduler user account has access to:
  - The repository directory.
  - The virtual environment.
  - The output directory.

### After configuration changes

- Re-run pytest if you changed code.
- Perform a limited run with `--limit` and `--dry-run` to ensure selectors still work.
- Monitor the next scheduled run closely (logs, CSV, validation report).

---

## Summary

From an operational standpoint, the Product List Scraper Template provides:

- A predictable CLI with config-driven behavior.
- Optional global settings via `settings.yml`.
- Basic logging and validation for visibility.
- Straightforward integration with cron and Task Scheduler.

By following the setup, scheduling, and troubleshooting practices in this document, you can run the scraper reliably and repeatedly in development, staging, and production environments.
