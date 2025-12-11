import pytest

from product_scraper.config import ConfigError, get_targets_from_config


def test_get_targets_from_config_valid():
    config = {
        "targets": [
            {
                "name": "example",
                "list_url": "https://example.com/products",
                "link_selector": "a.product-link",
                "detail_selectors": {"title": "h1"},
            }
        ]
    }

    targets = get_targets_from_config(config)

    assert len(targets) == 1
    assert targets[0]["name"] == "example"


@pytest.mark.parametrize(
    "config",
    [
        {},
        {"targets": []},
    ],
)
def test_get_targets_from_config_missing_or_empty_targets(config):
    with pytest.raises(ConfigError):
        get_targets_from_config(config)


def test_get_targets_from_config_missing_required_fields():
    config = {
        "targets": [
            {
                "name": "bad",
                "list_url": "",
                "link_selector": "",
                "detail_selectors": {},
            }
        ]
    }

    with pytest.raises(ConfigError):
        get_targets_from_config(config)


def test_get_targets_from_config_non_mapping_target():
    config = {"targets": ["not-a-dict"]}

    with pytest.raises(ConfigError):
        get_targets_from_config(config)


def test_get_targets_from_config_invalid_detail_selectors():
    config = {
        "targets": [
            {
                "name": "bad-detail",
                "list_url": "https://example.com",
                "link_selector": ".link",
                "detail_selectors": "not-a-dict",
            }
        ]
    }

    with pytest.raises(ConfigError):
        get_targets_from_config(config)
