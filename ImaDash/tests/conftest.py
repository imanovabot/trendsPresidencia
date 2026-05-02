"""
Fixtures compartidos para tests de ImaDash.

IMPORTANTE: Mockeamos sqlalchemy de forma ligera pero suficiente para:
- Definir modelos (Column, Integer, String, DateTime, ForeignKey, relationship)
- Crear AsyncSession mock (no se usa en tests de routers)
"""

import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# ============================================================================
# Mock global de sqlalchemy (suficiente para definición de modelos)
# ============================================================================

sqlalchemy_mock = MagicMock(name="sqlalchemy-module")

# Submódulos
sqlalchemy_orm_mock = MagicMock(name="sqlalchemy.orm")
sqlalchemy_mock.orm = sqlalchemy_orm_mock

# Column, Integer, String, DateTime, ForeignKey, relationship
def create_column_mock(*args, **kwargs):
    col = MagicMock(name="Column")
    col.args = args
    col.kwargs = kwargs
    return col

sqlalchemy_mock.Column = create_column_mock
sqlalchemy_mock.Integer = MagicMock(name="Integer")
sqlalchemy_mock.String = MagicMock(name="String")
sqlalchemy_mock.DateTime = MagicMock(name="DateTime")
sqlalchemy_mock.ForeignKey = MagicMock(name="ForeignKey")
sqlalchemy_mock.relationship = MagicMock(name="relationship")

# AsyncSession (usado en anotaciones de tipo)
class AsyncSessionMock:
    pass
sqlalchemy_mock.ext = MagicMock()
sqlalchemy_mock.ext.asyncio = MagicMock()
sqlalchemy_mock.ext.asyncio.AsyncSession = AsyncSessionMock

# declarative_base
def declarative_base_mock():
    Base = MagicMock(name="declarative_base")
    Base.registry = MagicMock()
    return Base
sqlalchemy_mock.ext.declarative = MagicMock()
sqlalchemy_mock.ext.declarative.declarative_base = declarative_base_mock
sqlalchemy_mock.declarative_base = declarative_base_mock

# Instalar mock en sys.modules
sys.modules['sqlalchemy'] = sqlalchemy_mock
sys.modules['sqlalchemy.orm'] = sqlalchemy_orm_mock
sys.modules['sqlalchemy.ext'] = sqlalchemy_mock.ext
sys.modules['sqlalchemy.ext.asyncio'] = sqlalchemy_mock.ext.asyncio
sys.modules['sqlalchemy.ext.declarative'] = sqlalchemy_mock.ext.declarative

# ============================================================================
# Mock global de caldav (no instalado)
# ============================================================================

caldav_mock = MagicMock()
sys.modules['caldav'] = caldav_mock
sys.modules['caldav.objects'] = MagicMock()

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_env(monkeypatch):
    """Variables de entorno por defecto para tests."""
    env_defaults = {
        "GITHUB_TOKEN": "ghp_testtoken",
        "GITHUB_OWNER": "test-owner",
        "GITHUB_REPO": "test-repo",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "IMAP_SERVER": "imap.test.com",
        "IMAP_USER": "test@test.com",
        "IMAP_PASS": "testpass",
        "WHISPER_MODEL": "tiny",
        "CALDAV_URL": "https://caldav.test.com",
        "CALDAV_USER": "caldav_user",
        "CALDAV_PASS": "caldav_pass",
        "IMA_API_URL": "http://localhost:9000",
    }
    for k, v in env_defaults.items():
        monkeypatch.setenv(k, v)
