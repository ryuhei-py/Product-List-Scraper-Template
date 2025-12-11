# Architecture

This document describes the architecture of the **Product List Scraper Template**.

The goal is to provide a **clean, reusable, and testable** structure for typical product / catalog scraping tasks, while remaining simple enough to adapt quickly for real projects.

---

## High-level overview

At a high level, the system:

1. Loads a **targets configuration** (`config/targets.yml`) that describes what to scrape.
2. Optionally loads **global settings** (`config/settings.yml`) and environment variables (`.env`).
3. Uses a **Fetcher** to download:
   - one or more product list pages
   - corresponding product detail pages
4. Uses **parsers** to extract:
   - product detail URLs from list pages
   - structured product fields from detail pages
5. Uses an **Exporter** to write the collected records to CSV (and optionally JSON).
6. Uses a **Validator** to generate a simple data-quality report.
7. Returns an exit code indicating success or failure.

The architecture is deliberately layered so that each component has a single responsibility and can be tested in isolation.

---

## Data and control flow

### Flow diagram

```mermaid
flowchart LR
    subgraph Config
        T[targets.yml]
        S[settings.yml (optional)]
    end

    subgraph Runtime
        CLI[CLI\nproduct_scraper.cli]
        F[Fetcher\nfetcher.py]
        LP[ListPageParser\nparser.py]
        DP[DetailPageParser\nparser.py]
        E[Exporter\nexporter.py]
        V[Validator\nvalidator.py]
    end

    T --> CLI
    S --> CLI

    CLI --> F
    CLI --> LP
    CLI --> DP
    CLI --> E
    CLI --> V

    F --> LP
    LP --> F
    F --> DP
    DP --> E
    E --> V
```

### Narrative

#### Configuration phase

The CLI reads a YAML configuration file (e.g., `config/targets.yml`) to obtain a list of scraping targets.

Optionally, it reads `config/settings.yml` for HTTP, validation, and logging defaults.

Environment variables from `.env` are loaded (if present) so that proxies or secrets can be configured without changing code.

#### Initialization phase

The CLI validates the loaded configuration and selects a single target to run:

- By default, the first target in the list.
- Or a specific one chosen by `--target-name`.

It configures logging based on `settings.yml` (e.g., log level).

It creates a Fetcher instance with HTTP configuration (timeout, retries, headers, delay).

#### List-page phase

The CLI instructs the Fetcher to download the list page (`list_url`).

The ListPageParser extracts product detail URLs via a CSS selector (`link_selector`).

The CLI normalizes these URLs:

- Absolute URLs (starting with http) are used as-is.
- Relative URLs are resolved against the list page URL via `urljoin`.

#### Detail-page phase

For each normalized product URL (optionally truncated by `--limit`), the CLI:

- Uses the Fetcher to download the detail page HTML.
- Passes the HTML to DetailPageParser to extract fields (title, price, image URL, description, and any extra selectors defined in config).
- Each parsed product is collected as a dictionary of field values.

#### Export phase

If `--dry-run` is not used:

- The Exporter writes the accumulated records to a CSV file at the specified output path.
- Optionally, the Exporter can be extended to produce JSON or other formats.

#### Validation and reporting phase

If validation is enabled in settings:

- The Validator inspects the records to compute:
  - Total records count
  - Missing values per field
- It returns a human-readable text report.
- The CLI prints this report to stdout.

#### Exit

The CLI returns exit code 0 on success.

Non-zero codes are used for configuration errors, fetch failures (when considered fatal), or unexpected exceptions.

---

## Package layout

The Python package uses a `src` layout:

```text
src/
└─ product_scraper/
   ├─ __init__.py
   ├─ config.py
   ├─ fetcher.py
   ├─ parser.py
   ├─ exporter.py
   ├─ validator.py
   └─ cli.py
```

Each module has a clear scope:

- `config.py`  
  Load and validate configuration files.
- `fetcher.py`  
  HTTP client abstraction with basic retry behavior.
- `parser.py`  
  HTML parsing for list and detail pages.
- `exporter.py`  
  Output serialization (CSV, optionally JSON).
- `validator.py`  
  Data-quality checks and summary reporting.
- `cli.py`  
  Orchestration, argument parsing, and integration of all components.

---

## Modules and responsibilities

### config.py

#### Responsibilities

- Load the targets configuration (YAML) from a given path.
- Optionally load a settings configuration (YAML) from a given path.
- Validate the basic structure of the loaded configuration before use.

#### Key concepts

- `load_targets_config(path)`  
  Reads the YAML file. Returns a dictionary representing the loaded config.
- `load_settings_config(path)`  
  Returns a dictionary or an empty dict if the file does not exist. Ensures that the top-level object is a mapping.
- `get_targets_from_config(config)`  
  Extracts and validates the targets list. Ensures:
  - `targets` exists and is a non-empty list.
  - Each item is a mapping.
  - Each item has the required keys (`list_url`, `link_selector`).
  - `detail_selectors` is a mapping (may be empty).

#### Design rationale

Centralizing config loading and validation prevents configuration-related errors from scattering across the CLI and business logic.

Validation failures raise a specific `ConfigError`, allowing the CLI to report human-friendly messages.

### fetcher.py

#### Responsibilities

- Provide a small wrapper around HTTP GET requests.
- Implement simple retry logic and timeouts.
- Accept custom headers (e.g., User-Agent) from configuration.

#### Key concepts

- Fetcher class:
  - Initialized with:
    - timeout (seconds)
    - `max_retries`
    - optional headers dict
  - `get(url: str) -> str`:
    - Attempts to fetch the URL up to `max_retries` times.
    - Raises a `FetchError` on persistent failure.
- `FetchError` exception:
  - Signals that the client code (e.g., CLI) should decide how to handle the failure (skip vs abort).

#### Design rationale

Isolating HTTP logic in Fetcher:

- Makes it easier to swap requests/httpx/aiohttp later if needed.
- Makes network behavior straightforward to test (via monkeypatch or mocking).
- Global HTTP behavior (timeouts, retries, headers) can be tuned centrally via `settings.yml`.

### parser.py

This module holds both list page and detail page parsers, built on top of BeautifulSoup.

#### ListPageParser

##### Responsibilities

- Extract product detail URLs from the HTML of a list page using a single CSS selector.

##### Key concepts

- `ListPageParser(list_url: str, link_selector: str)`
  - `list_url` provides context for logging and future extensions.
  - `link_selector` is typically something like `"a.product-link"`.
- `parse_list(html: str) -> list[str]`
  - Parses the document.
  - Selects all anchor elements matching `link_selector`.
  - Collects their href attributes as strings (after basic cleaning).
  - Returns a list of URLs (relative or absolute).

##### Design rationale

Keeping list-page parsing simple allows you to focus on:

- Getting the correct selector.
- Handling pagination by invoking the parser on multiple pages if needed.
- Any URL normalization (relative → absolute) is centralized in the CLI, not in the parser.

#### DetailPageParser

##### Responsibilities

- Extract a set of product fields from the HTML of a detail page.
- Support both a core set of fields and arbitrary extra fields defined in configuration.

##### Key concepts

- `DetailPageParser(selectors: dict[str, str])`

Selectors map field names to CSS selectors, e.g.:



```yaml
detail_selectors:
  title: "h1.product-title"
  price: ".price"
  image_url: "img.product-image"
  description: ".description"
  sku: ".sku"             # extra field
```

- `parse_detail(html: str) -> dict[str, str | None]`

Always returns at least the core fields:

- `title`, `price`, `image_url`, `description`

For each selector:

- If missing, the field value is `None`.
- If present:
  - For `image_url`: prefer the `src` attribute; fallback to element text.
  - For other fields: use `element.get_text(strip=True)`.

Any extra selectors in `selectors` are also extracted and included in the result.

##### Design rationale

The parser is declarative:

- The meaning of fields is defined in config, not in code.
- The core fields ensure a consistent baseline across sites.
- Extra fields allow per-site customization without code changes.

### exporter.py

#### Responsibilities

- Serialize a collection of product records to CSV (and optionally JSON).
- Handle edge cases gracefully (e.g., empty record list).

#### Key concepts

- CSV export:
  - Uses the keys from the first record to define columns.
  - Writes all records, respecting `None`/empty values.
- Optional JSON export (if implemented or extended):
  - Serializes records as a list of dictionaries.

#### Design rationale

Export formats are kept simple on purpose.

For more complex use cases (databases, APIs, etc.), you can:

- Add new exporter classes.
- Or create separate modules, keeping the core scraper unchanged.

### validator.py

#### Responsibilities

- Provide lightweight data-quality checks on the final record set.
- Produce a human-readable report.

#### Key concepts

- Validation functions:
  - Count total records.
  - For each field:
    - Count how many records are missing (`None` or empty).
  - Optionally compute simple derived metrics (e.g., percentage missing).
- Quality report:
  - Returns a text summary, such as:
    - total records
    - missing counts per field
    - any basic warnings or notes

#### Design rationale

The validator is deliberately simple and non-blocking:

- It reports quality but does not enforce hard rules by default.
- This fits client workflows where:
  - They want visibility into data quality.
  - They may handle remediation downstream (e.g., in Excel).

### cli.py

#### Responsibilities

- Provide a command-line interface around the scraper.
- Integrate configuration, HTTP, parsing, exporting, and validation.
- Implement logging and exit-code conventions.

#### Key concepts

- Argument parsing:
  - `--config` (path to targets YAML; required)
  - `--output` (output CSV path; required)
  - `--limit` (optional max number of items)
  - `--dry-run` (do not write output files)
  - `--target-name` (optional: select a specific target by name)
- Configuration loading:
  - Load targets via `load_targets_config`.
  - Validate via `get_targets_from_config`.
  - Optionally load settings via `load_settings_config("config/settings.yml")`.
  - Load environment variables via `load_dotenv()` if `.env` is present.
- Logging:
  - Configure logging level from `settings.yml` (`logging.level`).
  - Use logger for informational events.
- Pipeline orchestration:
  - Fetch list page HTML.
  - Build detail URLs.
  - Fetch detail HTML for each product.
  - Parse detail fields, accumulate records.
  - Export to CSV unless `--dry-run`.
  - Run validation if enabled; print report.

#### Design rationale

The CLI is intentionally thin and primarily orchestrates components.

All heavy logic lives in the package modules, keeping the CLI easy to understand and modify.

---

## Configuration model

Configuration is split into:

- Targets config (`config/targets.yml`)  
  Defines what to scrape.
- Settings config (`config/settings.yml`, optional)  
  Defines how to run the scraper globally (HTTP, validation, logging, etc.).

### Targets config (`config/targets.yml`)

`targets.yml` describes the sites (or site variants) that the scraper should process.

#### Basic structure

At minimum, `targets.yml` must define a non-empty list under the `targets` key:

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

Required fields per target:

- `name` (string, recommended)  
  Logical name of the target (e.g., "example-site"). Used with the `--target-name` CLI flag.
- `list_url` (string, required)  
  URL of the product list page to start from.
- `link_selector` (string, required)  
  CSS selector for anchors pointing to product detail pages. Example: `"a.product-link"`.
- `detail_selectors` (mapping, required)  
  Mapping of field names to CSS selectors evaluated on the detail page.

Minimum recommended fields:

- `title`
- `price`
- `image_url`
- `description`

You may add extra fields as needed (e.g., `sku`, `category`).

The core code validates that:

- `targets` exists and is a non-empty list.
- Each target is a mapping with non-empty `list_url` and `link_selector`.
- `detail_selectors` is a mapping (may be empty, but that’s not very useful).

If the config is invalid, the CLI prints a clear error and exits with a non-zero status.

#### Multiple targets

You can define multiple targets in a single file:

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

  - name: example-sale
    list_url: "https://example.com/sale"
    link_selector: "a.sale-product-link"
    detail_selectors:
      title: "h1.product-title"
      price: ".price"
      image_url: "img.product-image"
      description: ".description"
      badge: ".badge"
```

At runtime:

- By default, the CLI uses the first target in the list.
- You can select a specific target using `--target-name`:



```bash
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products_example.csv \
  --target-name example-sale
```

This pattern lets you:

- Keep related variants in one file (e.g., regular vs sale pages).
- Avoid duplicating configurations across separate YAML files.

#### Detail selectors and extra fields

`detail_selectors` is a mapping of logical field names to CSS selectors.

Example:

yaml



```yaml
detail_selectors:
  title: "h1.product-title"
  price: ".price"
  image_url: "img.product-image"
  description: ".description"
  sku: ".sku"
  category: ".breadcrumb .category"
```

Behavior:

The parser ensures the following core fields always exist in the output dict:

- `title`
- `price`
- `image_url`
- `description`

For each field specified in `detail_selectors`:

- If the selector is missing or empty → the value is `None`.
- If the element is not found in the HTML → the value is `None`.
- Otherwise:
  - For `image_url`, the parser prefers the `src` attribute; if missing, it falls back to element text.
  - For other fields, the parser uses `element.get_text(strip=True)` and normalizes empty strings to `None`.

Any extra fields (e.g., `sku`, `category`) are included in the output records as additional columns.

This design allows you to add and remove fields without changing code. Only the YAML definition needs to be updated.

#### URL patterns and relative URLs

Some sites use:

- Absolute URLs: `https://example.com/product/123`
- Root-relative URLs: `/product/123`
- Page-relative URLs: `product/123`, `./product/123`

The scraper:

- Reads raw href attributes from the list page.
- Normalizes them in the CLI:
  - If the URL starts with "http" → treated as absolute.
  - Otherwise → resolved via `urllib.parse.urljoin(list_url, href)`.

This means:

- You can use a single `link_selector` for different URL types.
- You do not need to adjust for relative vs absolute URLs in configuration.

### Settings config (`config/settings.yml`)

`settings.yml` provides global operational defaults. It is optional: if absent, the scraper falls back to built-in defaults.

#### Example settings.yml

A typical `settings.yml` might look like:

yaml



```yaml
http:
  user_agent: "Mozilla/5.0 (compatible; ProductScraper/1.0)"
  timeout: 10        # seconds
  max_retries: 3
  delay_seconds: 1.0 # delay between requests

validation:
  enabled: true

logging:
  level: "INFO"

output:
  directory: "sample_output"
  csv_filename: "products.csv"
  json_filename: "products.json"
```

The core CLI uses:

- `http.*` to configure the Fetcher.
- `validation.enabled` to decide whether to run the validation stage.
- `logging.level` to configure Python’s logging.

The `output.*` section is a recommended schema for organizing your outputs. The default CLI uses the `--output` flag for the CSV path and does not automatically read `output.directory` or `csv_filename` unless you extend the code accordingly.

#### HTTP settings (`http`)

The `http` section controls how the Fetcher behaves:

yaml



```yaml
http:
  user_agent: "Mozilla/5.0 (compatible; ProductScraper/1.0)"
  timeout: 10
  max_retries: 3
  delay_seconds: 1.0
```

- `user_agent` (string, optional)  
  Sets the User-Agent header for outgoing requests. Default: omission leads to the underlying HTTP library’s default behavior.
- `timeout` (number, optional)  
  Request timeout in seconds. Default: 10 seconds (in the template implementation).
- `max_retries` (integer, optional)  
  Number of attempts per URL. Default: 3.
- `delay_seconds` (number, optional)  
  Fixed delay between requests. Helps to reduce load on the target site and stay polite. Default: 0 (no delay) if not specified.

These values are read by the CLI and used to initialize Fetcher.

#### Validation settings (`validation`)

Validation is a lightweight, non-blocking step that summarizes data quality.

yaml



```yaml
validation:
  enabled: true
```

- `enabled` (boolean, optional)  
  `true`: run validation and print a data-quality report.  
  `false`: skip validation entirely.  
  Default: `true` if `validation` is missing.

The validation report typically includes:

- Total records count.
- Missing counts per field.
- Simple notes about completeness.

This is useful in early development and in ongoing operations to monitor data quality over time.

#### Logging settings (`logging`)

Logging is configured via `logging` section:

yaml



```yaml
logging:
  level: "INFO"
```

- `level` (string, optional)  
  Interpreted as a standard logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.  
  Default: `INFO` when missing or invalid.

The CLI uses this value to call `logging.basicConfig(level=...)`. Within the code, `logger.info(...)` etc. are used for:

- High-level progress (number of URLs discovered, records exported).
- Warnings for anomalies (skipped URLs).
- Errors before exiting.

In scheduled runs, you typically redirect stdout/stderr to log files. The `logging.level` controls how verbose those logs are.

#### Output settings (`output`)

The `output` section is advisory: it proposes a convention for where and how to store files:

yaml



```yaml
output:
  directory: "sample_output"
  csv_filename: "products.csv"
  json_filename: "products.json"
```

By default, the CLI:

- Requires an explicit `--output` argument for the CSV path.
- Does not automatically use these values.

You can:

- Use `output.*` in your own scripts that wrap the CLI.
- Extend the CLI to:
  - Use `output.directory` and `csv_filename` as defaults when `--output` is not provided.
  - Optionally write JSON using `json_filename`.

Keeping `output.*` in `settings.yml` helps centralize deployment-specific decisions (paths, naming conventions).

---

## Environment-specific configurations

For real deployments, you may want different configs for:

- Local development
- Staging
- Production

### Environment-specific targets

You can maintain separate targets files:

- `config/targets.dev.yml`
- `config/targets.stage.yml`
- `config/targets.prod.yml`

And select them via `--config`:



```bash
# Development
python -m product_scraper.cli \
  --config config/targets.dev.yml \
  --output data/dev_products.csv

# Production
python -m product_scraper.cli \
  --config config/targets.prod.yml \
  --output data/prod_products.csv
```

This pattern is useful when:

- Different environments use different domains or URLs.
- Some targets should only run in non-production environments.

### Environment-specific settings

Similarly for settings:

- `config/settings.dev.yml`
- `config/settings.prod.yml`

You can:

- Symlink or copy the appropriate file to `config/settings.yml` during deployment.
- Or pass a configurable path to the CLI if you extend it.

Examples:

- Lower timeouts and fewer retries in development.
- Longer timeouts and more conservative delays in production.

### Environment variables

Environment variables complement YAML:

- Keep secrets out of Git (tokens, credentials, proxy URLs).
- Provide runtime overrides independent of YAML.

Typical patterns:

- `HTTP_PROXY`, `HTTPS_PROXY` for network routing.
- `SCRAPER_ENV` to indicate env (dev/stage/prod) if you extend the code to react to it.

The core template does not hard-code any specific environment variables, but `.env` is loaded automatically, so you can rely on them in custom extensions.

---

## Advanced patterns (design suggestions)

The base template intentionally keeps configuration simple. However, the same structure can be extended to more advanced scenarios.

Important: The patterns below are design suggestions. They are not fully wired into the core CLI by default and require additional code to take effect.

### Pagination

For list pages that require pagination, you might extend a target like:

yaml



```yaml
targets:
  - name: example-paged
    list_url: "https://example.com/products"
    link_selector: "a.product-link"
    detail_selectors:
      title: "h1.product-title"
      price: ".price"
      image_url: "img.product-image"
      description: ".description"
    pagination:
      type: "query_param"
      param: "page"
      start: 1
      end: 5
```

Interpretation (custom logic you can implement):

For `type: "query_param"`:

- The CLI (or a higher-level controller) would generate:
  - `https://example.com/products?page=1`
  - `https://example.com/products?page=2`
  - `...`
  - `https://example.com/products?page=5`
- It would then run the list-page parsing step for each page.

Other pagination patterns you could design:

- `type: "path_segment"` ? when page number is part of the URL path.
- `type: "offset"` ? when an offset parameter is used (e.g., `?start=0&limit=50`).

### Multiple list pages per target

Some sites naturally group content (e.g., categories):

yaml



```yaml
targets:
  - name: multi-list-example
    list_pages:
      - url: "https://example.com/products/category/a"
        link_selector: "a.product-link"
      - url: "https://example.com/products/category/b"
        link_selector: "a.product-link"
    detail_selectors:
      title: "h1.product-title"
      price: ".price"
      image_url: "img.product-image"
      description: ".description"
```

Possible logic (if you implement it):

- For each entry in `list_pages`, fetch and parse URLs.
- Combine all discovered detail URLs into a single set before processing detail pages.

This avoids duplicating entire targets for categories that share the same detail selectors.

### Limits and filters

You might want to express config-driven limits instead of using `--limit` only:

yaml



```yaml
targets:
  - name: limited-example
    list_url: "https://example.com/products"
    link_selector: "a.product-link"
    detail_selectors:
      title: "h1.product-title"
      price: ".price"
      image_url: "img.product-image"
      description: ".description"
    limits:
      max_items: 100
```

If you implement support for `limits.max_items`, the CLI could:

- Cap the number of detail pages processed regardless of `--limit`.
- Or treat `--limit` as a temporary override for local debugging.

Configuration-driven limits make operational behavior more predictable and reproducible across environments.

---

## Validation and safety

The configuration loader validates essential aspects of `targets.yml`:

- `targets` must be present and non-empty.
- Each target must be a mapping with:
  - `list_url`
  - `link_selector`
  - `detail_selectors` (mapping)

If validation fails:

- A `ConfigError` is raised.
- The CLI prints a human-readable message and exits with a non-zero code.

To keep configuration safe and maintainable:

- Prefer explicit keys over magic defaults.
- Avoid embedding credentials or secrets in YAML; use `.env` or deployment tooling instead.
- Use comments in YAML to document decisions and selectors.

---

## Examples

### Single-site, simple configuration

yaml



```yaml
# config/targets.yml
targets:
  - name: example-simple
    list_url: "https://example.com/products"
    link_selector: "a.product-link"
    detail_selectors:
      title: "h1.product-title"
      price: ".price"
      image_url: "img.product-image"
      description: ".description"
```

Run:



```bash
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products.csv
```

### Multi-target configuration

yaml



```yaml
# config/targets.yml
targets:
  - name: example-regular
    list_url: "https://example.com/products"
    link_selector: "a.product-link"
    detail_selectors:
      title: "h1.product-title"
      price: ".price"
      image_url: "img.product-image"
      description: ".description"

  - name: example-sale
    list_url: "https://example.com/sale"
    link_selector: "a.sale-product-link"
    detail_selectors:
      title: "h1.product-title"
      price: ".price"
      image_url: "img.product-image"
      description: ".description"
      badge: ".badge"
```

Run a specific target:



```bash
python -m product_scraper.cli \
  --config config/targets.yml \
  --output sample_output/products_sale.csv \
  --target-name example-sale
```

### Settings for production-like environment

yaml



```yaml
# config/settings.yml
http:
  user_agent: "Mozilla/5.0 (compatible; ProductScraper/1.0)"
  timeout: 15
  max_retries: 5
  delay_seconds: 0.5

validation:
  enabled: true

logging:
  level: "INFO"
```

You might also set proxies via `.env`:



```bash
# .env
HTTPS_PROXY=http://user:pass@proxy.example.com:8080
```

---

## Summary

The Product List Scraper Template is organized as a small, layered system:

- Config + settings → CLI → Fetcher → Parsers → Exporter → Validator

This structure emphasizes:

- Clear responsibilities per module
- Config-driven behavior for new sites
- Testability and maintainability
- A realistic, portfolio-friendly representation of how a production scraper is typically built

By keeping the architecture simple but explicit, the template can be:

- Quickly adapted to new scraping projects, and
- Easily explained to clients and reviewers as part of a professional portfolio.
