"""
Fixtures para tests de integración — requieren servicios reales corriendo.
"""

import pytest

pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.integration
@pytest.fixture
def imapi_url():
    return "http://localhost:8000"


@pytest.mark.integration
@pytest.fixture
def websocket_url():
    return "ws://localhost:8000/ws"
