"""Tests E2E del frontend con Playwright"""
from __future__ import annotations

import re
import pytest

from playwright.sync_api import Page, expect


@pytest.fixture(scope="module")
def frontend_url() -> str:
    """URL del frontend desplegado"""
    return "http://187.77.14.245:8081"


class TestFrontend:
    """Tests de la interfaz web"""

    def test_page_loads(self, page: Page, frontend_url: str) -> None:
        """Verifica que la página cargue correctamente"""
        page.goto(frontend_url, timeout=10000)
        expect(page).to_have_title(re.compile(r"trendsPresidencia", re.I), timeout=5000)

    def test_candidates_visible(self, page: Page, frontend_url: str) -> None:
        """Verifica que los candidatos se muestren en la lista"""
        page.goto(frontend_url, timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        # Esperar a que aparezcan las tarjetas (carga dinámica)
        page.wait_for_selector(".candidate-card", timeout=10000)
        cards = page.query_selector_all(".candidate-card")
        assert len(cards) >= 4, f"Se esperaban al menos 4 tarjetas, se encontraron {len(cards)}"

    def test_search_works(self, page: Page, frontend_url: str) -> None:
        """Verifica que la búsqueda filtre candidatos"""
        page.goto(frontend_url, timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        search_input = page.query_selector("#searchInput")
        assert search_input is not None, "No se encontró el input de búsqueda"
        search_input.fill("Abelardo")
        page.wait_for_timeout(1000)
        # Esperar a que se actualice la lista
        page.wait_for_selector(".candidate-card", timeout=5000)
        cards = page.query_selector_all(".candidate-card")
        assert len(cards) >= 1, "La búsqueda no devolvió resultados"
        first_card = cards[0]
        name = first_card.query_selector(".candidate-name")
        assert name is not None, "No se encontró el nombre en la tarjeta"
        assert "Abelardo" in name.inner_text(), f"Nombre incorrecto: {name.inner_text()}"

    def test_category_filter(self, page: Page, frontend_url: str) -> None:
        """Verifica que el filtro de categoría funcione"""
        page.goto(frontend_url, timeout=10000)
        category_select = page.query_selector("#categoryFilter")
        assert category_select is not None
        options = category_select.query_selector_all("option")
        assert len(options) > 1, "El filtro de categoría no tiene opciones"
        category_select.select_option("Partido Conservador")
        page.wait_for_timeout(500)
        cards = page.query_selector_all(".candidate-card")
        for card in cards:
            party = card.query_selector(".candidate-party")
            if party:
                assert "Conservador" in party.inner_text(),                     f"Candidato no pertenece al partido filtrado: {party.inner_text()}"

    def test_modal_opens(self, page: Page, frontend_url: str) -> None:
        """Verifica que el modal de metodología se abra"""
        page.goto(frontend_url, timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        methodology_link = page.query_selector("#methodologyLink")
        assert methodology_link is not None, "No se encontró el enlace de metodología"
        methodology_link.click()
        modal = page.locator("#methodologyModal")
        assert modal is not None, "No se encontró el modal"
        expect(modal).to_be_visible(timeout=5000)

    def test_modal_closes(self, page: Page, frontend_url: str) -> None:
        """Verifica que el modal se cierre al hacer clic en el botón"""
        page.goto(frontend_url, timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        methodology_link = page.query_selector("#methodologyLink")
        methodology_link.click()
        page.wait_for_selector("#methodologyModal", state="visible", timeout=5000)
        # Cerrar con clic en el botón
        close_btn = page.query_selector("#closeModal")
        assert close_btn is not None, "No se encontró el botón de cerrar"
        close_btn.click()
        expect(page.locator("#methodologyModal")).to_be_hidden(timeout=3000)

    def test_candidate_detail(self, page: Page, frontend_url: str) -> None:
        """Verifica que el panel de detalle se muestre al seleccionar un candidato"""
        page.goto(frontend_url, timeout=10000)
        page.wait_for_load_state("networkidle", timeout=10000)
        # Esperar a que se carguen las tarjetas
        page.wait_for_selector(".candidate-card", timeout=10000)
        first_card = page.query_selector(".candidate-card")
        assert first_card is not None, "No se encontró ninguna tarjeta de candidato"
        # Hacer clic y esperar que aparezca el detalle
        first_card.click()
        detail_panel = page.locator("#detailPanel")
        assert detail_panel is not None, "No se encontró el panel de detalle"
        expect(detail_panel).to_be_visible(timeout=5000)
        name = detail_panel.locator("h2")
        assert name is not None, "No se encontró el título en el detalle"
        assert len(name.inner_text()) > 0, "El nombre del candidato está vacío"
