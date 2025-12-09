"""Parse product list pages to extract product links."""

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
