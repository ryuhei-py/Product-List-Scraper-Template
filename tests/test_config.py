import pytest

from product_scraper.config import ConfigError, get_targets_from_config, load_settings_config


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


def test_get_targets_from_config_empty_detail_selectors():
    config = {
        "targets": [
            {
                "name": "empty-detail",
                "list_url": "https://example.com",
                "link_selector": ".link",
                "detail_selectors": {},
            }
        ]
    }

    with pytest.raises(ConfigError):
        get_targets_from_config(config)


def test_get_targets_from_config_valid_list_only():
    config = {
        "targets": [
            {
                "name": "list-only",
                "list_url": "https://example.com/list",
                "item_selector": ".item",
                "item_fields": {
                    "title": ".title",
                    "price": ".price",
                },
            }
        ]
    }

    targets = get_targets_from_config(config)

    assert len(targets) == 1
    assert targets[0]["item_selector"] == ".item"
    assert targets[0]["item_fields"]["title"] == ".title"


@pytest.mark.parametrize(
    "config",
    [
        {
            "targets": [
                {
                    "name": "missing-item-fields",
                    "list_url": "https://example.com",
                    "item_selector": ".item",
                }
            ]
        },
        {
            "targets": [
                {
                    "name": "empty-item-fields",
                    "list_url": "https://example.com",
                    "item_selector": ".item",
                    "item_fields": {},
                }
            ]
        },
        {
            "targets": [
                {
                    "name": "empty-item-selector",
                    "list_url": "https://example.com",
                    "item_selector": "",
                    "item_fields": {"title": ".title"},
                }
            ]
        },
    ],
)
def test_get_targets_from_config_invalid_list_only(config):
    with pytest.raises(ConfigError):
        get_targets_from_config(config)


def test_load_settings_config_missing_file_returns_empty_dict(tmp_path):
    settings_path = tmp_path / "missing_settings.yml"

    assert not settings_path.exists()

    result = load_settings_config(settings_path)

    assert result == {}


def test_load_settings_config_empty_file_returns_empty_dict(tmp_path):
    settings_path = tmp_path / "empty_settings.yml"
    settings_path.write_text("", encoding="utf-8")

    result = load_settings_config(settings_path)

    assert result == {}


def test_load_settings_config_non_mapping_raises_value_error(tmp_path):
    settings_path = tmp_path / "list_settings.yml"
    settings_path.write_text("- a\n- b\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_settings_config(settings_path)
