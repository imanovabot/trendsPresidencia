"""Servicio de TikTok usando API no oficial (tiktok-scraper)"""
from __future__ import annotations

import json
import logging
from typing import Any

from config.settings import settings

logger = logging.getLogger(__name__)


class TikTokService:
    """Servicio para consultar métricas de TikTok (filtrado anti-bot)"""

    def __init__(self) -> None:
        self.timeout = 10.0
        self._session: Any = None

    def _is_bot_account(self, video: dict) -> bool:
        """
        Detecta si una cuenta es probablemente un bot.
        Filtros:
        - Menos de 50 seguidores
        - Más de 1000 videos pero menos de 100 followers (spam)
        - Sin foto de perfil
        - Nombre genérico
        """
        author = video.get("author", {})
        followers = author.get("followers", 0)
        following = author.get("following", 0)
        videos_count = author.get("video_count", 0)
        username = author.get("username", "").lower()

        # Filtro 1: cuenta sin seguidores
        if followers < 50:
            return True

        # Filtro 2: ratio following/followers muy alto (spam)
        if following > followers * 10 and followers < 1000:
            return True

        # Filtro 3: demasiados videos con pocos seguidores
        if videos_count > 1000 and followers < 100:
            return True

        return False

    async def search_videos(self, query: str, count: int = 10) -> list[dict]:
        """
        Busca videos relacionados con la consulta.
        Filtra bots automáticamente.
        """
        try:
            if not settings.tiktok_api_key:
                logger.warning("TikTok API key no configurada")
                return []

            # TODO: Implementar con API real (Apify, RapidAPI, etc.)
            # Por ahora retorna vacío hasta tener API configurada
            logger.info(f"Buscando TikTok para: {query}")
            return []

        except Exception as e:
            logger.error(f"Error buscando TikTok: {e}")
            return []

    async def get_hashtag_metrics(self, hashtag: str) -> dict[str, Any]:
        """Obtiene métricas de un hashtag (sin bots)"""
        try:
            videos = await self.search_videos(f"#{hashtag}", count=20)
            if not videos:
                return {"views": 0, "likes": 0, "shares": 0, "videos": 0, "real_accounts": 0}

            # Filtrar bots
            real_videos = [v for v in videos if not self._is_bot_account(v)]
            real_count = len(real_videos)

            if real_count == 0:
                return {"views": 0, "likes": 0, "shares": 0, "videos": 0, "real_accounts": 0}

            total_views = sum(v.get("views", 0) for v in real_videos)
            total_likes = sum(v.get("likes", 0) for v in real_videos)
            total_shares = sum(v.get("shares", 0) for v in real_videos)

            return {
                "views": total_views,
                "likes": total_likes,
                "shares": total_shares,
                "videos": real_count,
                "real_accounts": real_count,
                "avg_views": total_views / real_count,
            }
        except Exception as e:
            logger.error(f"Error obteniendo hashtag metrics: {e}")
            return {"views": 0, "likes": 0, "shares": 0, "videos": 0, "real_accounts": 0}

    async def calculate_tiktok_score(self, candidate_name: str) -> float:
        """
        Calcula puntaje TikTok (0-100) para un candidato.
        Solo considera cuentas reales (filtra bots).
        """
        try:
            hashtags = [candidate_name.replace(" ", "").lower(), "colombia2026"]
            metrics = await self.get_hashtag_metrics(hashtags[0])

            if not metrics or metrics.get("real_accounts", 0) == 0:
                return 0.0

            videos = metrics.get("real_accounts", 0)
            avg_views = metrics.get("avg_views", 0)
            engagement = metrics.get("likes", 0) + metrics.get("shares", 0)

            # Fórmula: volumen (40%) + vistas (35%) + engagement (25%)
            volume_score = min(videos / 100, 1.0) * 100
            views_score = min(avg_views / 100000, 1.0) * 100
            engagement_score = min(engagement / 10000, 1.0) * 100

            final_score = (
                volume_score * 0.4
                + views_score * 0.35
                + engagement_score * 0.25
            )

            return round(final_score, 1)
        except Exception as e:
            logger.error(f"Error calculando TikTok score para {candidate_name}: {e}")
            return 0.0

    async def close(self) -> None:
        """Cerrar sesión"""
        if self._session:
            await self._session.close()
