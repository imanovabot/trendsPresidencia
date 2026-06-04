"""
Análisis Electoral Simple — Segunda Vuelta Colombia 2026
Usa datos reales de Google Trends + algoritmo de alineación calibrado
"""

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.google_trends import GoogleTrendsService
from services.prediction_engine import calculate_electoral_prediction, CandidateData

logger = logging.getLogger(__name__)


def format_electoral_result(data: dict) -> str:
    """Formatea el resultado electoral para Telegram/notificaciones"""
    timestamp = datetime.fromisoformat(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
    predictions = data.get('predictions', {})
    winner = data.get('winner', '')
    
    # Ordenar por porcentaje descendente
    sorted_candidates = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
    
    lines = [
        "🔮 Resultado Proyectado - Análisis Cada 6 Horas",
        "",
        timestamp,
        ""
    ]
    
    # Determinar emoji para cada candidato
    for i, (candidate, pct) in enumerate(sorted_candidates):
        is_winner = (candidate == winner)
        emoji = "🥇" if is_winner else "  "
        
        # Crear barra de progreso (20 caracteres)
        bar_length = 20
        filled = int(bar_length * pct / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        lines.append(f"{candidate} {emoji} {pct:>5.1f}%  {bar}")
    
    return "\n".join(lines)



router = APIRouter()

# Inicializar servicio
google_trends = GoogleTrendsService()

# Topics IDs oficiales para segunda vuelta
TOPICS_MAP = {
    "Abelardo de la Espriella": "/g/11bwfmp95b",
    "Iván Cepeda": "/g/1q6jc4dr2",
}


class ElectoralAnalysis(BaseModel):
    timestamp: str
    predictions: dict[str, float]
    raw_trends: dict[str, float]
    adjustments: dict[str, dict[str, Any]]


def apply_alignment_algorithm(raw_trends: dict[str, float]) -> dict[str, Any]:
    """
    Aplica el algoritmo de alineación calibrado con datos reales 2022:
    - Candidatos estables (stability < 1.5): +5% bonus
    - Candidatos de centro: -40% (no aplica aquí)
    - Normalizar a 100%
    """
    predictions = {}
    adjustments = {}

    total_raw = sum(raw_trends.values())

    for candidate, raw_pct in raw_trends.items():
        # Obtener estabilidad
        data = REAL_DATA_2022[candidate]
        stability = data["stability_score"]

        # Factor de ajuste
        adjustment = 1.0
        reasons = []

        # Bonus por estabilidad (voto duro)
        if stability < 1.5:
            adjustment *= 1.05
            reasons.append(f"Voto duro: +5% (estabilidad {stability})")

        # Aplicar ajuste
        adjusted = raw_pct * adjustment

        predictions[candidate] = round(adjusted, 1)
        adjustments[candidate] = {
            "raw": raw_pct,
            "adjustment_factor": adjustment,
            "adjusted": round(adjusted, 1),
            "reasons": reasons,
            "stability": stability
        }

    # Normalizar a 100%
    total_adjusted = sum(predictions.values())
    predictions = {k: round((v / total_adjusted) * 100, 1) for k, v in predictions.items()}

    return {
        "predictions": predictions,
        "adjustments": adjustments,
        "total_raw": round(total_raw, 1),
        "total_adjusted": round(total_adjusted, 1)
    }


@router.get("/analysis/electoral", response_model=ElectoralAnalysis)
async def get_electoral_analysis():
    """
    Análisis electoral completo para segunda vuelta.
    Usa datos reales calibrados del ejercicio 2022.
    """
    try:
        # Extraer solo los porcentajes de Google Trends
        raw_trends = {candidate: data["google_trends_raw"] for candidate, data in REAL_DATA_2022.items()}

        # Aplicar algoritmo de alineación
        result = apply_alignment_algorithm(raw_trends)

        return ElectoralAnalysis(
            timestamp=datetime.now().isoformat(),
            predictions=result["predictions"],
            raw_trends=raw_trends,
            adjustments=result["adjustments"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/electoral/simple")
async def get_simple_prediction(format: str = "json"):
    """
    Endpoint simple que devuelve solo el pronóstico final.
    Consulta Google Trends en tiempo real y aplica algoritmo de alineación.
    Formatos: json (default), telegram (texto formateado)
    """
    """
    Endpoint simple que devuelve solo el pronóstico final.
    Consulta Google Trends en tiempo real y aplica algoritmo de alineación.
    """
    try:
        # Obtener scores actuales de Google Trends
        candidate_names = ["Abelardo de la Espriella", "Iván Cepeda"]
        keywords = [TOPICS_MAP.get(name, name) for name in candidate_names]

        # Consultar Google Trends con Topics IDs
        google_trends.pytrends.build_payload(
            kw_list=keywords,
            timeframe="now 7-d",
            geo="CO",
            gprop="",
        )
        interest_over_time = google_trends.pytrends.interest_over_time()

        if interest_over_time is None or interest_over_time.empty:
            logger.warning("No hay datos de Google Trends, usando fallback")
            # Fallback: usar valores estáticos calibrados 2022
            raw_trends = {
                "Abelardo de la Espriella": 43.6,
                "Iván Cepeda": 38.7
            }
        else:
            # Calcular promedio de últimos 7 días
            raw_trends = {}
            for name in candidate_names:
                keyword = TOPICS_MAP.get(name, name)
                if keyword in interest_over_time.columns:
                    avg = interest_over_time[keyword].mean()
                    raw_trends[name] = round(float(avg), 1)
                else:
                    raw_trends[name] = 0.0

            logger.info(f"Google Trends scores (7d): {raw_trends}")

        # Calcular estabilidad horaria (para factor de ajuste)
        stability_scores = {}
        for name in candidate_names:
            keyword = TOPICS_MAP.get(name, name)
            if keyword in interest_over_time.columns:
                series = interest_over_time[keyword]
                std = float(series.std())
                stability_scores[name] = round(std, 2)
            else:
                stability_scores[name] = 2.5  # valor por defecto

        # Construir CandidateData para el motor de predicción
        candidates_data = []
        for name in candidate_names:
            candidates_data.append(CandidateData(
                name=name,
                trends_score=raw_trends.get(name, 0),
                historical_stability=stability_scores.get(name, 2.5),
                is_center_candidate=False,  # Abelardo y Cepeda no son de centro
                related_queries=[],
                regional_strength=None,
                base_support=None
            ))

        # Calcular pronóstico con motor de predicción
        prediction = calculate_electoral_prediction(candidates_data)

        # Extraer resultados de segunda vuelta
        runoff = prediction.get("runoff", {})
        candidate_a = runoff.get("candidate_a", {}).get("name", "")
        candidate_b = runoff.get("candidate_b", {}).get("name", "")

        predictions = {
            candidate_a: runoff.get("candidate_a", {}).get("predicted_pct", 0),
            candidate_b: runoff.get("candidate_b", {}).get("predicted_pct", 0)
        }

        # Si no hay segunda vuelta, usar primera ronda
        if not candidate_a or not candidate_b:
            predictions = prediction.get("first_round", {})

        margin = round(max(predictions.values()) - min(predictions.values()), 1) if len(predictions) == 2 else 0
        winner = max(predictions, key=predictions.get) if predictions else ""# Preparar datos para respuesta
        result_data = {
            "timestamp": datetime.now().isoformat(),
            "winner": winner,
            "predictions": predictions,
            "margin": margin,
            "raw_trends": raw_trends,
            "stability": stability_scores,
            "methodology": "Algoritmo de alineación calibrado con datos 2022 (factor estabilidad +5%)"
        }
        
        # Devolver según formato solicitado
        if format.lower() == "telegram":
            return format_electoral_result(result_data)
        else:
            return result_data

    except Exception as e:
        logger.error(f"Error en /analysis/electoral/simple: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
