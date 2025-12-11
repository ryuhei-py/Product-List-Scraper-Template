# Configuration guide

This guide explains how to configure the **Product List Scraper Template** using YAML files.

There are two main configuration files:

- `config/targets.yml` (required) → defines **what** to scrape.
- `config/settings.yml` (optional) → defines **how** the scraper should run globally (HTTP behavior, validation, logging, etc.).

The goal is to keep the scraper:

- **Declarative** ? most site-specific logic lives in YAML.
- **Portable** ? no secrets in version control; use `.env` or deployment tooling.
- **Extensible** ? easy to add more sites, fields, or behaviors without rewriting core code.

---

## Overview

### Targets vs settings

- `targets.yml` answers:  
  > “Which site (or sites) should we scrape, and which selectors do we use?”
- `settings.yml` answers:  
  > “With which HTTP parameters, logging level, and validation rules should we run?”

The scraper can run with only `targets.yml`. Adding `settings.yml` gives you more control over operational behavior but is **optional**.

### Environment variables and `.env`

In addition to YAML configuration, environment variables can be used for:

- Proxies (`HTTP_PROXY`, `HTTPS_PROXY`)
- Authentication tokens
- Other environment-specific settings (if you extend the code)

If a `.env` file exists in the project root, it is automatically loaded via `python-dotenv`. See `.env.example` for suggested placeholders.

---

## Targets configuration (`config/targets.yml`)

`targets.yml` describes the sites (or site variants) that the scraper should process.

### Basic structure

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

### Multiple targets

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

### Detail selectors and extra fields

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

### URL patterns and relative URLs

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

---

## Settings configuration (`config/settings.yml`)

`settings.yml` provides global operational defaults. It is optional: if absent, the scraper falls back to built-in defaults.

### Example settings.yml

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

### HTTP settings (`http`)

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

### Validation settings (`validation`)

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

### Logging settings (`logging`)

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

### Output settings (`output`)

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

`config/targets.yml` defines what to scrape:

- At least one `targets` entry with `list_url`, `link_selector`, and `detail_selectors`.
- Optionally, multiple targets and extra fields per detail page.

`config/settings.yml` defines how to run:

- HTTP behavior (`timeout`, `max_retries`, `user_agent`, `delay_seconds`).
- Validation and logging defaults.
- Recommended output conventions.

`.env` holds environment-specific secrets and network settings.

Advanced patterns (pagination, multiple list pages, config-driven limits) can be expressed in YAML and then wired into code as needed, without breaking the core template.

By keeping configuration explicit, declarative, and environment-aware, this template can be adapted to many scraping projects while remaining understandable to both developers and clients.
