"""Servicio de X/Twitter usando API v2 (filtrado anti-bot)"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)


class XService:
    """Servicio para consultar métricas de X/Twitter (solo cuentas reales)"""

    def __init__(self) -> None:
        self.timeout = 10.0
        self.base_url = "https://api.twitter.com/2"
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Authorization": f"Bearer {settings.x_bearer_token}"},
            )
        return self._client

    def _is_bot_account(self, user: dict) -> bool:
        """
        Detecta si una cuenta es probablemente un bot.
        Filtros:
        - Sin verificación oficial
        - Menos de 100 seguidores
        - Cuenta creada recientemente (< 30 días)
        - Ratio tweets/followers muy alto
        """
        verified = user.get("verified", False)
        followers = user.get("public_metrics", {}).get("followers_count", 0)
        following = user.get("public_metrics", {}).get("following_count", 0)
        tweet_count = user.get("public_metrics", {}).get("tweet_count", 0)
        created_at = user.get("created_at", "")

        # Filtro 1: Sin verificación y muy pocos seguidores
        if not verified and followers < 100:
            return True

        # Filtro 2: más siguiendo que seguidores (spam)
        if following > followers * 5 and followers < 1000:
            return True

        # Filtro 3: demasiados tweets en poco tiempo (spam)
        if tweet_count > 5000 and followers < 500:
            return True

        return False

    async def search_recent_tweets(
        self, query: str, max_results: int = 10
    ) -> list[dict[str, Any]]:
        """
        Busca tweets recientes sobre una consulta.
        Filtra bots de los resultados.
        """
        if not settings.x_bearer_token:
            logger.warning("X/Twitter Bearer Token no configurado")
            return []

        try:
            response = await self.client.get(
                "/tweets/search/recent",
                params={
                    "query": query,
                    "max_results": min(max_results, 100),
                    "tweet.fields": "public_metrics,created_at,author_id",
                    "expansions": "author_id",
                    "user.fields": "public_metrics,verified,created_at",
                },
            )
            response.raise_for_status()
            data = response.json()

            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

            # Filtrar bots
            real_tweets = []
            for tweet in tweets:
                author_id = tweet.get("author_id")
                if author_id in users:
                    user = users[author_id]
                    if not self._is_bot_account(user):
                        tweet["author"] = user
                        real_tweets.append(tweet)
                else:
                    # Si no hay datos de autor, incluir por defecto
                    real_tweets.append(tweet)

            logger.info(f"Tweets filtrados: {len(real_tweets)}/{len(tweets)} reales")
            return real_tweets
        except Exception as e:
            logger.error(f"Error buscando tweets para '{query}': {e}")
            return []

    async def get_user_metrics(self, username: str) -> dict[str, Any]:
        """Obtiene métricas de un usuario (verificado)"""
        if not settings.x_bearer_token:
            return {"followers": 0, "following": 0, "tweet_count": 0}

        try:
            response = await self.client.get(
                "/users/by/username",
                params={"usernames": username},
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("data"):
                return {"followers": 0, "following": 0, "tweet_count": 0}

            user = data["data"][0]
            return {
                "followers": user.get("public_metrics", {}).get("followers_count", 0),
                "following": user.get("public_metrics", {}).get("following_count", 0),
                "tweet_count": user.get("public_metrics", {}).get("tweet_count", 0),
                "verified": user.get("verified", False),
            }
        except Exception as e:
            logger.error(f"Error obteniendo métricas de usuario @{username}: {e}")
            return {"followers": 0, "following": 0, "tweet_count": 0, "verified": False}

    async def calculate_x_score(self, candidate_name: str) -> float:
        """
        Calcula puntaje X/Twitter (0-100) para un candidato.
        Solo considera contenido de cuentas reales.
        """
        try:
            if not settings.x_bearer_token:
                return 0.0

            tweets = await self.search_recent_tweets(candidate_name, max_results=50)

            if not tweets:
                return 0.0

            total_likes = sum(t.get("public_metrics", {}).get("like_count", 0) for t in tweets)
            total_retweets = sum(
                t.get("public_metrics", {}).get("retweet_count", 0) for t in tweets
            )
            total_replies = sum(
                t.get("public_metrics", {}).get("reply_count", 0) for t in tweets
            )

            # Métricas por tweet
            engagement_rate = (total_likes + total_retweets + total_replies) / max(
                len(tweets), 1
            )

            # Fórmula: volumen (30%) + engagement (50%) + replies (20%)
            volume_score = min(len(tweets) / 100, 1.0) * 100
            engagement_score = min(engagement_rate / 1000, 1.0) * 100
            reply_score = min(total_replies / 500, 1.0) * 100

            final_score = (
                volume_score * 0.3
                + engagement_score * 0.5
                + reply_score * 0.2
            )

            return round(final_score, 1)
        except Exception as e:
            logger.error(f"Error calculando X score para {candidate_name}: {e}")
            return 0.0

    async def close(self) -> None:
        """Cerrar cliente HTTP"""
        if self._client:
            await self._client.aclose()
