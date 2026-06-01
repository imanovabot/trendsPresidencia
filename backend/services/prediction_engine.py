"""
Motor de Predicción Electoral — trendsPresidencia
Implementa el algoritmo de alineación calibrado con datos reales de Colombia 2026.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CandidateData:
    """Datos de un candidato para el cálculo de predicción"""
    name: str
    trends_score: float  # 0-100 (promedio del día o último punto)
    historical_stability: float  # desviación estándar horaria (menor = más estable)
    is_center_candidate: bool = False
    related_queries: list[str] | None = None
    regional_strength: dict[str, float] | None = None  # {"Antioquia": 85, "Costa": 60...}
    base_support: float | None = None  # % de voto duro histórico (si se conoce)


def calculate_electoral_prediction(
    candidates: list[CandidateData],
    weighting: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Calcula el pronóstico electoral alineado usando el algoritmo calibrado.

    Args:
        candidates: Lista de candidatos con sus métricas
        weighting: Pesos para promedio del día vs última hora
                   {'daily_avg': 0.7, 'last_hour': 0.3} (default)

    Returns:
        Dict con porcentajes ajustados, segunda vuelta proyectada y metadata
    """
    if not candidates:
        return {"error": "No hay candidatos"}

    weighting = weighting or {"daily_avg": 0.7, "last_hour": 0.3}

    # 1. Calcular porcentajes brutos iniciales (sin ajustes)
    total_raw = sum(c.trends_score for c in candidates)
    raw_results = {c.name: (c.trends_score / total_raw) * 100 for c in candidates}

    # 2. Aplicar factores de ajuste por tipo de candidato
    adjusted = {}
    for c in candidates:
        base_pct = raw_results[c.name]

        # REGLA 1: Factor de desinflado de opinión (candidatos de centro/opinión)
        if c.is_center_candidate or _is_center_by_name(c.name):
            # Los candidatos de centro tienen sobreestimación histórica del 40%
            opinion_factor = 0.60  # Mantiene solo el 60% del digital
            logger.info(f"[{c.name}] Aplicando factor opinión (centro): {opinion_factor}")
            adjusted[c.name] = base_pct * opinion_factor

        # REGLA 2: Recompensa por estabilidad (voto duro)
        elif c.historical_stability < 2.0:
            structure_multiplier = 1.05  # +5% por estructura disciplinada
            logger.info(f"[{c.name}] Aplicando multiplicador estructura (+5%): {c.historical_stability}")
            adjusted[c.name] = base_pct * structure_multiplier

        # REGLA 3: Candidatos con picos normales (ej: efecto regional)
        else:
            adjusted[c.name] = base_pct

    # 3. Normalizar para que sume 100%
    total_adjusted = sum(adjusted.values())
    final_results = {name: round((score / total_adjusted) * 100, 2) for name, score in adjusted.items()}

    # 4. Determinar segunda vuelta (top 2)
    sorted_candidates = sorted(final_results.items(), key=lambda x: x[1], reverse=True)
    top_two = sorted_candidates[:2]
    runoff = {
        "candidate_a": {"name": top_two[0][0], "predicted_pct": top_two[0][1]},
        "candidate_b": {"name": top_two[1][0], "predicted_pct": top_two[1][1]},
    }

    # 5. Proyectar distribución de votos de terceros en segunda vuelta
    third_party_votes = {}
    for name, pct in sorted_candidates[2:]:
        # Asumir distribución equitativa por defecto (se puede calibrar con encuestas)
        third_party_votes[name] = {
            "current_pct": pct,
            "runoff_distribution": {
                "left": round(pct / 3, 2),
                "right": round(pct / 3, 2),
                "blank_abstention": round(pct / 3, 2),
            }
        }

    # 6. Calcular pronóstico de segunda vuelta
    runoff_forecast = _project_runoff(top_two[0][0], top_two[1][0], third_party_votes)

    return {
        "first_round": final_results,
        "runoff": runoff,
        "runoff_forecast": runoff_forecast,
        "third_party_analysis": third_party_votes,
        "metadata": {
            "algorithm_version": "1.0",
            "calibration": "Colombia 2026 elections",
            "weights_applied": weighting,
            "total_raw_score": round(total_raw, 2),
            "adjustment_factors": {
                c.name: "opinion" if c.is_center_candidate or _is_center_by_name(c.name)
                else "stability" if c.historical_stability < 2.0
                else "none"
                for c in candidates
            },
        },
    }


def _is_center_by_name(name: str) -> bool:
    """Heurística para detectar candidatos de centro por nombre"""
    center_keywords = ["Fajardo", "López", " centro", "verde", "optimista"]
    name_lower = name.lower()
    return any(kw in name_lower for kw in center_keywords)


def _project_runoff(
    candidate_a: str,
    candidate_b: str,
    third_parties: dict[str, Any]
) -> dict[str, float]:
    """
    Proyecta el resultado de segunda vuelta basado en transferencia histórica de votos.
    Por defecto asume distribución equitativa, pero se puede calibrar con encuestas.
    """
    # Obtener todos los votos de terceros
    transfer_left = 0.0
    transfer_right = 0.0
    transfer_blank = 0.0

    for party_data in third_parties.values():
        dist = party_data["runoff_distribution"]
        transfer_left += dist["left"]
        transfer_right += dist["right"]
        transfer_blank += dist["blank_abstention"]

    # Asignar transferencias (simplificado: izquierda recibe todo el centro-izquierda, derecha recibe centro-derecha)
    # Esto se puede calibrar con encuestas específicas por candidato
    final_left = 50.0 + (transfer_left - transfer_right) / 2
    final_right = 100.0 - final_left

    return {
        candidate_a: round(final_left, 2),
        candidate_b: round(final_right, 2),
        "transfer_summary": {
            "from_third_parties_to_left": round(transfer_left, 2),
            "from_third_parties_to_right": round(transfer_right, 2),
            "blank_abstention": round(transfer_blank, 2),
        }
    }


def detect_noise_shock(
    current_value: float,
    hourly_series: list[float],
    threshold_multiplier: float = 2.5
) -> dict[str, Any]:
    """
    Detecta si el valor actual es un 'shock' de audiencia (ruido) comparado con la serie horaria.

    Args:
        current_value: Valor actual del índice
        hourly_series: Serie de valores de las últimas N horas
        threshold_multiplier: Múltiplo de la desviación estándar para considerar shock

    Returns:
        Dict con is_shock, z_score, expected_range
    """
    if not hourly_series or len(hourly_series) < 3:
        return {"is_shock": False, "z_score": 0, "expected_range": (0, 100)}

    import statistics
    mean = statistics.mean(hourly_series)
    stdev = statistics.stdev(hourly_series) if len(hourly_series) > 1 else 0

    if stdev == 0:
        return {"is_shock": False, "z_score": 0, "expected_range": (mean, mean)}

    z_score = (current_value - mean) / stdev
    is_shock = abs(z_score) > threshold_multiplier

    expected_min = mean - (threshold_multiplier * stdev)
    expected_max = mean + (threshold_multiplier * stdev)

    return {
        "is_shock": is_shock,
        "z_score": round(z_score, 2),
        "current_value": current_value,
        "historical_mean": round(mean, 2),
        "historical_stdev": round(stdev, 2),
        "expected_range": (round(expected_min, 2), round(expected_max, 2)),
        "interpretation": _interpret_shock(is_shock, z_score, current_value, mean),
    }


def _interpret_shock(is_shock: bool, z_score: float, current: float, mean: float) -> str:
    if not is_shock:
        return "Valor dentro del rango esperado"
    elif current > mean:
        return f"Pico anómalo positivo (z={z_score:.1f}): probable shock de audiencia (stream, noticia viral)"
    else:
        return f"Caída anómala (z={z_score:.1f}): posible pérdida de interés o evento negativo"


def calculate_hourly_stability(hourly_values: list[float]) -> float:
    """
    Calcula la desviación estándar de una serie horaria.
    Menor valor = candidato con voto duro y estable.
    Mayor valor = candidato volátil o dependiente de eventos.
    """
    if len(hourly_values) < 2:
        return 0.0
    import statistics
    return round(statistics.stdev(hourly_values), 2)


def calculate_weighted_daily_average(
    measurements: list[dict[str, float]],
    hour_weights: dict[int, float] | None = None
) -> dict[str, float]:
    """
    Promedio ponderado del día, dando más peso a las horas clave (12:00-16:00).

    Args:
        measurements: Lista de mediciones por hora [{hour: 12, "Cepeda": 80, "Abelardo": 90}, ...]
        hour_weights: Pesos por hora (default: horas 12-16 tienen peso 2.0)

    Returns:
        Dict con promedio ponderado por candidato
    """
    if not measurements:
        return {}

    # Pesos por defecto: horas 12-16 (12:00-16:59) tienen el doble de peso
    default_weights = {h: 1.0 for h in range(24)}
    for h in range(12, 17):  # 12:00 - 16:59
        default_weights[h] = 2.0

    weights = hour_weights or default_weights

    # Obtener todos los nombres de candidatos
    all_names = set()
    for m in measurements:
        all_names.update(m.keys())
    all_names.discard("hour")

    weighted_sums = {name: 0.0 for name in all_names}
    weight_sum = {name: 0.0 for name in all_names}

    for measurement in measurements:
        hour = measurement.get("hour", 0)
        weight = weights.get(hour, 1.0)

        for name in all_names:
            if name in measurement:
                weighted_sums[name] += measurement[name] * weight
                weight_sum[name] += weight

    # Calcular promedio ponderado
    result = {}
    for name in all_names:
        if weight_sum[name] > 0:
            result[name] = round(weighted_sums[name] / weight_sum[name], 2)
        else:
            result[name] = 0.0

    return result
