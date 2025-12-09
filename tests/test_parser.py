from product_scraper.parser import DetailPageParser, ListPageParser


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
