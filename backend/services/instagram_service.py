"""Servicio de Instagram usando Basic Display API / Graph API"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)


class InstagramService:
    """Servicio para consultar métricas de Instagram (filtrado anti-bot)"""

    def __init__(self) -> None:
        self.timeout = 10.0
        self.base_url = "https://graph.instagram.com"
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    def _is_bot_account(self, user: dict) -> bool:
        """
        Detecta si una cuenta de Instagram es probablemente un bot.
        Filtros similares a X/TikTok.
        """
        followers = user.get("followers_count", 0)
        following = user.get("follows_count", 0)
        media_count = user.get("media_count", 0)
        username = user.get("username", "").lower()

        # Filtro 1: pocos seguidores
        if followers < 50:
            return True

        # Filtro 2: ratio following/followers muy alto
        if following > followers * 10 and followers < 1000:
            return True

        # Filtro 3: demasiados posts con pocos seguidores
        if media_count > 1000 and followers < 100:
            return True

        # Filtro 4: nombre genérico de bot
        bot_keywords = ["bot", "follow", "like", "auto", "igram", "insta"]
        if any(kw in username for kw in bot_keywords):
            return True

        return False

    async def get_user_metrics(self, username: str) -> dict[str, Any]:
        """
        Obtiene métricas básicas de un usuario de Instagram.
        Requiere Access Token configurado.
        """
        if not settings.instagram_access_token:
            logger.warning("Instagram Access Token no configurado")
            return {"followers": 0, "following": 0, "posts": 0, "is_bot": False}

        try:
            # Obtener ID del usuario
            user_resp = await self.client.get(
                f"/v18.0/me",
                params={"fields": "id,username,account_type,media_count"},
            )
            user_resp.raise_for_status()
            user_data = user_resp.json()

            # Obtener seguidores
            followers_resp = await self.client.get(
                f"/v18.0/{user_data['id']}",
                params={"fields": "followers_count,follows_count"},
            )
            followers_resp.raise_for_status()
            followers_data = followers_resp.json()

            metrics = {
                "id": user_data.get("id"),
                "username": user_data.get("username"),
                "followers": followers_data.get("followers_count", 0),
                "following": followers_data.get("follows_count", 0),
                "posts": user_data.get("media_count", 0),
            }

            # Detectar bot
            is_bot = self._is_bot_account(metrics)
            metrics["is_bot"] = is_bot

            return metrics
        except Exception as e:
            logger.error(f"Error obteniendo métricas de Instagram @{username}: {e}")
            return {"followers": 0, "following": 0, "posts": 0, "is_bot": False}

    async def search_hashtag(self, hashtag: str, count: int = 10) -> list[dict]:
        """
        Busca posts recientes de un hashtag.
        Filtra bots automáticamente.
        """
        if not settings.instagram_access_token:
            logger.warning("Instagram Access Token no configurado")
            return []

        try:
            # Buscar hashtag ID
            hashtag_resp = await self.client.get(
                "/v18.0/ig_hashtag_search",
                params={"user_id": "me", "q": hashtag},
            )
            hashtag_resp.raise_for_status()
            hashtag_data = hashtag_resp.json()

            if not hashtag_data.get("data"):
                return []

            hashtag_id = hashtag_data["data"][0]["id"]

            # Obtener posts recientes
            media_resp = await self.client.get(
                f"/v18.0/{hashtag_id}/recent_media",
                params={"user_id": "me", "fields": "id,caption,media_type,like_count,comments_count,timestamp,username"},
                timeout=self.timeout,
            )
            media_resp.raise_for_status()
            media_data = media_resp.json()

            posts = media_data.get("data", [])

            # Filtrar bots por autor
            real_posts = []
            seen_authors = set()
            for post in posts:
                username = post.get("username", "")
                # Obtener métricas del autor si no lo tenemos
                if username and username not in seen_authors:
                    author_metrics = await self.get_user_metrics(username)
                    seen_authors.add(username)
                    if not author_metrics.get("is_bot", True):
                        real_posts.append(post)
                elif username in seen_authors:
                    # Ya lo evaluamos, incluir si era real
                    real_posts.append(post)

            return real_posts[:count]
        except Exception as e:
            logger.error(f"Error buscando hashtag #{hashtag}: {e}")
            return []

    async def calculate_instagram_score(self, candidate_name: str) -> float:
        """
        Calcula puntaje Instagram (0-100) para un candidato.
        Solo considera cuentas/posts reales.
        """
        try:
            if not settings.instagram_access_token:
                return 0.0

            # Buscar por hashtag del nombre del candidato
            hashtag = candidate_name.replace(" ", "").lower()
            posts = await self.search_hashtag(hashtag, count=20)

            if not posts:
                return 0.0

            # Calcular engagement promedio
            total_likes = sum(p.get("like_count", 0) for p in posts)
            total_comments = sum(p.get("comments_count", 0) for p in posts)
            avg_engagement = (total_likes + total_comments) / len(posts)

            # Puntaje: volumen de posts (30%) + engagement (70%)
            volume_score = min(len(posts) / 20, 1.0) * 100
            engagement_score = min(avg_engagement / 5000, 1.0) * 100

            final_score = volume_score * 0.3 + engagement_score * 0.7

            return round(final_score, 1)
        except Exception as e:
            logger.error(f"Error calculando Instagram score para {candidate_name}: {e}")
            return 0.0

    async def close(self) -> None:
        """Cerrar cliente HTTP"""
        if self._client:
            await self._client.aclose()
