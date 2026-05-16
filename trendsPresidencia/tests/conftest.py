"""Configuración de tests
- Playwright para tests E2E (marcados con @pytest.mark.e2e)
- Fixtures básicos para tests unitarios sin Playwright
"""
from __future__ import annotations

import pytest

# Importaciones condicionales de Playwright
try:
    from playwright.sync_api import Browser, Page, expect
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# ============================================
# FIXTURES PARA TESTS UNITARIOS (sin Playwright)
# ============================================

@pytest.fixture(scope="session")
def event_loop():
    """Event loop para tests asíncronos"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================
# FIXTURES PARA TESTS E2E (requieren Playwright)
# ============================================

if PLAYWRIGHT_AVAILABLE:
    @pytest.fixture(scope="session")
    def browser() -> Browser:
        """Navegador compartido para toda la sesión"""
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            yield browser
            browser.close()

    @pytest.fixture
    def page(browser: Browser) -> Page:
        """Nueva página para cada test"""
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="es-CO"
        )
        page = context.new_page()
        yield page
        context.close()
else:
    # Stubs para cuando Playwright no está disponible
    @pytest.fixture(scope="session")
    def browser():
        pytest.skip("Playwright no instalado")

    @pytest.fixture
    def page(browser):
        pytest.skip("Playwright no instalado")
