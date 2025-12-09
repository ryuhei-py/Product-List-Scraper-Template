import pytest

from product_scraper.fetcher import FetchError, Fetcher


class DummyResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


def test_get_success(monkeypatch):
    fetcher = Fetcher(timeout=5.0, max_retries=2, headers={"User-Agent": "test"})
    response = DummyResponse(status_code=200, text="ok")

    calls = []

    def fake_get(url, timeout, headers):
        calls.append((url, timeout, headers))
        return response

    monkeypatch.setattr("product_scraper.fetcher.requests.get", fake_get)

    result = fetcher.get("https://example.com")

    assert result == "ok"
    assert len(calls) == 1
    assert calls[0][1] == 5.0
    assert calls[0][2] == {"User-Agent": "test"}


def test_retries_on_5xx_then_succeeds(monkeypatch):
    fetcher = Fetcher(max_retries=3)
    responses = iter(
        [
            DummyResponse(status_code=502),
            DummyResponse(status_code=503),
            DummyResponse(status_code=200, text="done"),
        ]
    )

    call_count = {"count": 0}

    def fake_get(url, timeout, headers):
        call_count["count"] += 1
        return next(responses)

    monkeypatch.setattr("product_scraper.fetcher.requests.get", fake_get)

    result = fetcher.get("https://example.com/retry")

    assert result == "done"
    assert call_count["count"] == 3


def test_no_retry_on_4xx(monkeypatch):
    fetcher = Fetcher(max_retries=5)
    response = DummyResponse(status_code=404, text="not found")
    calls = {"count": 0}

    def fake_get(url, timeout, headers):
        calls["count"] += 1
        return response

    monkeypatch.setattr("product_scraper.fetcher.requests.get", fake_get)

    with pytest.raises(FetchError) as excinfo:
        fetcher.get("https://example.com/missing")

    assert "404" in str(excinfo.value)
    assert calls["count"] == 1


def test_fetch_error_after_exhausting_retries(monkeypatch):
    fetcher = Fetcher(max_retries=2)
    responses = iter(
        [
            DummyResponse(status_code=503),
            DummyResponse(status_code=503),
        ]
    )
    calls = {"count": 0}

    def fake_get(url, timeout, headers):
        calls["count"] += 1
        return next(responses)

    monkeypatch.setattr("product_scraper.fetcher.requests.get", fake_get)

    with pytest.raises(FetchError) as excinfo:
        fetcher.get("https://example.com/unavailable")

    assert "503" in str(excinfo.value)
    assert calls["count"] == 2
