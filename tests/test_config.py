import os

from config import get_settings


def test_get_settings_defaults(monkeypatch):
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("NVD_LOOKBACK_DAYS", raising=False)
    monkeypatch.delenv("INGEST_INTERVAL_HOURS", raising=False)

    settings = get_settings()

    assert settings.env == "development"
    assert settings.log_level == "INFO"
    assert settings.origins_list == ["*"]
    assert settings.nvd_lookback_days == 7
    assert settings.ingest_interval_hours == 6


def test_get_settings_parses_csv_origins(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = get_settings()

    assert settings.log_level == "debug"
    assert settings.origins_list == ["http://localhost:3000", "http://127.0.0.1:3000"]
