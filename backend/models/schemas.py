"""Modelos Pydantic para la API de trendsPresidencia"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SentimentBreakdown(BaseModel):
    positive: float = Field(..., ge=0, le=100, description="Porcentaje de sentimiento positivo")
    neutral: float = Field(..., ge=0, le=100, description="Porcentaje de sentimiento neutral")
    negative: float = Field(..., ge=0, le=100, description="Porcentaje de sentimiento negativo")


class CandidateSources(BaseModel):
    google_trends: float = Field(default=0.0, ge=0, le=100, description="Puntaje Google Trends (0-100)")
    youtube: float = Field(default=0.0, ge=0, le=100, description="Puntaje YouTube (0-100)")
    tiktok: float = Field(default=0.0, ge=0, le=100, description="Puntaje TikTok (0-100)")
    x: float = Field(default=0.0, ge=0, le=100, description="Puntaje X/Twitter (0-100)")
    instagram: float = Field(default=0.0, ge=0, le=100, description="Puntaje Instagram (0-100)")
    sentiment: float = Field(..., ge=0, le=100, description="Puntaje de sentimiento (0-100)")


class Candidate(BaseModel):
    id: str = Field(..., description="Identificador único del candidato")
    name: str = Field(..., description="Nombre completo del candidato")
    party: str = Field(..., description="Partido político o coalición")
    momentum: float = Field(..., ge=0, le=100, description="Puntaje de momentum digital (0-100)")
    change_24h: float = Field(..., description="Cambio en las últimas 24 horas (porcentaje)")
    sources: CandidateSources
    sentiment_breakdown: SentimentBreakdown
    top_news: List[str] = Field(default_factory=list, description="Noticias más relevantes")
    description: str = Field(..., description="Descripción breve del candidato")
    color: str = Field(..., pattern=r'^#[0-9A-Fa-f]{6}$', description="Color hexadecimal para UI")


class CandidateList(BaseModel):
    candidates: List[Candidate]
    total: int
    last_updated: datetime
    update_frequency_hours: int


class CandidateDetail(Candidate):
    sources_detail: Optional[dict] = Field(None, description="Desglose detallado de fuentes")
    recent_news: Optional[List[dict]] = Field(None, description="Noticias recientes con metadata")


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
