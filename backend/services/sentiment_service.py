"""Servicio de análisis de sentimiento usando HuggingFace Inference API"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

# Modelo por defecto (cardiffnlp/twitter-roberta-base-sentiment)
DEFAULT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# Labels del modelo
LABELS = ["negative", "neutral", "positive"]


class SentimentService:
    """Servicio para análisis de sentimiento"""

    def __init__(self) -> None:
        self.api_key = settings.huggingface_api_key
        self.model = DEFAULT_MODEL
        self.client = httpx.AsyncClient(timeout=15.0)
        self.cache: dict[str, dict[str, Any]] = {}

    async def analyze_text(self, text: str) -> dict[str, float]:
        """
        Analiza el sentimiento de un texto.

        Returns:
            dict: {negative: prob, neutral: prob, positive: prob}
        """
        if not text or not text.strip():
            return {"negative": 0.0, "neutral": 100.0, "positive": 0.0}

        cache_key = str(hash(text[:500]))  # Solo primeros 500 caracteres
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return cached["data"]

        try:
            headers = {
                "Accept": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Usar API de inferencia de HuggingFace
            url = f"https://api-inference.huggingface.co/models/{self.model}"

            resp = await self.client.post(
                url,
                json={"inputs": text[:512]},  # Limitar longitud
                headers=headers,
            )

            if resp.status_code != 200:
                logger.error(f"HuggingFace API error {resp.status_code}: {resp.text}")
                return {"negative": 0.0, "neutral": 100.0, "positive": 0.0}

            result = resp.json()

            # El modelo devuelve [[{label: "...", score: 0.9}, ...]]
            if isinstance(result, list) and len(result) > 0:
                scores = {item["label"]: item["score"] for item in result[0]}

                # Normalizar a porcentajes
                total = sum(scores.values())
                normalized = {k: round(v / total * 100, 1) for k, v in scores.items()}

                # Asegurar que tenemos las 3 categorías
                final = {
                    "negative": normalized.get("LABEL_0", normalized.get("negative", 0.0)),
                    "neutral": normalized.get("LABEL_1", normalized.get("neutral", 0.0)),
                    "positive": normalized.get("LABEL_2", normalized.get("positive", 0.0)),
                }

                self.cache[cache_key] = {"ts": datetime.now(), "data": final}
                return final
            else:
                logger.warning(f"Formato inesperado de HuggingFace: {result}")
                return {"negative": 0.0, "neutral": 100.0, "positive": 0.0}

        except Exception as e:
            logger.error(f"Error analizando sentimiento: {e}")
            return {"negative": 0.0, "neutral": 100.0, "positive": 0.0}

    async def batch_analyze(self, texts: list[str]) -> list[dict[str, float]]:
        """Analiza múltiples textos en batch"""
        results = []
        for text in texts:
            result = await self.analyze_text(text)
            results.append(result)
        return results

    async def close(self) -> None:
        """Cerrar cliente HTTP"""
        await self.client.aclose()
