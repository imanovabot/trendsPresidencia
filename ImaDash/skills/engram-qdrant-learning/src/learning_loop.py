"""Ciclo de aprendizaje automático de errores"""
from __future__ import annotations

import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent))

from memory import MemoryCapture
from qdrant_store import QdrantErrorStore
from error_classifier import ErrorClassifier, ClassifiedError

class LearningLoop:
    """Ciclo completo: capturar → clasificar → indexar → buscar soluciones"""
    
    def __init__(self):
        self.capturer = MemoryCapture()
        self.store = QdrantErrorStore()
        self.classifier = ErrorClassifier()
    
    def record_error(
        self,
        error_message: str,
        context: str = "",
        solution: str = "",
        severity: str | None = None
    ) -> dict:
        """
        Registra un error y devuelve sugerencias de soluciones pasadas.
        
        Returns:
            {
                "error_id": str,
                "classification": ClassifiedError,
                "similar_past": list[dict],  # Errores similares con sus soluciones
                "suggested_solution": str
            }
        """
        # 1. Clasificar
        classification = self.classifier.classify(error_message, context)
        severity = severity or classification.severity.value
        
        # 2. Buscar errores similares antes de capturar
        similar_past = self.store.search_similar(f"{error_message} {context}", limit=3)
        
        # 3. Determinar solución sugerida
        if similar_past and similar_past[0]["score"] > 0.7:
            # Alta confianza: usar solución de error similar
            suggested_solution = similar_past[0]["solution"]
            confidence = "high"
        elif similar_past and similar_past[0]["score"] > 0.5:
            suggested_solution = similar_past[0]["solution"]
            confidence = "medium"
        else:
            suggested_solution = solution or classification.suggested_solution
            confidence = "new"
        
        # 4. Capturar error
        error_id = self.capturer.capture_error(
            error_type=classification.type.value,
            message=error_message,
            context=context,
            solution=suggested_solution,
            severity=severity,
            metadata={
                "keywords": classification.keywords,
                "confidence": confidence,
                "similar_count": len(similar_past)
            }
        )
        
        # 5. Indexar en Qdrant
        self.store.index_error({
            "fingerprint": error_id,
            "error_type": classification.type.value,
            "message": error_message,
            "context": context,
            "solution": suggested_solution,
            "severity": severity,
            "timestamp": self.capturer.get_error(error_id)["timestamp"]
        })
        
        return {
            "error_id": error_id,
            "classification": {
                "type": classification.type.value,
                "severity": severity,
                "keywords": classification.keywords,
                "suggested_solution": classification.suggested_solution
            },
            "similar_past": similar_past,
            "suggested_solution": suggested_solution,
            "confidence": confidence
        }
    
    def report_error(self, error_message: str, context: str = "", solution: str = "") -> str:
        """
        Reporta un error de forma legible con soluciones sugeridas.
        
        Returns:
            Texto formateado del reporte
        """
        result = self.record_error(error_message, context, solution)
        
        lines = [
            "=" * 60,
            "🐛 ERROR REPORTADO Y APRENDIDO",
            "=" * 60,
            f"ID: {result['error_id'][:16]}...",
            f"Tipo: {result['classification']['type']}",
            f"Severidad: {result['classification']['severity']}",
            "",
            f"📝 Mensaje:",
            f"   {error_message}",
            "",
            f"💡 Solución sugerida:",
            f"   {result['suggested_solution']}",
            f"   (Confianza: {result['confidence']})",
        ]
        
        if result["similar_past"]:
            lines.extend([
                "",
                f"🔍 Errores similares encontrados ({len(result['similar_past'])}):"
            ])
            for i, past in enumerate(result["similar_past"][:3], 1):
                lines.append(f"   {i}. [{past['score']:.2%}] {past['message']}")
                lines.append(f"      Solución: {past['solution']}")
        
        lines.extend([
            "",
            "=" * 60,
            "✅ Error indexado en memoria semántica"
        ])
        
        return "\n".join(lines)

# CLI rápido
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python learning_loop.py 'mensaje de error' ['contexto'] ['solución']")
        sys.exit(1)
    
    error_msg = sys.argv[1]
    context = sys.argv[2] if len(sys.argv) > 2 else ""
    solution = sys.argv[3] if len(sys.argv) > 3 else ""
    
    loop = LearningLoop()
    print(loop.report_error(error_msg, context, solution))
