#!/usr/bin/env python3
"""Tests unitarios para app.py (FastAPI)"""
import pytest
from fastapi.testclient import TestClient

class TestApp:
    def test_health_endpoint(self, client):
        """GET /health debe retornar 200"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "ok"]
    
    def test_dashboard_page(self, client):
        """GET / debe servir dashboard"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Imanova" in response.text
    
    def test_orchestrator_status(self, client):
        """GET /orchestrator/status debe retornar estado"""
        response = client.get("/orchestrator/status")
        assert response.status_code == 200
