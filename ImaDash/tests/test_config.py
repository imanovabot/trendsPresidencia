"""
Tests para config.py — validación de Settings.
"""

import pytest
from pydantic import ValidationError
from config import Settings


def test_settings_defaults():
    """Valores por defecto de Settings."""
    with pytest.raises(ValidationError):
        # Debería fallar si faltan campos requeridos
        Settings()


def test_settings_with_env(monkeypatch):
    """Settings desde variables de entorno."""
    env = {
        "DATABASE_URL": "postgresql://user:pass@host/db",
        "IMAP_SERVER": "imap.example.com",
        "IMAP_USER": "user@example.com",
        "IMAP_PASS": "secret",
        "CALDAV_URL": "https://caldav.example.com",
        "CALDAV_USER": "caldav_user",
        "CALDAV_PASS": "caldav_secret",
        "GITHUB_TOKEN": "ghp_testtoken",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "WHISPER_MODEL": "small",
    }
    for key, val in env.items():
        monkeypatch.setenv(key, val)

    settings = Settings()

    assert settings.database_url == env["DATABASE_URL"]
    assert settings.imap_server == env["IMAP_SERVER"]
    assert settings.imap_user == env["IMAP_USER"]
    assert settings.github_token == env["GITHUB_TOKEN"]
    assert settings.whisper_model == "small"


def test_cors_origins_parsing(monkeypatch):
    """Parsing de CORS_ORIGINS (lista separada por comas)."""
    # Set required env vars
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_OWNER", "test-owner")
    monkeypatch.setenv("GITHUB_REPO", "test-repo")
    monkeypatch.setenv("IMAP_SERVER", "imap.test.com")
    monkeypatch.setenv("IMAP_USER", "test@test.com")
    monkeypatch.setenv("IMAP_PASS", "test-pass")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost,https://example.com")
    settings = Settings()
    assert settings.cors_origins == "http://localhost,https://example.com"


def test_imapi_base_url(monkeypatch):
    """URL base de ImaPi."""
    # Set required env vars
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_OWNER", "test-owner")
    monkeypatch.setenv("GITHUB_REPO", "test-repo")
    monkeypatch.setenv("IMAP_SERVER", "imap.test.com")
    monkeypatch.setenv("IMAP_USER", "test@test.com")
    monkeypatch.setenv("IMAP_PASS", "test-pass")
    monkeypatch.setenv("IMAPI_BASE_URL", "http://localhost:9000")
    settings = Settings()
    assert settings.imapi_base_url == "http://localhost:9000"
