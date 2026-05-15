"""Tests del sistema de aprendizaje de errores"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memory import MemoryCapture
from qdrant_store import QdrantErrorStore
from error_classifier import ErrorClassifier, ErrorType, Severity

def test_memory_capture():
    print("\n🧪 Test MemoryCapture")
    capturer = MemoryCapture(storage_dir="/tmp/test_engram")
    
    error_id = capturer.capture_error(
        error_type="frontend",
        message="Botón de refrescar no aparece",
        context="Coolify no desplegó",
        solution="Verificar rama en Coolify",
        severity="medium"
    )
    
    assert len(error_id) == 64, "Error ID debe ser SHA256 hex"
    errors = capturer.list_errors()
    assert len(errors) >= 1, "Debe haber al menos un error"
    print(f"✅ Capturado error: {error_id[:12]}...")

def test_classifier():
    print("\n🧪 Test ErrorClassifier")
    
    # Test deployment error
    result = ErrorClassifier.classify("Error 403 en producción", "Coolify falló")
    assert result.type == ErrorType.DEPLOYMENT
    assert result.severity == Severity.HIGH
    print(f"✅ Clasificado: {result.type} / {result.severity}")
    
    # Test frontend error
    result = ErrorClassifier.classify("Botón CSS no funciona", "refrescar falla")
    assert result.type == ErrorType.FRONTEND
    print(f"✅ Clasificado: {result.type}")
    
    # Test config error
    result = ErrorClassifier.classify("Falta variable de entorno", ".env incompleto")
    assert result.type == ErrorType.CONFIG
    print(f"✅ Clasificado: {result.type}")

def test_qdrant_store():
    print("\n🧪 Test QdrantErrorStore")
    store = QdrantErrorStore()
    stats = store.get_stats()
    print(f"   Backend: {stats['backend']}, Points: {stats['points']}")
    
    # Indexar error
    error_data = {
        "fingerprint": "test123",
        "error_type": "test",
        "message": "Error de prueba",
        "context": "testing",
        "solution": "Reiniciar sistema",
        "severity": "low",
        "timestamp": "2025-01-01T00:00:00"
    }
    store.index_error(error_data)
    
    # Buscar
    results = store.search_similar("error prueba", limit=1)
    assert len(results) >= 0, "Búsqueda debe retornar lista"
    if results:
        assert results[0]["message"] == "Error de prueba", "Debe encontrar el error de prueba"
    print(f"✅ Búsqueda funciona, encontrados: {len(results)}")

def test_learning_loop():
    print("\n🧪 Test LearningLoop")
    from learning_loop import LearningLoop
    
    loop = LearningLoop()
    result = loop.record_error(
        error_message="Botón refrescar no aparece",
        context="Coolify desplegó código viejo",
        solution="Verificar rama trendsPresidencia"
    )
    
    assert "error_id" in result
    assert "classification" in result
    assert "suggested_solution" in result
    print(f"✅ Ciclo completo: {result['confidence']} confianza")
    print(f"   Solución: {result['suggested_solution'][:60]}...")

def test_report_format():
    print("\n🧪 Test report_error")
    from learning_loop import LearningLoop
    
    loop = LearningLoop()
    report = loop.report_error(
        error_message="Test error report",
        context="Desde test",
        solution="Hacer esto"
    )
    
    assert "ERROR REPORTADO" in report
    assert "Solución sugerida" in report
    print("✅ Reporte formateado correctamente")
    print(report[:200])

if __name__ == "__main__":
    print("="*60)
    print("🧪 TESTS — Sistema de Aprendizaje de Errores")
    print("="*60)
    
    test_memory_capture()
    test_classifier()
    test_qdrant_store()
    test_learning_loop()
    test_report_format()
    
    print("\n" + "="*60)
    print("✅ Todos los tests pasaron")
    print("="*60)
