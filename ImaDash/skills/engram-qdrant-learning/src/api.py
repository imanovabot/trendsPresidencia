"""API REST del sistema de aprendizaje de errores"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.learning_loop import LearningLoop
from src.qdrant_store import QdrantErrorStore

app = FastAPI(
    title="Engram-Qdrant Learning API",
    description="Sistema de memoria semántica para aprender de errores",
    version="1.0.0"
)

loop = LearningLoop()
store = QdrantErrorStore()

class ErrorReport(BaseModel):
    error_message: str
    context: str = ""
    solution: str = ""
    severity: str | None = None

class SearchQuery(BaseModel):
    query: str
    limit: int = 5

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/stats")
async def stats() -> dict[str, Any]:
    return store.get_stats()

@app.post("/errors/record")
async def record_error(error: ErrorReport) -> dict[str, Any]:
    """Registra un error y devuelve soluciones sugeridas"""
    result = loop.record_error(
        error_message=error.error_message,
        context=error.context,
        solution=error.solution,
        severity=error.severity
    )
    return result

@app.post("/errors/report")
async def report_error(error: ErrorReport) -> dict[str, str]:
    """Devuelve reporte formateado del error"""
    report = loop.report_error(
        error_message=error.error_message,
        context=error.context,
        solution=error.solution
    )
    return {"report": report}

@app.post("/errors/search")
async def search_errors(query: SearchQuery) -> dict[str, Any]:
    """Busca errores similares por consulta semántica"""
    results = store.search_similar(query.query, limit=query.limit)
    return {"query": query.query, "results": results}

@app.get("/errors/recent")
async def recent_errors(limit: int = 10) -> dict[str, Any]:
    """Errores más recientes"""
    from src.memory import MemoryCapture
    capturer = MemoryCapture()
    errors = capturer.list_errors(limit=limit)
    return {"errors": errors}

# Para ejecutar: uvicorn src.api:app --reload
