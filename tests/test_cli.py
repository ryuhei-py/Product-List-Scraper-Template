import csv
from pathlib import Path

import product_scraper.cli as cli
from product_scraper.cli import run_pipeline
from product_scraper.fetcher import FetchError
from product_scraper.fetcher import FileFetcher as CLIFileFetcher


def test_run_pipeline_smoke(monkeypatch, tmp_path, capsys):
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
    captured = capsys.readouterr()
    assert "missing_counts" in captured.out


def test_run_pipeline_normalizes_url_fields(monkeypatch, tmp_path):
    list_url = "https://example.com/products"
    list_html = """
    <html>
        <body>
            <a class="product-link" href="/product/1">Product 1</a>
        </body>
    </html>
    """

    detail_pages = {
        "https://example.com/product/1": """
        <html>
            <h1 class="title">Item One</h1>
            <a class="buy" href="/buy/1">Buy</a>
            <img class="hero" src="/img/1.jpg" />
        </html>
        """
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
            "product_url": "a.buy@href",
            "image_url": "img.hero@src",
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
    with output_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    row = rows[0]
    assert row["product_url"] == "https://example.com/buy/1"
    assert row["image_url"] == "https://example.com/img/1.jpg"
    assert row["detail_url"] == "https://example.com/product/1"
    assert row["source_list_url"] == list_url


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
    assert "missing_counts" in captured.out


def test_main_uses_settings_output_when_not_provided(monkeypatch, tmp_path):
    output_dir = tmp_path / "out"
    output_filename = "from_settings.csv"
    expected = output_dir / output_filename
    target_config = {
        "name": "example",
        "list_url": "https://example.com",
        "item_selector": ".item",
        "item_fields": {"title": ".title"},
    }

    def fake_load_targets_config(path):
        return {"targets": [target_config]}

    def fake_get_targets_from_config(config):
        return config["targets"]

    def fake_load_settings_config(path):
        return {
            "output": {
                "directory": str(output_dir),
                "csv_filename": output_filename,
            }
        }

    called = {}

    def fake_run_pipeline(**kwargs):
        called["output_path"] = kwargs["output_path"]
        return 0

    monkeypatch.setattr(cli, "load_targets_config", fake_load_targets_config)
    monkeypatch.setattr(cli, "get_targets_from_config", fake_get_targets_from_config)
    monkeypatch.setattr(cli, "load_settings_config", fake_load_settings_config)
    monkeypatch.setattr(cli, "run_pipeline", fake_run_pipeline)

    exit_code = cli.main(["--config", "ignored.yml"])

    assert exit_code == 0
    assert called["output_path"] == expected
