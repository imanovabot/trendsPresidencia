"""API Principal de trendsPresidencia - Solo Google Trends + Algoritmo de Alineación"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from services.google_trends import GoogleTrendsService

logger = logging.getLogger(__name__)

# Directorio base
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Inicializar servicio
google_trends = GoogleTrendsService()


# ============================================
# BACKGROUND TASK - AUTO REFRESH
# ============================================

async def scheduled_refresh():
    """Tarea en segundo plano que refresca datos automáticamente cada X minutos"""
    if not settings.auto_refresh_enabled:
        logger.info("Auto-refresh deshabilitado por configuración")
        return

    while True:
        try:
            interval = settings.auto_refresh_interval_minutes * 60
            await asyncio.sleep(interval)
            logger.info(f"⏰ Iniciando refresco automático (cada {settings.auto_refresh_interval_minutes} min)...")

            # Cargar datos
            data_file = DATA_DIR / "candidates.json"
            if not data_file.exists():
                logger.error("Archivo de candidatos no encontrado")
                continue

            with open(data_file) as f:
                data = json.load(f)

            candidates = data["candidates"]
            candidate_names = [c["name"] for c in candidates]
            results = {}

            # 1. Obtener datos de Google Trends para los 4 candidatos
            try:
                trends_scores = await google_trends.get_trends_for_candidates(candidate_names)
                for c in candidates:
                    c["sources"]["google_trends"] = trends_scores.get(c["name"], 0)
                results["google_trends"] = "ok"
            except Exception as e:
                logger.error(f"Error en refresh Google Trends: {e}")
                results["google_trends"] = str(e)

            # 2. Calcular momentum = Google Trends (sin pesos múltiples)
            for c in candidates:
                c["momentum"] = round(c["sources"].get("google_trends", 0), 1)

            # 3. Guardar actualización
            data["last_updated"] = datetime.now().isoformat()
            with open(data_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 4. Calcular pronóstico de segunda vuelta y guardarlo
            try:
                runoff_forecast = await google_trends.get_runoff_forecast()
                data["runoff_forecast"] = runoff_forecast
                results["runoff_forecast"] = "ok" if "error" not in runoff_forecast else f"error: {runoff_forecast.get('error')}"
            except Exception as e:
                logger.error(f"Error calculando pronóstico de segunda vuelta: {e}")
                results["runoff_forecast"] = f"error: {e}"

            logger.info(f"✅ Refresco automático completado: {results}")

        except Exception as e:
            logger.error(f"Error en refresco automático: {e}", exc_info=True)


class MomentumRequest(BaseModel):
    candidate_names: list[str] | None = None
    force_refresh: bool = False


class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: str
    services: dict[str, str]


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        description="API de Pronóstico Electoral - Solo Google Trends + Algoritmo de Alineación",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_model=dict[str, str])
    async def root() -> dict[str, str]:
        """Endpoint raíz"""
        return {
            "app": settings.project_name,
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health", response_model=HealthCheck)
    async def health_check() -> HealthCheck:
        """Verificar estado de la API"""
        services_status = {"google_trends": "ok"}

        # Verificar Google Trends
        try:
            await google_trends.get_trends_for_candidates(["test"])
        except Exception as e:
            logger.error(f"Google Trends no responde: {e}")
            services_status["google_trends"] = "error"

        return HealthCheck(
            status="healthy",
            version="2.0.0",
            timestamp=datetime.now().isoformat(),
            services=services_status,
        )

    @app.get("/api/v1/candidates", response_model=dict[str, Any])
    async def get_candidates(
        category: str | None = None,
        search: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        """
        Obtiene lista de candidatos con métricas de Google Trends.
        Solo incluye datos de Google Trends (sin YouTube, Sentimiento, etc.)
        """
        try:
            # Cargar datos base desde JSON
            data_file = DATA_DIR / "candidates.json"
            if not data_file.exists():
                raise HTTPException(status_code=404, detail="Archivo de candidatos no encontrado")

            with open(data_file) as f:
                data = json.load(f)

            candidates = data.get("candidates", [])

            # Si se solicita refresh, consultar Google Trends
            if refresh:
                logger.info("Refrescando datos desde Google Trends...")
                candidate_names = [c["name"] for c in candidates]

                try:
                    trends_scores = await google_trends.get_trends_for_candidates(candidate_names)
                    for c in candidates:
                        c["sources"]["google_trends"] = trends_scores.get(c["name"], 0)
                except Exception as e:
                    logger.error(f"Error refrescando Google Trends: {e}")

                # Calcular momentum = Google Trends directamente
                for c in candidates:
                    c["momentum"] = round(c["sources"].get("google_trends", 0), 1)

                # Guardar
                data["last_updated"] = datetime.now().isoformat()
                with open(data_file, "w") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            # Filtrar
            if category:
                candidates = [c for c in candidates if c["party"] == category]

            if search:
                query = search.lower().strip()
                candidates = [
                    c for c in candidates
                    if query in c["name"].lower()
                    or query in c["party"].lower()
                    or query in c["description"].lower()
                ]

            return {
                "candidates": candidates,
                "total": len(candidates),
                "last_updated": data.get("last_updated"),
                "update_frequency_hours": data.get("update_frequency_hours", 6),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en /candidates: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/candidates/{candidate_id}", response_model=dict[str, Any])
    async def get_candidate_detail(candidate_id: str) -> dict[str, Any]:
        """Obtiene detalle de un candidato específico"""
        try:
            data_file = DATA_DIR / "candidates.json"
            with open(data_file) as f:
                data = json.load(f)

            candidate = next((c for c in data["candidates"] if c["id"] == candidate_id), None)
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidato no encontrado")

            return candidate

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en /candidates/{candidate_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/candidates/refresh", response_model=dict[str, Any])
    async def refresh_candidates(background_tasks: BackgroundTasks) -> dict[str, Any]:
        """Fuerza actualización inmediata de datos desde Google Trends"""
        try:
            data_file = DATA_DIR / "candidates.json"
            with open(data_file) as f:
                data = json.load(f)

            candidates = data["candidates"]
            candidate_names = [c["name"] for c in candidates]

            # Obtener datos de Google Trends
            trends_scores = await google_trends.get_trends_for_candidates(candidate_names)
            for c in candidates:
                c["sources"]["google_trends"] = trends_scores.get(c["name"], 0)

            # Calcular momentum
            for c in candidates:
                c["momentum"] = round(c["sources"].get("google_trends", 0), 1)

            # Guardar
            data["last_updated"] = datetime.now().isoformat()
            with open(data_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Calcular pronóstico de segunda vuelta
            runoff_forecast = await google_trends.get_runoff_forecast()
            data["runoff_forecast"] = runoff_forecast

            with open(data_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return {
                "status": "ok",
                "refreshed": len(candidates),
                "timestamp": datetime.now().isoformat(),
                "runoff_forecast": runoff_forecast
            }

        except Exception as e:
            logger.error(f"Error en refresh: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/runoff/forecast", response_model=dict[str, Any])
    async def get_runoff_forecast() -> dict[str, Any]:
        """
        Obtiene el pronóstico de segunda vuelta más reciente.
        Usa el algoritmo de alineación calibrado con datos 2022.
        """
        try:
            # Intentar obtener del caché primero
            data_file = DATA_DIR / "candidates.json"
            if data_file.exists():
                with open(data_file) as f:
                    data = json.load(f)
                if "runoff_forecast" in data and "error" not in data["runoff_forecast"]:
                    return data["runoff_forecast"]

            # Si no hay caché, calcular en tiempo real
            forecast = await google_trends.get_runoff_forecast()
            return forecast

        except Exception as e:
            logger.error(f"Error obteniendo pronóstico de segunda vuelta: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/analysis/runoff", response_model=dict[str, Any])
    async def get_runoff_analysis() -> dict[str, Any]:
        """
        Calcula pronóstico de segunda vuelta en tiempo real.
        Incluye datos brutos, estabilidad y factores de ajuste.
        """
        try:
            forecast = await google_trends.get_runoff_forecast()
            if "error" in forecast:
                raise HTTPException(status_code=500, detail=forecast["error"])
            return forecast
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en análisis de segunda vuelta: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Iniciar tarea de refresco automático en segundo plano
    @app.on_event("startup")
    async def startup_event():
        background_tasks = asyncio.create_task(scheduled_refresh())
        logger.info("🚀 trendsPresidencia API iniciada - Solo Google Trends + Algoritmo de Alineación")

    return app
