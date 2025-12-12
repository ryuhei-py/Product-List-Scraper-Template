# Operations guide
This guide covers how to run, monitor, and troubleshoot the Product List Scraper Template in real-world usage (local runs, scheduled runs, and client delivery contexts).

It assumes you have already reviewed:
- `README.md` for quickstart usage.
- `docs/CONFIG_GUIDE.md` for target/settings configuration.
- `docs/architecture.md` for internal design.

---

## Installation and runtime setup
This section describes installing and preparing runtime configs.

### Recommended install (editable, for development/iteration)

# Create and activate a virtual environment, then install
```bash
python -m venv .venv
# Windows:
#   .\.venv\Scripts\activate
# macOS/Linux:
#   source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e .
```

### Optional Excel export support

# Install Excel extras
```bash
pip install -e ".[excel]"
```

### Runtime config files (local/client)

# Create runtime configs from examples
```bash
cp config/targets.example.yml config/targets.yml
cp config/settings.example.yml config/settings.yml
```

Recommended policy:
- Track `*.example.yml` as portfolio/reference.
- Keep `config/targets.yml` and `config/settings.yml` out of Git (they can include client-specific URLs, selectors, or operational settings).

---

## Running the scraper
This section provides common run modes.

### Basic run (writes output)

# Run a full scrape
```bash
product-scraper --config config/targets.yml --output output/products.csv
```

### Dry run (no output file)
Use this when iterating on selectors/config.

# Run without writing output
```bash
product-scraper --config config/targets.yml --output output/products.csv --dry-run
```

### Limit records
Useful for fast tests and quick validation.

# Run with a limit
```bash
product-scraper --config config/targets.yml --output output/products.csv --limit 25
```

### Select a target
If multiple targets exist in the YAML.

# Run a specific target
```bash
product-scraper --config config/targets.yml --output output/products.csv --target laptops-demo
```

If your CLI uses `--target-name` instead of `--target`, use the flag your implementation provides.

---

## Understanding output and traceability
This section explains added fields and normalization.

Traceability fields:
- `source_list_url` (always present): list page used for the run.
- `detail_url` (detail-follow mode only): resolved absolute URL that was fetched for each record.

URL normalization (`*_url`):
- Any field name ending in `*_url` (for example, `image_url`, `product_url`, `detail_url`) is resolved to an absolute URL when possible.
- Relative URLs are normalized using `urljoin(...)` with a base that depends on the mode:
  - List-only: base is `list_url`.
  - Detail-follow: base is `detail_url` for detail page fields.
- If you want a field normalized, name it with the `*_url` suffix.

CSV header policy:
- CSV export writes headers as a stable union-of-keys across all records.
- Start with keys from the first record (in insertion order).
- Append any newly encountered keys from later records.
- This ensures optional/conditional fields do not disappear.

---

## HTTP behavior: retries, timeouts, delays, backoff
This section describes HTTP controls in `config/settings.yml` under `http:`.

Typical keys:

```yaml
http:
  user_agent: "Mozilla/5.0 (compatible; ProductScraper/1.0)"
  timeout: 10
  max_retries: 3
  delay_seconds: 0.0
  retry_backoff_seconds: 0.0
  retry_backoff_multiplier: 2.0
  retry_jitter_seconds: 0.0
```

Timeouts:
- `timeout` controls how long a request can hang before failing.
- In production, use a finite timeout (10–30 seconds is common).

Retries:
- Retry on 429 (rate limited).
- Retry on 5xx (transient server errors).
- Do not retry other 4xx by default.
- Retries should be limited to avoid being disrespectful or blocked.

Delay (politeness / stability):
- `delay_seconds` introduces a sleep between requests (especially important in detail-follow mode).
- Increasing delay reduces block risk and improves compliance posture.

Backoff knobs (optional):
- Backoff is applied only if `retry_backoff_seconds > 0.0`.
- `retry_backoff_seconds`: initial backoff delay.
- `retry_backoff_multiplier`: backoff growth factor per retry.
- `retry_jitter_seconds`: random jitter to avoid synchronized retries.
- Keep defaults at 0.0 for local iteration; enable backoff for production-like workloads.

---

## Validation and quality reporting
This section explains validation controls.

Validation/quality reporting helps detect silent failures (for example, site HTML changed and fields became empty). A typical settings block:

```yaml
validation:
  enabled: true
```

Common quality checks:
- Missing/empty field counts by column.
- Coverage ratios (how often each field appears).

Operational recommendation: watch for sudden drops in coverage (for example, title becomes missing for 90% of records). Treat major coverage changes as a signal to update selectors.

---

## Logs and observability
This section describes logging practices.

Logging is typically configured via `logging.level`:

```yaml
logging:
  level: "INFO"
```

Recommended practices:
- Use `INFO` for normal operations, `DEBUG` for selector iteration.
- Log key lifecycle events: selected target name, mode (list-only vs detail-follow), number of items/links parsed, number of records exported, summary of quality report, errors with URL context.
- For scheduled runs, capture logs to a file or an external system (depending on client requirements).

---

## Scheduling (cron / Task Scheduler / CI)
This section outlines scheduling approaches.

### Linux/macOS cron example
Run daily at 02:00.

# Schedule a nightly run
```bash
0 2 * * * /path/to/venv/bin/product-scraper --config /path/to/config/targets.yml --output /path/to/output/products.csv >> /path/to/logs/scraper.log 2>&1
```

### Windows Task Scheduler (conceptual)
Action: run `product-scraper`.

Arguments: `--config C:\path\to\config\targets.yml --output C:\path\to\output\products.csv`

Ensure the task uses the correct Python/venv environment.

### CI-based runs (GitHub Actions)
For internal monitoring or portfolio demos, you can schedule runs with GitHub Actions. Be mindful:
- Do not scrape sites that disallow automated access.
- Avoid hitting targets too frequently.
- Prefer test sites or your own endpoints.

---

## Troubleshooting
This section lists common symptoms and fixes.

Symptom: “Config validation error”  
Common causes: missing required keys for the selected mode, empty selector strings, duplicate name across targets, wrong YAML indentation/type (mapping vs list).  
Fix: validate YAML structure and required keys; use the examples in `config/targets.example.yml` as a baseline.

Symptom: “Zero records”  
Likely causes: `item_selector` is wrong (list-only mode), `link_selector` is wrong (detail-follow mode), site structure changed, target returned different content due to geo/locale/cookies.  
Fix: use `--dry-run` and temporarily log parsed counts; inspect live HTML in browser devtools; update selectors.

Symptom: “Many missing fields”  
Likely causes: field selectors too specific; fields are loaded dynamically (SPA) and not present in raw HTML; different layouts for different items.  
Fix: loosen selectors; for SPA targets, consider an official API if available or a rendered browser approach only if compliant and required; add conditional extraction logic if needed.

Symptom: “Frequent 429 / blocks”  
Fix: increase `delay_seconds`; enable backoff (set `retry_backoff_seconds > 0`); reduce concurrency (template is single-threaded by default); use more conservative headers and caching; re-check ToS and confirm scraping is allowed.

Symptom: “Some URLs are still relative”  
Fix: ensure the field name ends with `*_url`; confirm the raw value is a URL-like attribute (`href`, `src`); confirm your selector spec is extracting the attribute correctly (`@href`, `@src`).

---

## Client delivery checklist
This section provides a pre-delivery checklist.

- Example commands in README run successfully on the client’s machine.
- Target config validated (no silent schema drift).
- Correct mode chosen (list-only vs detail-follow).
- `*_url` fields normalized correctly (no broken image/product links).
- Output schema matches the client’s expectations.
- Retries/delays/backoff tuned to target behavior and compliance requirements.
- Logging level set appropriately.
- Clear operational instructions provided (where configs live, how to schedule, where outputs/logs are written).
- Legal/compliance notes acknowledged (ToS/robots/data policy).

---

## Related documentation
This section links to other docs.

- `docs/CONFIG_GUIDE.md` — configuration and selector syntax.
- `docs/architecture.md` — module-level architecture and contracts.
- `docs/testing.md` — test strategy and local dev workflow.
- `docs/SECURITY_AND_LEGAL.md` — compliance, risk, and best practices.

---

_Last updated: 2025-12-12_
