from product_scraper.parser import ListPageParser


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
