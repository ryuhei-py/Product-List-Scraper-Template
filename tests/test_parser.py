from product_scraper.parser import DetailPageParser, ListItemsParser, ListPageParser


def test_parse_list_returns_links():
    html = """
    <html>
        <body>
            <a class="product-link" href=" https://example.com/p1 ">Product 1</a>
            <div><a class="product-link" href="https://example.com/p2">Product 2</a></div>
            <a class="other" href="https://example.com/ignore">Ignore</a>
            <a class="product-link" href="   ">Empty</a>
            <a class="product-link">Missing href</a>
        </body>
    </html>
    """
    parser = ListPageParser(link_selector="a.product-link")

    links = parser.parse_list(html)

    assert links == [
        "https://example.com/p1",
        "https://example.com/p2",
    ]


def test_parse_list_no_matches_returns_empty_list():
    html = """
    <html><body><p>No products here</p></body></html>
    """
    parser = ListPageParser(link_selector="a.product-link")

    links = parser.parse_list(html)

    assert links == []


def test_parse_detail_extracts_fields():
    html = """
    <html>
        <body>
            <h1 class="product-title">
                Awesome Product
            </h1>
            <div class="price">
                $19.99
            </div>
            <img class="product-image" src="https://example.com/image.jpg" />
            <div class="description">
                <p>Line one.</p>
                <p>Line two.</p>
            </div>
        </body>
    </html>
    """
    parser = DetailPageParser(
        selectors={
            "title": "h1.product-title",
            "price": ".price",
            "image_url": "img.product-image",
            "description": ".description",
        }
    )

    data = parser.parse_detail(html)

    assert data == {
        "title": "Awesome Product",
        "price": "$19.99",
        "image_url": "https://example.com/image.jpg",
        "description": "Line one.Line two.",
    }


def test_parse_detail_missing_selectors_and_elements():
    html = """
    <html>
        <body>
            <h1 class="product-title">Only Title</h1>
        </body>
    </html>
    """
    parser = DetailPageParser(
        selectors={
            "title": "h1.product-title",
            # price selector omitted intentionally
            "image_url": ".missing-image",
            "description": ".missing-description",
        }
    )

    data = parser.parse_detail(html)

    assert data["title"] == "Only Title"
    assert data["price"] is None
    assert data["image_url"] is None
    assert data["description"] is None


def test_parse_detail_extracts_extra_fields():
    html = """
    <html>
        <body>
            <h1 class="product-title">Product with SKU</h1>
            <div class="price">$10.00</div>
            <img class="product-image" src="https://example.com/img.jpg" />
            <div class="description">Desc</div>
            <span class="sku-value">SKU-123</span>
        </body>
    </html>
    """
    parser = DetailPageParser(
        selectors={
            "title": "h1.product-title",
            "price": ".price",
            "image_url": "img.product-image",
            "description": ".description",
            "sku": ".sku-value",
        }
    )

    data = parser.parse_detail(html)

    assert data["title"] == "Product with SKU"
    assert data["sku"] == "SKU-123"


def test_selector_spec_supports_attr_and_text():
    html = """
    <html>
        <body>
            <a class="title" title="FULL">Short</a>
        </body>
    </html>
    """
    parser = DetailPageParser(
        selectors={
            "title": "a.title::text",
            "title_attr": "a.title@title",
            "title_attr_scrapy": "a.title::attr(title)",
        }
    )

    data = parser.parse_detail(html)

    assert data["title"] == "Short"
    assert data["title_attr"] == "FULL"
    assert data["title_attr_scrapy"] == "FULL"


def test_list_items_parser_parses_multiple_items():
    html = """
    <html>
        <body>
            <div class="item">
                <span class="name">First</span>
                <span class="price">$10</span>
            </div>
            <div class="item">
                <span class="name">Second</span>
                <span class="price">$20</span>
            </div>
        </body>
    </html>
    """
    parser = ListItemsParser(
        item_selector=".item",
        field_selectors={
            "name": ".name",
            "price": ".price::text",
        },
    )

    records = parser.parse_items(html)

    assert len(records) == 2
    assert records[0]["name"] == "First"
    assert records[0]["price"] == "$10"
    assert records[1]["name"] == "Second"
    assert records[1]["price"] == "$20"
