# Configuration Guide - targets.yml and settings.yml

This document explains the structure of the YAML configuration files used by the Product List Scraper Template.

---

## 1. Overview

This section describes how configuration is separated between site-specific and global settings.

The template separates **site-specific configuration** from **generic scraping logic** using two YAML files:

- `config/targets.yml`  
  Describes what to scrape for a given site (URLs, selectors, etc.).
- `config/settings.yml` (optional)  
  Describes global operational settings (timeouts, retries, delays, default output).

The exact field names may vary slightly depending on your implementation, but the examples below represent a typical structure.

---

## 2. config/targets.yml

This section explains the fields in `config/targets.yml`.

### 2.1 Example

```yaml
site_name: "example_shop"

list_pages:
  - url: "https://example.com/products"
    link_selector: "a.product-link"
    pagination:
      enabled: true
      param: "page"
      start: 1
      end: 3

detail_selectors:
  title: "h1.product-title"
  price: ".product-price"
  image_url: "img.main-image"
  description: ".product-description"

# Optional: additional selectors for other fields
extra_selectors:
  sku: ".product-sku"
  category: ".breadcrumb .category"

# Optional: controls for this target
limits:
  max_items: 200
```

### 2.2 Field reference

`site_name` (string, required)  
A human-readable identifier for the site or configuration. Used mainly for logging and reports. Does not affect scraping logic directly.

`list_pages` (list of objects, required)  
Defines one or more list pages that contain product links. Each entry typically includes:

- `url` (string, required)  
  The URL of the list page.
- `link_selector` (string, required)  
  CSS selector for anchor tags pointing to product detail pages. Example: `a.product-link`.
- `pagination` (object, optional)  
  - `enabled` (bool): whether to paginate this list page.  
  - `param` (string): the query parameter used for pagination, e.g., `page`.  
  - `start` (int): first page number.  
  - `end` (int): last page number (inclusive).  
  Alternative pagination schemes (e.g., next-link selectors) can be added as needed.

`detail_selectors` (object, required)  
Defines CSS selectors for core product fields on the detail page. Typical keys:

- `title` (string)
- `price` (string)
- `image_url` (string)
- `description` (string)

Your parser implementation decides whether to read attributes (e.g., `src` from `img`) and how to handle missing or malformed elements.

`extra_selectors` (object, optional)  
Any additional fields you want to extract. Example:

```yaml
extra_selectors:
  sku: ".product-sku"
  category: ".breadcrumb .category"
  brand: ".product-brand"
```

The template can combine `detail_selectors` and `extra_selectors` into a single record dict.

`limits` (object, optional)  
Allows target-specific limits:

- `max_items` (int): maximum number of product detail pages to process.

This can be used to throttle early experiments and avoid scraping extremely large sites during initial runs.

---

## 3. config/settings.yml (optional)

This section outlines optional global settings.

### 3.1 Example

```yaml
http:
  user_agent: "Mozilla/5.0 (compatible; ProductScraper/1.0)"
  timeout: 10          # seconds
  max_retries: 3
  delay_seconds: 1.0   # delay between requests

output:
  directory: "sample_output"
  csv_filename: "products.csv"
  json_filename: "products.json"   # optional

validation:
  enabled: true

logging:
  level: "INFO"        # e.g., DEBUG / INFO / WARNING / ERROR
```

### 3.2 Field reference

`http` (object)  
`user_agent` (string) — Custom User-Agent header to send with requests.  
`timeout` (int/float) — Request timeout in seconds.  
`max_retries` (int) — Number of retry attempts for transient failures (e.g., network/5xx status).  
`delay_seconds` (float) — Delay between requests to the same site; helps avoid overloading servers.

`output` (object)  
`directory` (string) — Base directory for output files (CSV/JSON).  
`csv_filename` (string) — Name of the CSV output file.  
`json_filename` (string, optional) — Name of the JSON output file if JSON export is enabled.  
The CLI may combine directory and filenames to construct full output paths.

`validation` (object)  
`enabled` (bool) — Whether to run the validation step (`validate_records`) and print a quality report.

`logging` (object)  
`level` (string) — Desired logging verbosity. Depending on your implementation, this may integrate with Python’s logging module.

---

## 4. Best practices

This section lists configuration best practices.

Keep configs version-controlled:

- Treat `targets.yml` and `settings.yml` as part of your codebase.
- Commit changes with clear messages when selectors or URLs change.

Separate per-site configs:

- For multiple clients or sites, keep separate config files:
  - `config/targets_site_a.yml`
  - `config/targets_site_b.yml`
- Use `--config` in the CLI to switch between them.

Document assumptions:

- Add comments in YAML to explain any non-obvious selectors or pagination logic.

Start small:

- Begin with one list page and a few fields.
- Once it works, expand selectors and pagination.

For operational considerations and legal or ethical scraping guidelines, see `docs/SECURITY_AND_LEGAL.md`.
