"""Servicio de Google Trends usando pytrends"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

import httpx
import statistics
from pytrends.request import TrendReq

from config.settings import settings

logger = logging.getLogger(__name__)


class GoogleTrendsService:
    """Servicio para consultar Google Trends con filtros electorales avanzados"""

    def __init__(self) -> None:
        self.language = settings.pytrends_language
        self.region = settings.pytrends_region
        self.timeframe = "now 7-d"  # Últimos 7 días (ventana electoral recomendada)
        self._pytrends: TrendReq | None = None

    @property
    def pytrends(self) -> TrendReq:
        if self._pytrends is None:
            self._pytrends = TrendReq(
                hl=self.language,
                tz=360,
                timeout=(10, 25),
                proxies=None,
            )
        return self._pytrends

    async def get_trends_for_candidates(
        self,
        candidate_names: list[str],
        timeframe: str | None = None,
        use_topic: bool = False,
        candidate_topics: dict[str, str] | None = None
    ) -> dict[str, float]:
        """
        Obtiene el interés de búsqueda para una lista de candidatos.

        Args:
            candidate_names: Lista de nombres de candidatos
            timeframe: Ventana de tiempo (ej: "now 7-d", "now 1-d", "today 12-h")
            use_topic: Si es True, usa Google Topics en lugar de términos exactos
            candidate_topics: Dict {nombre: topic_id} para usar Topics

        Returns:
            dict: {candidate_name: score (0-100)}
        """
        if not candidate_names:
            return {}

        try:
            keywords = candidate_names[:5]
            tf = timeframe or self.timeframe
            geo = self.region if self.region else None

            # Si use_topic=True, convertir nombres a topic IDs
            if use_topic and candidate_topics:
                keywords = [candidate_topics.get(name, name) for name in keywords]

            self.pytrends.build_payload(
                kw_list=keywords,
                timeframe=tf,
                geo=geo,
                gprop="",
            )

            interest_over_time = self.pytrends.interest_over_time()

            if interest_over_time is None or interest_over_time.empty:
                logger.warning(f"No hay datos de Google Trends para {keywords}")
                return {name: 0.0 for name in candidate_names}

            # Calcular promedio por candidato
            scores: dict[str, float] = {}
            for name in candidate_names:
                col_name = candidate_topics.get(name, name) if use_topic else name
                if col_name in interest_over_time.columns:
                    avg_score = interest_over_time[col_name].mean()
                    scores[name] = round(float(avg_score), 1)
                else:
                    scores[name] = 0.0

            logger.info(f"Google Trends scores ({tf}, use_topic={use_topic}): {scores}")
            return scores

        except Exception as e:
            logger.error(f"Error consultando Google Trends: {e}")
            return {name: 0.0 for name in candidate_names}

    async def get_related_queries(self, candidate_name: str, timeframe: str | None = None) -> list[str]:
        """Obtiene búsquedas relacionadas para un candidato"""
        try:
            tf = timeframe or self.timeframe
            self.pytrends.build_payload(
                kw_list=[candidate_name],
                timeframe=tf,
                geo=self.region,
            )
            related = self.pytrends.related_queries()
            if candidate_name in related and related[candidate_name]:
                top = related[candidate_name].get("top", [])
                return [row["query"] for row in top[:10]]
            return []
        except Exception as e:
            logger.error(f"Error obteniendo related queries para {candidate_name}: {e}")
            return []

    async def get_interest_by_region(
        self,
        candidate_name: str,
        resolution: str = "COUNTRY",
        timeframe: str | None = None
    ) -> dict[str, float]:
        """Obtiene interés por región/ciudad"""
        try:
            tf = timeframe or self.timeframe
            self.pytrends.build_payload(
                kw_list=[candidate_name],
                timeframe=tf,
                geo=self.region,
            )
            interest_by_region = self.pytrends.interest_by_region(
                resolution=resolution,
                inc_low_vol=True,
                inc_geo_code=True,
            )
            if interest_by_region is not None and candidate_name in interest_by_region.columns:
                return interest_by_region[candidate_name].to_dict()
            return {}
        except Exception as e:
            logger.error(f"Error obteniendo interés por región para {candidate_name}: {e}")
            return {}

    async def get_hourly_series(
        self,
        candidate_name: str,
        timeframe: str = "today 12-h"
    ) -> list[dict[str, Any]]:
        """
        Obtiene serie horaria de las últimas 12 horas para detectar ruido.
        Retorna: [{"hour": 10, "value": 85.2}, {"hour": 11, "value": 92.1}, ...]
        """
        try:
            self.pytrends.build_payload(
                kw_list=[candidate_name],
                timeframe=timeframe,
                geo=self.region,
            )
            interest_over_time = self.pytrends.interest_over_time()

            if interest_over_time is None or interest_over_time.empty:
                return []

            series = []
            for idx, row in interest_over_time.iterrows():
                hour = idx.hour if hasattr(idx, 'hour') else idx.strftime('%H')
                value = float(row[candidate_name]) if candidate_name in row else 0.0
                series.append({"hour": int(hour), "value": round(value, 2)})

            return series
        except Exception as e:
            logger.error(f"Error obteniendo serie horaria para {candidate_name}: {e}")
            return []

    async def calculate_stability_score(self, candidate_name: str) -> float:
        """
        Calcula la desviación estándar de las últimas 24 horas.
        Menor valor = más estable (voto duro).
        """
        series = await self.get_hourly_series(candidate_name, timeframe="today 24-h")
        values = [s["value"] for s in series]
        if len(values) < 2:
            return 0.0
        return round(statistics.stdev(values), 2)

    async def detect_noise_shock(
        self,
        candidate_name: str,
        current_value: float | None = None
    ) -> dict[str, Any]:
        """
        Detecta si el candidato tiene un pico anómalo (shock de audiencia).
        Compara el valor actual con la serie de las últimas 12 horas.
        """
        series = await self.get_hourly_series(candidate_name, timeframe="today 12-h")

        if not series:
            return {"is_shock": False, "z_score": 0, "interpretation": "Sin datos"}

        # Si no se provee current_value, usar el último de la serie
        if current_value is None:
            current_value = series[-1]["value"]

        values = [s["value"] for s in series]
        return self._calculate_shock(current_value, values)

    def _calculate_shock(
        self,
        current_value: float,
        historical_values: list[float]
    ) -> dict[str, Any]:
        """Calcula si el valor actual es un shock estadístico"""
        from services.prediction_engine import detect_noise_shock
        return detect_noise_shock(current_value, historical_values)

    async def close(self) -> None:
        """Cerrar conexión"""
        if self._pytrends:
            self._pytrends.close()
