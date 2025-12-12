from pathlib import Path

from product_scraper.cli import run_pipeline
from product_scraper.fetcher import FetchError
from product_scraper.fetcher import FileFetcher as CLIFileFetcher


def test_run_pipeline_smoke(monkeypatch, tmp_path):
    list_url = "https://example.com/products"
    list_html = """
    <html>
        <body>
            <a class="product-link" href="product/1">Product 1</a>
            <a class="product-link" href="https://example.com/product/2">Product 2</a>
        </body>
    </html>
    """

    detail_pages = {
        "https://example.com/product/1": """
        <html>
            <h1 class="title">Item One</h1>
            <div class="price">$10</div>
            <img class="image" src="https://example.com/img1.jpg" />
            <div class="description">First item</div>
        </html>
        """,
        "https://example.com/product/2": """
        <html>
            <h1 class="title">Item Two</h1>
            <div class="price">$20</div>
            <img class="image" src="https://example.com/img2.jpg" />
            <div class="description">Second item</div>
        </html>
        """,
    }

    class FakeFetcher:
        def __init__(self, *_, **__):
            pass

        def get(self, url):
            if url == list_url:
                return list_html
            if url in detail_pages:
                return detail_pages[url]
            raise FetchError(f"Unexpected URL: {url}")

    monkeypatch.setattr("product_scraper.cli.Fetcher", FakeFetcher)

    target_config = {
        "list_url": list_url,
        "link_selector": "a.product-link",
        "detail_selectors": {
            "title": "h1.title",
            "price": ".price",
            "image_url": "img.image",
            "description": ".description",
        },
    }

    output_path = Path(tmp_path / "products.csv")

    exit_code = run_pipeline(
        target_config=target_config,
        output_path=output_path,
        dry_run=False,
        settings=None,
    )

    assert exit_code == 0
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_demo_mode_writes_csv(monkeypatch, tmp_path):
    fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures"

    target_config = {
        "name": "demo",
        "list_url": (fixtures_dir / "list.html").as_uri(),
        "link_selector": "a.product-link",
        "detail_selectors": {
            "title": "h1.product-title",
            "price": ".price",
            "image_url": "img.product-image",
            "description": ".description",
        },
    }

    output_path = tmp_path / "demo.csv"

    exit_code = run_pipeline(
        target_config=target_config,
        output_path=output_path,
        dry_run=False,
        settings=None,
        fetcher_class=CLIFileFetcher,
    )

    assert exit_code == 0
    assert output_path.exists()
    with output_path.open(encoding="utf-8") as f:
        lines = f.read().strip().splitlines()
    # header + 2 detail rows
    assert len(lines) == 3


def test_run_pipeline_list_only_dry_run(monkeypatch, tmp_path, capsys):
    list_url = "https://example.com/products"
    list_html = """
    <html>
        <body>
            <div class="item">
                <a class="title" href="/p1" title="Full One">One</a>
                <img class="image" src="/img1.jpg" />
            </div>
            <div class="item">
                <a class="title" href="https://example.com/p2" title="Full Two">Two</a>
                <img class="image" src="https://example.com/img2.jpg" />
            </div>
        </body>
    </html>
    """

    class FakeFetcher:
        def __init__(self, *_, **__):
            pass

        def get(self, url):
            if url == list_url:
                return list_html
            raise FetchError(f"Unexpected URL: {url}")

    monkeypatch.setattr("product_scraper.cli.Fetcher", FakeFetcher)

    target_config = {
        "list_url": list_url,
        "item_selector": ".item",
        "item_fields": {
            "title": "a.title::text",
            "product_url": "a.title@href",
            "image_url": "img.image@src",
        },
    }

    output_path = Path(tmp_path / "products.csv")

    exit_code = run_pipeline(
        target_config=target_config,
        output_path=output_path,
        dry_run=True,
        settings=None,
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    # Dry run does not write file
    assert not output_path.exists()
    # No stderr expected
    assert captured.err == ""
