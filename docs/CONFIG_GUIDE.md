# Configuration guide
This guide explains the configuration model for the Product List Scraper Template. The template is configuration-driven so most adaptations happen in YAML, not Python.

This guide covers:
- Target configuration (`config/targets*.yml`).
- Settings configuration (`config/settings*.yml`).
- Selector specification syntax (text + attributes).
- Validation rules and common pitfalls.

---

## Configuration files
This section distinguishes tracked examples from runtime files.

### Tracked (portfolio/reference)
- `config/targets.example.yml`
- `config/settings.example.yml`

### Runtime (recommended, typically gitignored)
- `config/targets.yml`
- `config/settings.yml`

Recommended workflow:

# Create editable runtime configs from examples
```bash
cp config/targets.example.yml config/targets.yml
cp config/settings.example.yml config/settings.yml
```

---

## Targets configuration (`config/targets*.yml`)
This section describes how targets are defined.

Targets are defined under a single top-level key: `targets`. Each target must have a `name` (string, non-empty, unique) and `list_url` (string, non-empty). Then you choose one of two modes:

- List-only mode: parse repeated “item cards” directly from the list page.
- Detail-follow mode: extract detail links from the list page and scrape fields from each detail page.

### Mode A: list-only targets
This subsection explains when and how to use list-only mode.

When to use:
- The list page contains all the fields you need (title/price/image/URL/etc.).
- You want a fast, reliable pipeline (one request per run in simplest cases).
- You are building a demo or iterating on selectors quickly.

Required fields:
- `item_selector`: CSS selector for each repeated item card/container.
- `item_fields`: mapping of `field_name -> selector_spec`.

Example (working demo target):

```yaml
targets:
  - name: laptops-demo
    list_url: "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops"
    item_selector: "div.thumbnail"
    item_fields:
      title: "a.title@title"
      price: "h4.price"
      description: "p.description"
      image_url: "img@src"
      product_url: "a.title@href"
```

Output notes (list-only):
- Each parsed record gets `source_list_url` (the list URL used for the run).
- Any field ending with `*_url` (for example: `image_url`, `product_url`) is normalized to an absolute URL when possible (relative paths are resolved against the list URL).

### Mode B: detail-follow targets
This subsection explains when and how to use detail-follow mode.

When to use:
- The list page only contains summary fields.
- You need richer data from the product detail page (specifications, long descriptions, variants, etc.).

Required fields:
- `link_selector`: CSS selector for product links on the list page.
- `detail_selectors`: mapping of `field_name -> selector_spec`.

Example:

```yaml
targets:
  - name: my-shop
    list_url: "https://example.com/products"
    link_selector: "a.product-link"
    detail_selectors:
      title: "h1.product-title"
      price: ".price"
      image_url: "img.product-image@src"
      description: ".description"
```

Output notes (detail-follow):
- Each parsed record gets `source_list_url` (the list URL used for the run) and `detail_url` (the resolved absolute URL that was fetched).
- Any field ending with `*_url` (for example: `image_url`) is normalized to an absolute URL when possible (relative paths are resolved against the detail URL).

---

## Selector spec syntax
This section defines how selector specs work in `item_fields` and `detail_selectors`.

A selector spec determines how a value is extracted from HTML.

### Text extraction (default)
- `"h4.price"`: selects the element and extracts `get_text(strip=True)`.
- `"a.title::text"`: explicit text mode (equivalent to the above).
- If the element is not found or the text is empty, the result is treated as missing.

### Attribute extraction
Two equivalent syntaxes are supported:
- `"a.title@title"`: extracts the `title` attribute.
- `"a.title::attr(title)"`: same meaning (Scrapy-like).

Examples:
- `"img@src"` → `src` attribute.
- `"a@href"` → `href` attribute.

If the element is not found or the attribute is missing/empty, the result is treated as missing.

---

## Validation rules for targets
This section lists enforced validation rules.

Targets are validated at load time. Common enforced rules:
- `targets` must be a list.
- Each target must be a mapping/object.
- `name` must be present, a non-empty string, and unique.
- `list_url` must be present and a non-empty string.
- List-only mode:
  - `item_selector` must be present and non-empty.
  - `item_fields` must be present, a non-empty mapping.
- Detail-follow mode:
  - `link_selector` must be present and non-empty.
  - `detail_selectors` must be present, a non-empty mapping.
- All selector values in `item_fields` / `detail_selectors` must be non-empty strings.

If validation fails, the CLI should exit with a non-zero status and print a clear error message.

---

## Settings configuration (`config/settings*.yml`)
This section describes operational settings.

Settings are used to control HTTP behavior, retries, optional backoff, validation behavior, and logging.

A typical structure:

```yaml
http:
  user_agent: "Mozilla/5.0 (compatible; ProductScraper/1.0)"
  timeout: 10
  max_retries: 3
  delay_seconds: 0.0
  retry_backoff_seconds: 0.0
  retry_backoff_multiplier: 2.0
  retry_jitter_seconds: 0.0

validation:
  enabled: true

logging:
  level: "INFO"
```

### HTTP / retry behavior (typical expectations)
- Requests are made with a session (connection reuse).
- Retries are attempted for retryable cases such as HTTP 429 and HTTP 5xx.
- Backoff is only applied if `retry_backoff_seconds > 0.0`.

### Delay
- `delay_seconds` is useful for being respectful to target sites and reducing blocking risk.
- Set small delays during development; adjust per site policy and Terms of Service.

---

## Common mistakes and how to avoid them
This section lists typical errors and fixes.

1) “It runs but returns empty records”  
   Check that selectors match the site’s HTML, `item_selector` selects the repeated container (list-only mode), `link_selector` selects anchors with `href` (detail-follow mode), and selector specs return non-empty text/attributes. Tip: start with `--dry-run` and a small `--limit` when iterating.

2) “Some URL fields are relative”  
   This is expected from many sites. Name URL-like fields with the suffix `*_url` (for example, `image_url`, `product_url`). The CLI normalizes these to absolute URLs when possible.

3) “Config validation fails”  
   Typical causes: missing required keys for the selected mode, empty selector strings, duplicate name across targets. Fix the YAML and rerun.

---

## Where to go next
This section points to related docs.

- See `README.md` for end-to-end usage examples and CLI commands.
- See `docs/architecture.md` for the pipeline and module responsibilities.
- See `docs/operations.md` for operational guidance (timeouts, retries, logging, troubleshooting).
- See `docs/testing.md` for test strategy and local development workflow.
- See `docs/SECURITY_AND_LEGAL.md` for compliance expectations and safe scraping practices.

---

_Last updated: 2025-12-12_
