"""Servicio de análisis de sentimiento usando múltiples backends"""
from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from datetime import datetime

from config.settings import settings

logger = logging.getLogger(__name__)

# Modelo por defecto (cardiffnlp/twitter-roberta-base-sentiment)
DEFAULT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# Labels del modelo
LABELS = ["negative", "neutral", "positive"]

# Palabras clave en español para sentiment simple
POSITIVE_WORDS = {
    "bueno", "excelente", "increíble", "maravilloso", "fantástico", "genial",
    "positivo", "favorable", "apoyo", "apoyar", "ganar", "victoria", "triunfo",
    "lidera", "crece", "aumenta", "sube", "mejora", "mejor", "éxito",
    "amor", "feliz", "alegre", "satisfecho", "contento", "orgullo",
    "top", "preferido", "favorito", "destacado", "impresionante",
}

NEGATIVE_WORDS = {
    "malo", "terrible", "horrible", "pésimo", "desastroso", "fatal",
    "negativo", "desfavorable", "contra", "oposición", "perder", "derrota",
    "cae", "baja", "disminuye", "empeora", "peor", "fracaso",
    "odio", "triste", "enojado", "preocupado", "miedo", "corrupción",
    "escándalo", "proceso", "judicial", "investigación", "crítica",
}


class SentimentService:
    """Servicio para análisis de sentimiento"""

    def __init__(self) -> None:
        self.api_key = settings.huggingface_api_key
        self.model = DEFAULT_MODEL
        self.client = httpx.AsyncClient(timeout=15.0)
        self.cache: dict[str, dict[str, float]] = {}

    def _simple_spanish_sentiment(self, text: str) -> dict[str, float]:
        """Analiza sentimiento usando palabras clave en español"""
        text_lower = text.lower()
        words = re.findall(r'\w+', text_lower)
        
        pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
        neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
        
        total = pos_count + neg_count
        if total == 0:
            return {"negative": 0.0, "neutral": 100.0, "positive": 0.0}
        
        pos_pct = (pos_count / total) * 100
        neg_pct = (neg_count / total) * 100
        
        return {
            "negative": round(neg_pct, 1),
            "neutral": 0.0,
            "positive": round(pos_pct, 1),
        }

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

        # Intentar usar HuggingFace si hay API key
        if self.api_key:
            try:
                headers = {
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                }
                url = f"https://api-inference.huggingface.co/models/{self.model}"
                resp = await self.client.post(
                    url,
                    json={"inputs": text[:512]},
                    headers=headers,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    if isinstance(result, list) and len(result) > 0:
                        scores = {}
                        for item in result:
                            label = item.get("label", "").lower()
                            score = item.get("score", 0.0)
                            if label == "positive":
                                scores["positive"] = score * 100
                            elif label == "negative":
                                scores["negative"] = score * 100
                            else:
                                scores["neutral"] = score * 100
                        final = {
                            "negative": scores.get("negative", 0.0),
                            "neutral": scores.get("neutral", 0.0),
                            "positive": scores.get("positive", 0.0),
                        }
                        self.cache[cache_key] = {"ts": datetime.now(), "data": final}
                        return final
                else:
                    logger.error(f"HuggingFace API error {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"Error en HuggingFace API: {e}")

        # Fallback: análisis simple por palabras clave en español
        logger.info("Usando análisis de sentimiento basado en palabras clave (sin API)")
        result = self._simple_spanish_sentiment(text)
        self.cache[cache_key] = {"ts": datetime.now(), "data": result}
        return result

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
