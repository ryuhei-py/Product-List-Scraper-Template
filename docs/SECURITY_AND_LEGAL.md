# SECURITY AND LEGAL

This document describes security, legal, and ethical considerations for operating and adapting this scraper template responsibly. It also clarifies what safeguards the project provides, what it does **not** provide, and what the operator must decide before running against any real target.

This is **not legal advice**. If you are unsure about permissions, contractual obligations, data rights, or privacy requirements, consult qualified counsel and obtain explicit authorization from the data owner.

---

## Scope

### Covered
- Responsible operation of the scraper (rate limiting, retries/backoff, timeouts, identification).
- Legal/policy considerations (Terms of Service, robots.txt, access control boundaries).
- Privacy and data handling practices (minimization, retention, storage controls).
- Secure configuration and secrets handling.
- Practical checklists for running and delivering.

### Not covered / Non-goals
- Automatic legal compliance enforcement (e.g., this project does **not** automatically fetch or enforce `robots.txt`).
- Bypass or circumvention techniques (CAPTCHA solving, fingerprint evasion, stealth automation, account takeovers, paywall bypass, etc.).
- Legal determinations about what is “allowed” for a specific target or jurisdiction.

---

## Core Principles

1. **Authorization first**  
   Only run against targets when you are permitted to do so.

2. **Minimize harm**  
   Prefer conservative request rates, clear stop conditions, and careful retries.

3. **Data minimization**  
   Collect only what is needed for the defined purpose; avoid personal data unless explicitly required and authorized.

4. **Transparency and auditability**  
   Preserve provenance so outputs can be verified, reproduced, and investigated.

---

## Operator Responsibilities

Before running against any real target, the operator must:
- Confirm permission to access and collect data (policy/contract/authorization).
- Configure safe request behavior (timeouts, delays, retries/backoff).
- Ensure output storage and logs do not expose sensitive data.
- Define retention/deletion rules for outputs as required by policy/contract.
- Stop and escalate when signals indicate restrictions or unintended impact.

This template provides tools to support safe operation, but **does not replace** authorization and compliance review.

---

## Legal and Policy Considerations

### Terms of Service and acceptable use
- Many sites restrict automated access, reuse, and redistribution of content in their Terms of Service.
- If the target prohibits scraping, do not proceed without explicit authorization from the rights-holder.
- Prefer official APIs when available and permitted.

### robots.txt
- `robots.txt` often reflects site operator expectations and can be relevant depending on contract context and jurisdiction.
- This project does not automatically parse/enforce robots.txt; you must review it before running and decide how to proceed.

### Intellectual property, database rights, and redistribution
- Product images, descriptions, curated listings, and page layouts may be protected by copyright and/or database rights.
- Internal collection for an authorized purpose can have different obligations than republishing or redistributing the same content.
- Prefer collecting **minimal factual fields** and storing URLs as references instead of copying large blocks of text or media.

### Access controls and anti-circumvention boundaries
- Do not bypass access controls (authentication walls, paywalls, CAPTCHAs, managed challenges) in ways that violate law or policy.
- If strong anti-bot defenses are present, reconsider scope: seek permission, use an API, or adjust requirements.

### Jurisdiction and cross-border considerations
- Data protection and contractual requirements may vary by jurisdiction.
- If outputs will be transferred across borders or shared with third parties, confirm applicable requirements and client policies.

---

## Privacy and Personal Data Handling

### Recommended data classification
When defining target fields, classify each field:
- **Non-personal**: product title, price, SKU, availability, product URL
- **Potentially personal**: seller names if individuals, contact details, user-generated content
- **Sensitive**: avoid unless explicitly authorized and necessary

### Minimization and purpose limitation
- Collect only fields required for the documented purpose.
- Avoid collecting user profiles, reviews, emails, phone numbers, or identifiers unless explicitly authorized.

### Retention and deletion
- Define a retention window for outputs and logs.
- Implement deletion procedures if required by contract, policy, or privacy obligations.

---

## Built-in Safeguards and Operational Controls (Project-Specific)

This template includes configuration-driven controls that support responsible operation. They reduce risk, but do not guarantee compliance.

### Rate limiting / politeness
- Use `http.delay_seconds` to reduce load on the target.
- In **detail-follow mode**, this delay is applied **between detail page fetches**.
- Start conservatively and increase only when safe and permitted.

### Retries and backoff
- Retries can improve reliability but can increase load if misconfigured.
- Fetch retries are applied for:
  - HTTP `429`
  - HTTP `5xx`
  - transient network exceptions
- Other `4xx` responses generally do **not** retry.
- Optional backoff/jitter controls:
  - `http.retry_backoff_seconds`
  - `http.retry_backoff_multiplier`
  - `http.retry_jitter_seconds`

**Important nuance:** `http.max_retries` is used as “maximum attempts,” not “retries after the first attempt.”  
For example, `max_retries: 3` means up to **3 total attempts**.

### Timeouts
- Configure `http.timeout` to prevent hung runs and uncontrolled resource usage.

### Identification via User-Agent
- Configure a descriptive `http.user_agent` aligned with authorized use.
- If required, include a contact channel or client identifier in the UA string.

### Deterministic testing (no live scraping in tests)
- Unit tests rely on fixtures and mocks; CI does not scrape live sites.
- `--demo` runs against local HTML fixtures via a file-based fetcher.

### Traceability and URL normalization
This template preserves provenance and helps auditing:
- `source_list_url` is added to **all** records.
- `detail_url` is added to records in **detail-follow mode**.
- Any field name ending with `*_url` is treated as URL-like and normalized to absolute form using `urljoin()`:
  - list-only mode uses `list_url` as the base
  - detail-follow mode uses `detail_url` as the base for detail fields

---

## Security Practices for Secrets, Proxies, and Configuration

### Secrets and credentials
- Do not commit secrets to git.
- Store credentials/tokens in environment variables or a secret manager when extending this template.
- Use `.env` locally only; never commit `.env`.

### Proxy configuration
- Proxy credentials must be treated as secrets.
- Standard environment variables (`HTTP_PROXY`, `HTTPS_PROXY`) are supported by typical HTTP stacks and are suitable for secure runtime configuration.

### Least privilege
- If authentication is required for a target, use accounts with minimal permissions and rotate credentials periodically.

---

## Output Data Security

### Storage location and access control
- Store outputs in approved locations with appropriate filesystem permissions.
- Consider encryption at rest if outputs are sensitive or contract-restricted.
- Do not upload scraped datasets to public repositories.

### Sensitive data in outputs
- If sensitive fields must be collected, encrypt outputs and restrict distribution.
- Redact or exclude sensitive fields before sharing results.

### Integrity and provenance
Preserve enough context to reproduce and audit results:
- target name and config version/hash (recommended for delivery)
- run timestamp (recommended)
- source URLs (already supported via traceability fields)

---

## Logging and Observability Hygiene

### Avoid sensitive data leakage
- Do not log secrets, tokens, or personal data.
- Prefer logging:
  - record counts
  - error counts by category
  - missing-field counts (quality report)

### Logging level
- Use `INFO` for normal runs.
- Use `DEBUG` only in controlled environments and store logs securely.

---

## Safe Operation Notes (Project-Specific Nuances)

### `--dry-run` still fetches URLs
- `--dry-run` does **not** write output files, but it **still performs network fetch and parsing**.
- Use it as a safer iteration tool (no output side effects), not as a “no-network” mode.

### Partial failures in detail-follow mode
- In detail-follow mode, failed detail fetches are typically **skipped** (with errors reported).
- The run can still succeed if at least one record is produced.
- Treat skip rates (e.g., many failures) as an operational health signal and reassess throttling/permission.

### Run fails on “no records”
- If parsing yields zero records, the CLI exits with failure. This prevents silent “success with empty data.”

---

## Responsible Use Checklists

### Pre-run checklist
1. Permission confirmed (Terms/policy reviewed; authorization documented).
2. `robots.txt` reviewed (manual).
3. Scope and fields confirmed (data minimization applied).
4. Safe request controls set:
   - `http.delay_seconds` (conservative)
   - `http.timeout` (reasonable)
   - `http.max_retries` + backoff/jitter (modest)
5. User-Agent configured (`http.user_agent`).
6. Outputs stored securely (approved location, correct access controls).
7. Dry-run used for iteration (with awareness that it still fetches).

### Delivery checklist (for a client engagement)
- Example commands run successfully in the delivery environment.
- Target config validates cleanly (schema and mode selection correct).
- URL normalization verified (`*_url` fields resolve correctly).
- Output schema (headers/fields) matches requirements.
- Rate limits/retries/backoff align with permissions and target behavior.
- Logs do not leak sensitive data; secrets are not in the repo.
- Operational instructions included (config location, scheduling approach, where outputs/logs go).
- Compliance notes acknowledged (ToS/robots/privacy/data policy).

---

## When to Stop and Escalate

Stop the run and reassess if you observe:
- CAPTCHAs, managed challenges, or other clear bot restrictions.
- Sustained `429` or `403` responses suggesting rate limits or access restrictions.
- Evidence of overload or complaints from the target operator.
- Unexpected personal/sensitive data appearing in output.
- Requests to implement bypass/evasion techniques that may violate law or policy.

When escalating, document:
- timestamp, target name, config version
- HTTP status/error distribution
- sample failing URLs (if permitted to store)
- current throttling settings (`delay_seconds`, retries, timeout)

---

## References Within This Repository

- `docs/operations.md` — runtime setup, scheduling patterns, exit codes, troubleshooting
- `docs/CONFIG_GUIDE.md` — target schema, selector syntax, settings behavior, common mistakes
- `docs/testing.md` — deterministic testing approach and how to extend safely
- `docs/architecture.md` — pipeline design and data contract (traceability, URL normalization)