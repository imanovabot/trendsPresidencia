"""Tests E2E del backend API"""
from __future__ import annotations

import json

import pytest
import requests

BASE_URL = "http://187.77.14.245:8001"


@pytest.fixture(scope="module")
def api_data() -> dict:
    """Cargar datos de la API una sola vez"""
    resp = requests.get(f"{BASE_URL}/api/v1/candidates", timeout=10)
    assert resp.status_code == 200, f"API devolvió {resp.status_code}"
    return resp.json()


class TestHealth:
    """Tests del endpoint de salud"""

    def test_health_status(self) -> None:
        """Verifica que el health check responda correctamente"""
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "services" in data
        assert "timestamp" in data

    def test_health_services(self) -> None:
        """Verifica que todos los servicios estén reportados"""
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        data = resp.json()
        services = data["services"]
        assert "google_trends" in services
        assert "youtube" in services
        assert "sentiment" in services
        assert "news" in services


class TestCandidates:
    """Tests del endpoint de candidatos"""

    def test_candidates_returns_list(self, api_data: dict) -> None:
        """Verifica que la respuesta tenga una lista de candidatos"""
        assert "candidates" in api_data
        candidates = api_data["candidates"]
        assert isinstance(candidates, list)
        assert len(candidates) > 0

    def test_candidate_structure(self, api_data: dict) -> None:
        """Verifica la estructura de cada candidato"""
        required_fields = {"id", "name", "party", "momentum", "sources", "sentiment_breakdown"}
        for candidate in api_data["candidates"]:
            assert required_fields.issubset(candidate.keys()),                 f"Candidato {candidate.get('name', 'unknown')} falta campos"

    def test_candidate_sources_structure(self, api_data: dict) -> None:
        """Verifica que cada candidato tenga las fuentes"""
        required_sources = {"google_trends", "youtube", "sentiment"}
        for candidate in api_data["candidates"]:
            sources = candidate.get("sources", {})
            assert required_sources.issubset(sources.keys()),                 f"Candidato {candidate['name']} no tiene todas las fuentes"

    def test_momentum_values(self, api_data: dict) -> None:
        """Verifica que los valores de momentum sean números positivos"""
        for candidate in api_data["candidates"]:
            momentum = candidate.get("momentum", 0)
            assert isinstance(momentum, (int, float)),                 f"Momentum de {candidate['name']} no es número"
            assert 0 <= momentum <= 100,                 f"Momentum de {candidate['name']} fuera de rango: {momentum}"

    def test_candidate_count(self, api_data: dict) -> None:
        """Verifica que haya exactamente 4 candidatos"""
        assert len(api_data["candidates"]) == 4,             f"Se esperaban 4 candidatos, se encontraron {len(api_data['candidates'])}"

    def test_candidate_names(self, api_data: dict) -> None:
        """Verifica que estén los 4 candidatos esperados"""
        expected = {"abelardo", "ivan-cepeda", "paloma-valencia", "sergio-fajardo"}
        actual = {c["id"] for c in api_data["candidates"]}
        assert expected.issubset(actual),             f"Faltan candidatos. Esperados: {expected}, Encontrados: {actual}"


class TestCandidateDetail:
    """Tests del endpoint de detalle de candidato"""

    def test_get_abelardo(self) -> None:
        """Obtiene detalle de Abelardo de la Espriella"""
        resp = requests.get(f"{BASE_URL}/api/v1/candidates/abelardo", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Abelardo de la Espriella"
        assert "sources" in data
        assert "sentiment_breakdown" in data

    def test_get_ivan_cepeda(self) -> None:
        """Obtiene detalle de Iván Cepeda"""
        resp = requests.get(f"{BASE_URL}/api/v1/candidates/ivan-cepeda", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Iván Cepeda"

    def test_get_paloma_valencia(self) -> None:
        """Obtiene detalle de Paloma Valencia"""
        resp = requests.get(f"{BASE_URL}/api/v1/candidates/paloma-valencia", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Paloma Valencia"

    def test_get_sergio_fajardo(self) -> None:
        """Obtiene detalle de Sergio Fajardo"""
        resp = requests.get(f"{BASE_URL}/api/v1/candidates/sergio-fajardo", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Sergio Fajardo"

    def test_candidate_not_found(self) -> None:
        """Verifica que devuelva 404 para candidato inexistente"""
        resp = requests.get(f"{BASE_URL}/api/v1/candidates/no existe", timeout=5)
        assert resp.status_code == 404


class TestStats:
    """Tests del endpoint de estadísticas"""

    def test_stats_endpoint(self) -> None:
        """Verifica que el endpoint de estadísticas funcione"""
        resp = requests.get(f"{BASE_URL}/api/v1/stats", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_candidates" in data
        assert "avg_momentum" in data
        assert "max_momentum" in data
