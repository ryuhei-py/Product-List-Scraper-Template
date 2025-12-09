# Security, ethics, and legal notes

This document summarizes important security, ethical, and legal considerations when using the Product List Scraper Template.

> **Disclaimer**  
> This document does **not** constitute legal advice.  
> Laws, regulations, and website terms can change.  
> Always consult a qualified legal professional for specific use cases.

---

## 1. Respect websites and infrastructure

This section explains how to respect target sites and their infrastructure.

### 1.1 robots.txt

Many websites publish a `robots.txt` file that describes:

- Which paths may or may not be accessed by automated agents
- Rate and access policies for crawlers

You should:

- Check `https://example.com/robots.txt` (replace with your target domain)
- Respect disallowed paths whenever possible
- Avoid scraping areas that are explicitly forbidden

### 1.2 Terms of Service (ToS)

Each site typically has Terms of Service (ToS) that may contain clauses about:

- Automated access
- Data usage and redistribution
- Reverse engineering

Before scraping:

- Review the site’s ToS and policies.
- Confirm that your intended use (frequency, data type, redistribution) is permitted.

If in doubt, consider:

- Seeking permission from the site owner
- Using official APIs instead of scraping, when available

---

## 2. Rate limiting and resource usage

This section covers reasonable access patterns to avoid overloading sites.

### 2.1 Reasonable access patterns

- Configure delays between requests (e.g. `delay_seconds` in `settings.yml`).
- Limit concurrency and total requests per minute.
- Avoid long, aggressive crawls during business-peak hours.

### 2.2 Detection and blocking

If the site:

- Starts returning captchas
- Responds with 429 (Too Many Requests)
- Begins blocking your IP

You should:

- Reduce frequency
- Pause or stop the scraper
- Reevaluate your scraping strategy

---

## 3. Data privacy and compliance

This section highlights privacy and regulatory considerations.

### 3.1 Personal data

Scraping may incidentally capture personal data (names, emails, addresses, etc.). Depending on jurisdiction, this can trigger compliance requirements (GDPR, CCPA, etc.).

Best practices:

- Avoid collecting personal data unless absolutely necessary and legally permitted.
- Avoid scraping sensitive categories (health, financial, etc.).
- If you must handle personal data:
  - Consult legal expertise
  - Implement proper data protection and retention policies

### 3.2 Jurisdiction and regulations

Data protection and scraping laws vary by country and region.

- Check applicable laws in:
  - Your jurisdiction
  - The hosting location of the target site
  - The location of users whose data may be collected

---

## 4. Security considerations

This section lists security practices for environments and dependencies.

### 4.1 Environment and secrets

- If you use API keys or authentication tokens:
  - Store them in environment variables or a secure secrets manager
  - Never commit them to the repository
  - Use `.env` and `.env.example` carefully:
    - `.env` should be in `.gitignore`
    - `.env.example` should contain only placeholder values

### 4.2 Dependencies

- Keep dependencies up to date to avoid known vulnerabilities.
- Use `pip install -r requirements.txt` from trusted sources only.
- Consider using tools like `pip-audit` or dependency scanning in CI.

### 4.3 File system and output

- Verify that output paths (e.g. `sample_output/`) are safe and under your control.
- Avoid writing files to public directories in shared environments.

---

## 5. Usage in client work

This section outlines how to use the template responsibly in client projects.

When using this template for client projects (e.g. freelance platforms):

- Clarify in your proposals:
  - What data will be collected
  - How often scraping will run
  - How you will respect the target site’s policies
- If the client specifies a target site:
  - Confirm that they have the right to collect and use that data
  - Make clear that compliance with legal and contractual obligations is ultimately the client’s responsibility
- Include basic safeguards in your implementation:
  - Configurable delays and limits
  - Logging of requests and outcomes

---

## 6. Summary

This section summarizes the key actions when using the template.

1. **Check policies** — robots.txt and Terms of Service.
2. **Limit impact** — use reasonable rates and delays.
3. **Protect privacy** — avoid or carefully handle personal data.
4. **Secure the environment** — manage secrets and dependencies safely.
5. **Seek legal advice** for non-trivial or high-risk use cases.

By following these principles, you can use the Product List Scraper Template in a way that is more likely to be sustainable, compliant, and acceptable to both clients and site owners.
