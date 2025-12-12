# Security and legal guidance
This document provides practical guidance on security, legal, and ethical considerations when using and adapting this scraping template. It is not legal advice; consult qualified counsel or your client’s compliance team for regulated environments or high-risk data.

---

## Core principles
This section lists non-negotiable principles.

### Respect site rules and user expectations
- Read and follow the target site’s Terms of Service (ToS) and usage policies.
- Review `robots.txt` as a signal of crawl preferences (it may not be legally binding by itself, but it is operationally meaningful).
- Avoid abusive access patterns (high request rates, parallel hammering, bypassing protections).

### Minimize harm
- Collect only what you need (data minimization).
- Avoid collecting personal data unless you have explicit authorization and a lawful basis.
- Keep your footprint small and predictable (timeouts, rate limits, backoff).

### Be transparent with clients
- Ensure the client confirms they are authorized to collect the data.
- Ensure the client understands operational risks (blocking, HTML changes, data drift).
- Ensure the client agrees on data scope, retention, and security requirements.

---

## Responsible use checklist
This section lists quick checks before running or delivering.

- Review `robots.txt` and ToS; proceed only if permitted/authorized.
- Confirm lawful basis/consent for any personal data; prefer non-personal data.
- Throttle appropriately (`delay_seconds`, retries/backoff) to avoid overload.
- Use a descriptive User-Agent and client-approved headers.
- Keep outputs and secrets controlled: gitignore runtime configs, avoid logging sensitive data, store CSVs in approved locations.

---

## Legal considerations
This section covers common legal factors.

Scraping legality depends on jurisdiction, ToS, the type of data collected, and how it is used.

### Terms of Service (contractual obligations)
- A site’s ToS may restrict automated access. Even if data is publicly visible, ToS violations can create contractual risk.
- Document the ToS review outcome for the target.
- If the site explicitly prohibits scraping, consider alternatives (official APIs, data feeds/partners, licensed data sources).

### Robots.txt
- `robots.txt` is a machine-readable convention describing crawl preferences. It does not grant permission, but it is commonly treated as a baseline signal for good-faith behavior.
- If `robots.txt` disallows your path, treat it as a strong warning. If you proceed for legitimate reasons, obtain explicit client authorization and document it.

### Copyright and database rights
- Even if data is public, the compilation/presentation may be protected. Reproducing large parts of a database can carry risk.
- Extract only necessary fields, avoid cloning entire catalogs unless authorized, and respect attribution requirements if applicable.

### Personal data / privacy
- If you collect personal data (names, emails, phone numbers, profiles, identifiers), privacy laws may apply (jurisdiction-dependent).
- Prefer “non-personal” product/catalog data.
- If personal data is required: confirm lawful basis and purpose limitation; implement access controls and retention limits; encrypt at rest and in transit where required; avoid sharing raw data broadly.

---

## Ethical and operational safeguards
This section describes safeguards built into the template.

### Rate limiting and delays
- Use `http.delay_seconds` for politeness and stability.
- Increase delays for fragile sites or when seeing 429 responses.

### Retries and backoff
- Retries should be limited and reserved for transient failures (commonly 429 and 5xx).
- Optional backoff knobs exist to reduce repeated bursts.
- Keep default backoff off for local iteration; enable controlled backoff for production runs, especially if seeing blocks.

### Deterministic testing (no live scraping in tests)
- Tests should not scrape real sites. This reduces accidental policy violations, flaky CI failures, and unintended load on targets.
- Use HTML fixtures and mocked fetchers.

### Traceability
- Records include `source_list_url` (always) and `detail_url` (detail-follow mode).
- This supports auditing: where data came from, which page produced which record, quick investigation when content drifts.

---

## Security practices for client delivery
This section lists security guidelines when delivering to clients.

### Secrets and credentials
- Do not hardcode secrets in code or commit them to Git.
- Use `.env` (local) and environment variables (production).
- Keep `.env` out of version control; provide `.env.example` with placeholders only.
- If a client requires authenticated scraping (for example, session cookies or tokens), treat them as secrets.

### Output data handling
- Scraped data may be sensitive in business context even if it is public.
- Store outputs in client-controlled locations (S3, database, secure shared drive).
- Apply least-privilege access; avoid emailing raw data unless required and protected; consider encryption if the client requires it.

### Logging
- Logs can accidentally store sensitive information.
- Do not log credentials, tokens, cookies.
- Avoid logging full HTML responses.
- Log URLs and status codes; log only necessary context. For errors, prefer summarized messages with pointers (URL, selector name) rather than raw content dumps.

---

## Anti-bot systems and boundaries
This section highlights limits around anti-bot protections.

- Many sites employ anti-bot systems (rate limiting, fingerprinting, CAPTCHAs, managed challenges).
- Do not attempt to break security measures or bypass access controls in a way that violates law or policy.
- If a target uses strong anti-bot protections, consider official APIs, partnership/licensed access, lowering frequency and scope, and documenting compliance posture with client approval.
- If a client requests aggressive bypass techniques, reassess legality/compliance and scope.

---

## Practical compliance checklist
This section provides a pre-run checklist.

- [ ] ToS reviewed and compatible with intended use (documented).
- [ ] Data scope defined (fields, volume, frequency).
- [ ] Personal data avoided unless explicitly authorized and compliant.
- [ ] Rate limits defined (`delay_seconds`, retries tuned).
- [ ] Backoff enabled if needed (controlled values).
- [ ] Output storage location agreed and secured.
- [ ] Logs reviewed to avoid sensitive data leakage.
- [ ] Test plan uses fixtures/mocks (no live scraping in CI).
- [ ] Client acknowledges operational risks (blocks, HTML changes, data drift).

---

## When to stop and escalate
This section lists conditions for escalation.

- The site explicitly prohibits automated collection in ToS and the client cannot provide authorization/alternative access.
- You encounter strong anti-bot barriers (CAPTCHAs/challenges) repeatedly.
- The client requests collection of personal data without a clear lawful basis.
- The client asks for “stealth/bypass” approaches that appear to violate policy or law.

---

## References within this repo
This section links to related documents.

- `docs/CONFIG_GUIDE.md` — schema rules and selector syntax.
- `docs/operations.md` — operational tuning (timeouts, retries, delays, troubleshooting).
- `docs/testing.md` — deterministic tests and safe development workflow.

---

_Last updated: 2025-12-12_
