"""Captura de errores con Engram-style (sin dependencias externas)"""
from __future__ import annotations

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

class MemoryCapture:
    """Captura errores y los almacena en formato Engram-compatible"""
    
    def __init__(self, storage_dir: str = ".engram_cache"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.errors_file = self.storage_dir / "errors.jsonl"
    
    def capture_error(
        self,
        error_type: str,
        message: str,
        context: str,
        solution: str,
        severity: str = "medium",
        metadata: dict[str, Any] | None = None
    ) -> str:
        """
        Captura un error con su contexto y solución.
        
        Returns:
            error_id: hash único del error
        """
        error_data = {
            "error_type": error_type,
            "message": message,
            "context": context,
            "solution": solution,
            "severity": severity,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
            "fingerprint": self._fingerprint(error_type, message)
        }
        
        # Guardar en JSONL (append)
        with open(self.errors_file, "a") as f:
            f.write(json.dumps(error_data) + "\n")
        
        error_id = error_data["fingerprint"]
        print(f"✅ Error capturado: {error_type} (ID: {error_id[:12]}...)")
        return error_id
    
    def _fingerprint(self, error_type: str, message: str) -> str:
        """Genera hash único para deduplicar errores"""
        content = f"{error_type}:{message}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_error(self, error_id: str) -> dict | None:
        """Recupera un error por su ID"""
        with open(self.errors_file) as f:
            for line in f:
                error = json.loads(line)
                if error["fingerprint"] == error_id:
                    return error
        return None
    
    def list_errors(self, limit: int = 100) -> list[dict]:
        """Lista errores recientes"""
        errors = []
        with open(self.errors_file) as f:
            for line in f:
                errors.append(json.loads(line))
        return sorted(errors, key=lambda x: x["timestamp"], reverse=True)[:limit]
