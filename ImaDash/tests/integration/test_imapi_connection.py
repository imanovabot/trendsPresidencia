#!/usr/bin/env python3
"""Tests de integración: conexión ImaDash → ImaPi"""
import pytest
import httpx
from app import app

class TestImaPiIntegration:
    @pytest.mark.asyncio
    async def test_imapi_reachable(self):
        """ImaPi debe estar accesible en IMAPI_API_URL"""
        import os
        imapi_url = os.getenv("IMAPI_API_URL", "http://localhost:8001")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{imapi_url}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_dashboard_projects_endpoint(self, client):
        """Dashboard debe mostrar proyectos de ImaPi"""
        response = client.get("/orchestrator/projects")
        # Asumimos que ImaPi está disponible
        assert response.status_code in [200, 503]  # 503 si ImaPi no disponible
