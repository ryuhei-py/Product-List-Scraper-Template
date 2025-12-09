"""Parse product list pages and detail pages."""

from __future__ import annotations

from bs4 import BeautifulSoup


class ListPageParser:
    def __init__(self, link_selector: str) -> None:
        self.link_selector = link_selector

    def parse_list(self, html: str) -> list[str]:
        """Return list of product links found via the configured CSS selector."""
        soup = BeautifulSoup(html, "html.parser")
        links: list[str] = []

        for tag in soup.select(self.link_selector):
            href = tag.get("href")
            if href is None:
                continue
            cleaned = href.strip()
            if not cleaned:
                continue
            links.append(cleaned)

        return links


class DetailPageParser:
    def __init__(self, selectors: dict[str, str]) -> None:
        self.selectors = selectors

    def parse_detail(self, html: str) -> dict[str, str | None]:
        """Extract detail fields (title, price, image_url, description) from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        fields = ["title", "price", "image_url", "description"]
        data: dict[str, str | None] = {}

        for field in fields:
            selector = self.selectors.get(field)
            if not selector:
                data[field] = None
                continue

            element = soup.select_one(selector)
            if element is None:
                data[field] = None
                continue

            if field == "image_url":
                value = element.get("src") or element.get_text(strip=True)
            else:
                value = element.get_text(strip=True)

            cleaned = value.strip() if value else ""
            data[field] = cleaned or None

        return data
