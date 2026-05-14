"""API Principal de trendsPresidencia"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from services.google_trends import GoogleTrendsService
from services.instagram_service import InstagramService
from services.news_service import NewsService
from services.sentiment_service import SentimentService
from services.tiktok_service import TikTokService
from services.x_service import XService
from services.youtube_service import YouTubeService

logger = logging.getLogger(__name__)

# Directorio base
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Inicializar servicios
google_trends = GoogleTrendsService()
instagram = InstagramService()
tiktok = TikTokService()
x_service = XService()
youtube = YouTubeService()
sentiment = SentimentService()
news = NewsService()


class MomentumRequest(BaseModel):
    candidate_names: list[str]
    force_refresh: bool = False


class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: str
    services: dict[str, str]


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        description="API de Momentum Digital para candidatos presidenciales Colombia 2026",
        version="0.1.0",
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
    async def root():
        """Endpoint raíz"""
        return {
            "app": settings.project_name,
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health", response_model=HealthCheck)
    async def health_check():
        """Verificar estado de la API y servicios"""
        services_status = {
            "google_trends": "ok",
            "youtube": "ok" if settings.youtube_api_key else "configure_youtube_api_key",
            "tiktok": "ok" if settings.tiktok_api_key else "configure_tiktok_api_key",
            "x": "ok" if settings.x_bearer_token else "configure_x_bearer_token",
            "instagram": "ok" if settings.instagram_access_token else "configure_instagram_token",
            "sentiment": "ok",
            "news": "ok",
        }

        # Verificar que servicios estén funcionando
        try:
            await google_trends.get_trends_for_candidates(["test"])
        except Exception as e:
            logger.error(f"Google Trends no responde: {e}")
            services_status["google_trends"] = "error"

        return HealthCheck(
            status="healthy",
            version="0.1.0",
            timestamp=datetime.now().isoformat(),
            services=services_status,
        )

    @app.get("/api/v1/candidates", response_model=dict[str, Any])
    async def get_candidates(
        category: str | None = None,
        search: str | None = None,
        refresh: bool = False,
    ):
        """
        Obtiene lista de candidatos con métricas actualizadas.

        - **category**: Filtrar por partido (ej: 'Partido Conservador')
        - **search**: Buscar por nombre, partido o descripción
        - **refresh**: Forzar actualización de datos desde APIs
        """
        try:
            # Cargar datos base desde JSON
            data_file = DATA_DIR / "candidates.json"
            if not data_file.exists():
                raise HTTPException(status_code=404, detail="Archivo de candidatos no encontrado")

            with open(data_file) as f:
                data = json.load(f)

            candidates = data.get("candidates", [])

            # Si se solicita refresh, consultar APIs reales
            if refresh:
                logger.info("Refrescando datos desde APIs...")
                candidate_names = [c["name"] for c in candidates]

                # 1. Google Trends
                try:
                    trends_scores = await google_trends.get_trends_for_candidates(candidate_names)
                    for c in candidates:
                        c["sources"]["google_trends"] = trends_scores.get(c["name"], c["sources"]["google_trends"])
                except Exception as e:
                    logger.error(f"Error refrescando Google Trends: {e}")

                # 2. YouTube
                try:
                    for c in candidates:
                        yt_score = await youtube.calculate_youtube_score(c["name"])
                        c["sources"]["youtube"] = yt_score
                except Exception as e:
                    logger.error(f"Error refrescando YouTube: {e}")

                # 3. TikTok (sin bots)
                try:
                    for c in candidates:
                        tk_score = await tiktok.calculate_tiktok_score(c["name"])
                        c["sources"]["tiktok"] = tk_score
                except Exception as e:
                    logger.error(f"Error refrescando TikTok: {e}")

                # 4. X/Twitter (sin bots)
                try:
                    for c in candidates:
                        x_score = await x_service.calculate_x_score(c["name"])
                        c["sources"]["x"] = x_score
                except Exception as e:
                    logger.error(f"Error refrescando X: {e}")

                # 5. Instagram (sin bots)
                try:
                    for c in candidates:
                        ig_score = await instagram.calculate_instagram_score(c["name"])
                        c["sources"]["instagram"] = ig_score
                except Exception as e:
                    logger.error(f"Error refrescando Instagram: {e}")

                # 6. Sentiment (ejecutar en batch)
                try:
                    texts = [c.get("description", "") for c in candidates]
                    sentiments = await sentiment.batch_analyze(texts)
                    for c, sent in zip(candidates, sentiments):
                        c["sources"]["sentiment"] = sent.get("positive", 0)  # Usar positivo como score principal
                        c["sentiment_breakdown"] = sent
                except Exception as e:
                    logger.error(f"Error refrescando sentimiento: {e}")

                # Recalcular momentum con pesos actualizados
                # Pesos: GT 30%, YT 20%, TK 15%, X 15%, IG 10%, Sent 10%
                for c in candidates:
                    c["momentum"] = round(
                        c["sources"]["google_trends"] * 0.30
                        + c["sources"]["youtube"] * 0.20
                        + c["sources"]["tiktok"] * 0.15
                        + c["sources"]["x"] * 0.15
                        + c["sources"]["instagram"] * 0.10
                        + c["sources"]["sentiment"] * 0.10,
                        1,
                    )

                # Guardar actualización
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
    async def get_candidate_detail(candidate_id: str):
        """Obtiene detalle de un candidato específico"""
        try:
            data_file = DATA_DIR / "candidates.json"
            with open(data_file) as f:
                data = json.load(f)

            candidate = next((c for c in data["candidates"] if c["id"] == candidate_id), None)
            if not candidate:
                raise HTTPException(status_code=404, detail="Candidato no encontrado")

            # Obtener noticias relacionadas
            try:
                related_news = await news.search_news(candidate["name"], max_results=5)
                candidate["recent_news"] = related_news
            except Exception as e:
                logger.error(f"Error obteniendo noticias: {e}")
                candidate["recent_news"] = []

            # Obtener videos de YouTube
            try:
                videos = await youtube.search_videos(candidate["name"], max_results=5)
                candidate["recent_videos"] = videos
            except Exception as e:
                logger.error(f"Error obteniendo videos: {e}")
                candidate["recent_videos"] = []

            return candidate

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en /candidates/{candidate_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/candidates/refresh", response_model=dict[str, Any])
    async def refresh_candidates(request: MomentumRequest | None = None):
        """
        Fuerza actualización de datos desde APIs externas.
        Actualiza todos los candidatos o solo los especificados.
        """
        try:
            data_file = DATA_DIR / "candidates.json"
            with open(data_file) as f:
                data = json.load(f)

            candidates = data["candidates"]
            names_to_refresh = [c["name"] for c in candidates]

            if request and request.candidate_names:
                names_to_refresh = request.candidate_names
                candidates = [c for c in candidates if c["name"] in names_to_refresh]

            results = {}

            # Google Trends
            try:
                trends_scores = await google_trends.get_trends_for_candidates(names_to_refresh)
                results["google_trends"] = trends_scores
                for c in candidates:
                    if c["name"] in trends_scores:
                        c["sources"]["google_trends"] = trends_scores[c["name"]]
            except Exception as e:
                logger.error(f"Error en refresh Google Trends: {e}")
                results["google_trends"] = {"error": str(e)}

            # YouTube
            try:
                yt_scores = {}
                for name in names_to_refresh:
                    score = await youtube.calculate_youtube_score(name)
                    yt_scores[name] = score
                    for c in candidates:
                        if c["name"] == name:
                            c["sources"]["youtube"] = score
                results["youtube"] = yt_scores
            except Exception as e:
                logger.error(f"Error en refresh YouTube: {e}")
                results["youtube"] = {"error": str(e)}

            # Sentiment
            try:
                texts = [c.get("description", "") for c in candidates]
                sentiments = await sentiment.batch_analyze(texts)
                sent_scores = {}
                for c, sent in zip(candidates, sentiments):
                    sent_scores[c["name"]] = sent
                    c["sources"]["sentiment"] = sent.get("positive", 0)
                    c["sentiment_breakdown"] = sent
                results["sentiment"] = sent_scores
            except Exception as e:
                logger.error(f"Error en refresh sentiment: {e}")
                results["sentiment"] = {"error": str(e)}

            # Recalcular momentum
            for c in candidates:
                c["momentum"] = round(
                    c["sources"]["google_trends"] * 0.4
                    + c["sources"]["youtube"] * 0.3
                    + c["sources"]["sentiment"] * 0.3,
                    1,
                )

            data["last_updated"] = datetime.now().isoformat()
            with open(data_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return {
                "refreshed": len(candidates),
                "candidates": [c["name"] for c in candidates],
                "results": results,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error en refresh: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/news", response_model=dict[str, Any])
    async def get_news(
        search: str | None = None,
        max_results: int = 20,
        candidate: str | None = None,
    ):
        """
        Obtiene noticias recientes.

        - **search**: Buscar por término
        - **candidate**: Filtrar por nombre de candidato
        - **max_results**: Máximo de resultados (default 20)
        """
        try:
            if candidate:
                news_list = (await news.get_news_for_candidates([candidate])).get(candidate, [])
            elif search:
                news_list = await news.search_news(search, max_results=max_results)
            else:
                news_list = await news.fetch_news(max_entries=max_results)

            return {
                "news": news_list,
                "total": len(news_list),
                "sources": len(set(n["source"] for n in news_list)),
            }

        except Exception as e:
            logger.error(f"Error en /news: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/stats", response_model=dict[str, Any])
    async def get_stats():
        """Estadísticas generales del sistema"""
        try:
            data_file = DATA_DIR / "candidates.json"
            with open(data_file) as f:
                data = json.load(f)

            candidates = data["candidates"]

            # Calcular estadísticas
            momentum_values = [c["momentum"] for c in candidates]
            changes = [c["change_24h"] for c in candidates]

            stats = {
                "total_candidates": len(candidates),
                "parties": list(set(c["party"] for c in candidates)),
                "avg_momentum": round(sum(momentum_values) / len(momentum_values), 1) if momentum_values else 0,
                "max_momentum": max(momentum_values) if momentum_values else 0,
                "min_momentum": min(momentum_values) if momentum_values else 0,
                "avg_change_24h": round(sum(changes) / len(changes), 1) if changes else 0,
                "candidates_up": sum(1 for c in changes if c > 0),
                "candidates_down": sum(1 for c in changes if c < 0),
                "last_updated": data.get("last_updated"),
                "update_frequency_hours": data.get("update_frequency_hours", 6),
            }

            return stats

        except Exception as e:
            logger.error(f"Error en /stats: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.on_event("startup")
    async def startup_event():
        """Inicializar servicios"""
        logger.info("Iniciando trendsPresidencia API...")
        logger.info(f"Configuración: {settings.model_dump()}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cerrar recursos"""
        await google_trends.close()
        await youtube.close()
        await sentiment.close()

    return app


# Para ejecución directa: uvicorn main:app --reload
app = create_app()
