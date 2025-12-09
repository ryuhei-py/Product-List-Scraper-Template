# Operations - Running and Scheduling the Scraper

This document explains how to run the Product List Scraper Template locally and how to schedule it for periodic execution.

---

## 1. Local execution

This section covers local setup and execution steps.

### 1.1 Environment setup

From the project root, create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

If you have additional dev tools (e.g., ruff), they can be installed via `pyproject.toml` or extra requirements.

### 1.2 Configuration

Copy the example config and prepare it for your target site:

```bash
copy config/targets.example.yml config/targets.yml       # Windows
# cp config/targets.example.yml config/targets.yml      # macOS / Linux
```

Edit `config/targets.yml` to match your target site:

- list page URL(s)
- link selector for product URLs
- detail selectors for fields (title, price, etc.)
- optional pagination and limits

Optionally copy and adjust global settings:

```bash
copy config/settings.example.yml config/settings.yml
```

Then tune HTTP, output, and validation settings.

### 1.3 Running the CLI

The primary entrypoint is the CLI module:

```bash
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products.csv
```

`--config` points to the YAML config describing what to scrape.  
`--output` points to the CSV file to generate (directories will be created if needed).

On success, you should see:

- A CSV file under `sample_output/`
- A small data-quality report printed to stdout

---

## 2. Scheduling on Linux / macOS (cron)

This section shows how to schedule runs with cron.

### 2.1 Basic cron job

Ensure the project directory and virtual environment are set up. Identify the full paths:

- Project: `/home/username/Product-List-Scraper-Template`
- Python: `/home/username/Product-List-Scraper-Template/.venv/bin/python`

Open your crontab:

```bash
crontab -e
```

Add a line to run the scraper every day at 03:00:

```cron
0 3 * * * cd /home/username/Product-List-Scraper-Template && ./.venv/bin/python -m product_scraper.cli --config config/targets.yml --output sample_output/products.csv >> logs/scraper.log 2>&1
```

Notes:

- `cd` ensures the working directory is the project root.
- Output is appended to `logs/scraper.log` (create `logs/` if needed).
- You can use timestamped filenames in a wrapper script if you want daily archives.

---

## 3. Scheduling on Windows (Task Scheduler)

This section explains scheduling with Task Scheduler.

### 3.1 Prepare a wrapper script

Create a simple batch file (e.g., `run_scraper.bat`) in the project root:

```bat
@echo off
cd /d C:/Users/USERNAME/python-projects/Product-List-Scraper-Template
call ./.venv/Scripts/activate
python -m product_scraper.cli --config config/targets.yml --output sample_output/products.csv
```

Change `USERNAME` and paths as appropriate.

You can also redirect output to a log file:

```bat
python -m product_scraper.cli --config config/targets.yml --output sample_output/products.csv >> logs/scraper.log 2>&1
```

### 3.2 Create a Task

Open Task Scheduler.

Choose Create Basic Task....

Give it a name, e.g., Daily Product Scraper.

Trigger: Daily, set the desired time.

Action: Start a program.

Program/script:

`C:/Windows/System32/cmd.exe`

Add arguments:

`/c "C:/Users/USERNAME/python-projects/Product-List-Scraper-Template/run_scraper.bat"`

Finish and test the task by right-clicking → Run.

---

## 4. Operational best practices

This section lists recommended practices for production use.

Logging:

- Capture stdout and stderr to log files for troubleshooting.
- Consider using a rotating log strategy for long-running deployments.

Monitoring:

- Monitor exit codes (0 = success, non-zero = failure).
- Monitor log messages (e.g., number of records scraped).
- Set up alerts if repeated failures occur.

Config changes:

- Update `config/targets.yml` when site structure changes.
- Keep a version-controlled history of config files.

Resource usage:

- Be mindful of request frequency and total runtime.
- Adjust settings (requests per minute, timeouts) to avoid overloading target sites.

See `docs/SECURITY_AND_LEGAL.md` for legal and ethical guidelines when running scraping jobs in production.
