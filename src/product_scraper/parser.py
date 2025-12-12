"""Parse product list pages and detail pages."""

from __future__ import annotations

from typing import Any, Tuple

from bs4 import BeautifulSoup


def _parse_selector_spec(spec: str) -> Tuple[str, str | None, bool]:
    """
    Parse a selector spec into (css_selector, attr, text_mode).

    Supported formats:
    - "a.title@title" → css_selector="a.title", attr="title"
    - "a.title::attr(title)" → css_selector="a.title", attr="title"
    - "a.title::text" → css_selector="a.title", text_mode=True
    - "a.title" → css_selector="a.title", text_mode=True
    """
    if "::attr(" in spec and spec.endswith(")"):
        css_selector, attr_part = spec.split("::attr(", 1)
        attr = attr_part[:-1]
        return css_selector, attr, False

    if "@" in spec:
        css_selector, attr = spec.rsplit("@", 1)
        return css_selector, attr, False

    if spec.endswith("::text"):
        css_selector = spec[: -len("::text")]
        return css_selector, None, True

    return spec, None, True


def _extract_with_spec(root: Any, selector_spec: str) -> str | None:
    """
    Extract text or attribute from the first element matching the selector spec.

    Returns None if the element is missing or the extracted value is empty.
    """
    css_selector, attr, text_mode = _parse_selector_spec(selector_spec)
    element = root.select_one(css_selector)
    if element is None:
        return None

    if attr is not None:
        value = element.get(attr)
    else:
        value = element.get_text(strip=True) if text_mode else None

    if isinstance(value, str):
        value = value.strip()

    return value or None


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
        core_fields = ["title", "price", "image_url", "description"]
        all_fields = list(dict.fromkeys(core_fields + list(self.selectors.keys())))
        data: dict[str, str | None] = {}

        for field in all_fields:
            selector = self.selectors.get(field)
            if not selector:
                data[field] = None
                continue

            css_selector, attr, text_mode = _parse_selector_spec(selector)
            element = soup.select_one(css_selector)
            if element is None:
                data[field] = None
                continue

            if attr is not None:
                value = element.get(attr)
            elif field == "image_url":
                value = element.get("src") or element.get_text(strip=True)
            elif text_mode:
                value = element.get_text(strip=True)
            else:
                value = element.get_text(strip=True)

            if isinstance(value, str):
                value = value.strip()

            data[field] = value or None

        return data


class ListItemsParser:
    def __init__(self, item_selector: str, field_selectors: dict[str, str]) -> None:
        self.item_selector = item_selector
        self.field_selectors = field_selectors

    def parse_items(self, html: str) -> list[dict[str, Any]]:
        """Parse a list page of items where each item shares selectors for its fields."""
        soup = BeautifulSoup(html, "html.parser")
        items = soup.select(self.item_selector)
        records: list[dict[str, Any]] = []

        for item in items:
            record: dict[str, Any] = {}
            for field, selector_spec in self.field_selectors.items():
                record[field] = _extract_with_spec(item, selector_spec)
            records.append(record)

        return records
