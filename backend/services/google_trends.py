"""Servicio de Google Trends usando pytrends"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

import httpx
from pytrends.request import TrendReq

from config.settings import settings

logger = logging.getLogger(__name__)


class GoogleTrendsService:
    """Servicio para consultar Google Trends"""

    def __init__(self) -> None:
        self.language = settings.pytrends_language
        self.region = settings.pytrends_region
        self.timeframe = "now 7-d"  # Últimos 7 días
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

    async def get_trends_for_candidates(self, candidate_names: list[str]) -> dict[str, float]:
        """
        Obtiene el interés de búsqueda para una lista de candidatos.

        Returns:
            dict: {candidate_name: score (0-100)}
        """
        if not candidate_names:
            return {}

        try:
            # Construir payload para pytrends
            keywords = candidate_names[:5]  # pytrends limita a 5 keywords por request

            # Construir timeframe
            timeframe = "now 7-d"

            # Construir geo
            geo = self.region if self.region else None

            # Construir payload
            self.pytrends.build_payload(
                kw_list=keywords,
                timeframe=timeframe,
                geo=geo,
                gprop="",  # No filtrar por propiedad (web, images, etc.)
            )

            # Obtener datos de interés a lo largo del tiempo
            interest_over_time = self.pytrends.interest_over_time()

            if interest_over_time is None or interest_over_time.empty:
                logger.warning(f"No hay datos de Google Trends para {keywords}")
                return {name: 0.0 for name in candidate_names}

            # Calcular promedio por candidato
            scores: dict[str, float] = {}
            for name in candidate_names:
                if name in interest_over_time.columns:
                    avg_score = interest_over_time[name].mean()
                    scores[name] = round(float(avg_score), 1)
                else:
                    scores[name] = 0.0

            logger.info(f"Google Trends scores: {scores}")
            return scores

        except Exception as e:
            logger.error(f"Error consultando Google Trends: {e}")
            # Devolver 0 para todos en caso de error
            return {name: 0.0 for name in candidate_names}

    async def get_related_queries(self, candidate_name: str) -> list[str]:
        """Obtiene búsquedas relacionadas para un candidato"""
        try:
            self.pytrends.build_payload(
                kw_list=[candidate_name],
                timeframe=self.timeframe,
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

    async def get_interest_by_region(self, candidate_name: str, resolution: str = "COUNTRY") -> dict[str, float]:
        """Obtiene interés por región/ciudad"""
        try:
            self.pytrends.build_payload(
                kw_list=[candidate_name],
                timeframe=self.timeframe,
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

    async def close(self) -> None:
        """Cerrar conexión"""
        if self._pytrends:
            self._pytrends.close()
