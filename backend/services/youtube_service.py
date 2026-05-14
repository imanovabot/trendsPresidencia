"""Servicio de YouTube Data API v3"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeService:
    """Servicio para consultar YouTube Data API v3"""

    def __init__(self) -> None:
        self.api_key = settings.youtube_api_key
        self.client = httpx.AsyncClient(timeout=15.0)
        self.cache: dict[str, dict[str, Any]] = {}

    async def search_videos(self, candidate_name: str, max_results: int = 10) -> list[dict]:
        """Busca videos relacionados con el candidato"""
        if not self.api_key:
            logger.warning("YouTube API key no configurada")
            return []

        cache_key = f"search:{candidate_name}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached["ts"] < timedelta(hours=6):
                return cached["data"]

        try:
            params = {
                "part": "snippet",
                "q": candidate_name,
                "type": "video",
                "order": "relevance",
                "maxResults": max_results,
                "key": self.api_key,
                "publishedAfter": (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",
            }

            resp = await self.client.get(f"{YOUTUBE_API_BASE}/search", params=params)
            resp.raise_for_status()
            data = resp.json()

            videos = []
            for item in data.get("items", []):
                video = {
                    "id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "channel": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                    "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                }
                videos.append(video)

            self.cache[cache_key] = {"ts": datetime.now(), "data": videos}
            return videos

        except Exception as e:
            logger.error(f"Error buscando videos de {candidate_name}: {e}")
            return []

    async def get_video_statistics(self, video_ids: list[str]) -> dict[str, dict]:
        """Obtiene estadísticas de videos (vistas, likes, comentarios)"""
        if not self.api_key or not video_ids:
            return {}

        try:
            params = {
                "part": "statistics,snippet",
                "id": ",".join(video_ids[:50]),  # Límite de 50 IDs por request
                "key": self.api_key,
            }

            resp = await self.client.get(f"{YOUTUBE_API_BASE}/videos", params=params)
            resp.raise_for_status()
            data = resp.json()

            stats = {}
            for item in data.get("items", []):
                vid_id = item["id"]
                stats[vid_id] = {
                    "views": int(item["statistics"].get("viewCount", 0)),
                    "likes": int(item["statistics"].get("likeCount", 0)),
                    "comments": int(item["statistics"].get("commentCount", 0)),
                    "title": item["snippet"]["title"],
                }
            return stats

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de videos: {e}")
            return {}

    async def get_channel_statistics(self, candidate_name: str) -> dict[str, Any]:
        """Busca el canal principal del candidato y obtiene sus estadísticas"""
        if not self.api_key:
            return {}

        try:
            # Buscar canal
            params = {
                "part": "snippet,statistics",
                "q": candidate_name,
                "type": "channel",
                "maxResults": 1,
                "key": self.api_key,
            }

            resp = await self.client.get(f"{YOUTUBE_API_BASE}/search", params=params)
            resp.raise_for_status()
            search_data = resp.json()

            if not search_data.get("items"):
                return {}

            channel_id = search_data["items"][0]["id"]["channelId"]

            # Obtener estadísticas del canal
            params = {
                "part": "statistics",
                "id": channel_id,
                "key": self.api_key,
            }
            resp = await self.client.get(f"{YOUTUBE_API_BASE}/channels", params=params)
            resp.raise_for_status()
            channel_data = resp.json()

            if not channel_data.get("items"):
                return {}

            stats = channel_data["items"][0]["statistics"]
            return {
                "channel_id": channel_id,
                "title": search_data["items"][0]["snippet"]["title"],
                "subscribers": int(stats.get("subscriberCount", 0)),
                "total_videos": int(stats.get("videoCount", 0)),
                "total_views": int(stats.get("viewCount", 0)),
            }

        except Exception as e:
            logger.error(f"Error obteniendo canal de {candidate_name}: {e}")
            return {}

    async def calculate_youtube_score(self, candidate_name: str) -> float:
        """
        Calcula un puntaje 0-100 basado en métricas de YouTube.
        Considera: número de videos, vistas promedio, engagement.
        """
        videos = await self.search_videos(candidate_name, max_results=10)
        if not videos:
            return 0.0

        # Obtener estadísticas de los videos
        video_ids = [v["id"] for v in videos]
        stats = await self.get_video_statistics(video_ids)

        if not stats:
            return 0.0

        # Calcular métricas agregadas
        total_views = sum(s["views"] for s in stats.values())
        total_likes = sum(s["likes"] for s in stats.values())
        total_comments = sum(s["comments"] for s in stats.values())
        video_count = len(stats)

        if video_count == 0:
            return 0.0

        # Normalizar a escala 0-100
        # Vistas totales (máximo ~100M para 10 videos)
        view_score = min((total_views / 100_000_000) * 50, 50)
        # Engagement rate (likes+comments / vistas)
        engagement = (total_likes + total_comments) / total_views if total_views > 0 else 0
        engagement_score = min(engagement * 1000, 30)  # 3% engagement = 30 puntos
        # Cantidad de videos (más videos = más presencia)
        video_score = min(video_count * 2, 20)  # 10 videos = 20 puntos

        final_score = round(view_score + engagement_score + video_score, 1)
        logger.info(f"YouTube score para {candidate_name}: {final_score:.1f}")
        return final_score

    async def close(self) -> None:
        """Cerrar cliente HTTP"""
        await self.client.aclose()
