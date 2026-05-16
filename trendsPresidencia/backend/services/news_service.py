"""Servicio de noticias RSS"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import feedparser

from config.settings import settings

logger = logging.getLogger(__name__)

# Fuentes RSS de noticias colombianas
NEWS_SOURCES = [
    "https://www.eltiempo.com/rss",
    "https://www.elespectador.com/rss",
    "https://www.semana.com/rss",
    "https://www.rcnradio.com/rss",
    "https://www.bluradio.com/rss",
    "https://www.noticiasrcn.com/rss",
]


class NewsService:
    """Servicio para parsear noticias de RSS feeds"""

    def __init__(self) -> None:
        self.cache: dict[str, dict[str, Any]] = {}
        self.cache_ttl = timedelta(minutes=settings.news_update_interval_minutes)

    def _clean_text(self, text: str) -> str:
        """Limpia HTML y espacios"""
        if not text:
            return ""
        # Eliminar HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Eliminar espacios múltiples
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _hash_entry(self, title: str, link: str) -> str:
        """Genera hash único para entrada de noticia"""
        content = f"{title}:{link}"
        return hashlib.md5(content.encode()).hexdigest()

    def _is_recent(self, published: datetime) -> bool:
        """Verifica si la noticia es de las últimas 24h"""
        cutoff = datetime.now(published.tzinfo) - timedelta(hours=24)
        return published >= cutoff

    async def fetch_news(self, max_entries: int = 50) -> list[dict[str, Any]]:
        """
        Obtiene noticias de todas las fuentes RSS configuradas.

        Returns:
            Lista de noticias con: {title, link, summary, source, published_at}
        """
        all_entries = []
        seen_hashes = set()

        for source_url in NEWS_SOURCES:
            try:
                feed = feedparser.parse(source_url)
                feed_title = feed.feed.get("title", "Desconocido")

                for entry in feed.entries[:10]:  # Top 10 por fuente
                    # Extraer campos
                    title = self._clean_text(entry.get("title", ""))
                    link = entry.get("link", "")

                    # Fecha de publicación
                    published_str = entry.get("published", entry.get("updated", ""))
                    try:
                        published = datetime(*entry.published_parsed[:6]) if entry.get("published_parsed") else datetime.now()
                    except:
                        published = datetime.now()

                    # Resumen
                    summary = self._clean_text(
                        entry.get("summary", entry.get("description", ""))
                    )[:500]

                    # Evitar duplicados
                    entry_hash = self._hash_entry(title, link)
                    if entry_hash in seen_hashes:
                        continue
                    seen_hashes.add(entry_hash)

                    # Solo noticias recientes
                    if self._is_recent(published):
                        all_entries.append({
                            "title": title,
                            "link": link,
                            "summary": summary,
                            "source": feed_title,
                            "published_at": published.isoformat(),
                            "hash": entry_hash,
                        })

            except Exception as e:
                logger.error(f"Error fetching RSS de {source_url}: {e}")
                continue

        # Ordenar por fecha (más reciente primero)
        all_entries.sort(key=lambda x: x["published_at"], reverse=True)

        logger.info(f"Noticias obtenidas: {len(all_entries)} de {len(NEWS_SOURCES)} fuentes")
        return all_entries[:max_entries]

    async def search_news(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Busca noticias que contengan un término específico"""
        all_news = await self.fetch_news()
        query_lower = query.lower()

        filtered = [
            n for n in all_news
            if query_lower in n["title"].lower() or query_lower in n["summary"].lower()
        ]

        logger.info(f"Noticias encontradas para '{query}': {len(filtered)}")
        return filtered[:max_results]

    async def get_news_for_candidates(self, candidate_names: list[str]) -> dict[str, list[dict]]:
        """Obtiene noticias relevantes para cada candidato"""
        all_news = await self.fetch_news(max_entries=100)
        result = {name: [] for name in candidate_names}

        for news in all_news:
            title_lower = news["title"].lower()
            summary_lower = news["summary"].lower()

            for name in candidate_names:
                if name.lower() in title_lower or name.lower() in summary_lower:
                    if len(result[name]) < 5:  # Máximo 5 noticias por candidato
                        result[name].append(news)

        return result

    def clear_cache(self) -> None:
        """Limpia la cache de noticias"""
        self.cache.clear()
        logger.info("Cache de noticias limpiada")
