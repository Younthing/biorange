import pytest

from biorange.core.config.config_model import APISettings, DatabaseSettings, Settings


def test_api_settings_default_values():
    api_settings = APISettings()
    assert api_settings.key == "default_api_key"
    assert api_settings.url == "https://api.default.com"


def test_api_settings_custom_values():
    api_settings = APISettings(key="custom_key", url="https://api.custom.com")
    assert api_settings.key == "custom_key"
    assert api_settings.url == "https://api.custom.com"


def test_database_settings_default_values():
    database_settings = DatabaseSettings()
    assert database_settings.url == "default_database_url"
    assert database_settings.pool_size == 5


def test_database_settings_custom_values():
    database_settings = DatabaseSettings(url="custom_database_url", pool_size=10)
    assert database_settings.url == "custom_database_url"
    assert database_settings.pool_size == 10


def test_settings_default_values():
    settings = Settings()
    assert settings.api.key == "default_api_key"
    assert settings.api.url == "https://api.default.com"
    assert settings.database.url == "default_database_url"
    assert settings.database.pool_size == 5


def test_settings_custom_values():
    api_settings = APISettings(key="custom_key", url="https://api.custom.com")
    database_settings = DatabaseSettings(url="custom_database_url", pool_size=10)
    settings = Settings(api=api_settings, database=database_settings)

    assert settings.api.key == "custom_key"
    assert settings.api.url == "https://api.custom.com"
    assert settings.database.url == "custom_database_url"
    assert settings.database.pool_size == 10
