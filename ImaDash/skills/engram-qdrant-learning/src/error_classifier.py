"""Clasificación de errores por tipo y severidad"""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass

class ErrorType(str, Enum):
    DEPLOYMENT = "deployment"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    API = "api"
    CONFIG = "config"
    TEST = "test"
    UNKNOWN = "unknown"

class Severity(str, Enum):
    CRITICAL = "critical"   # Bloquea producción
    HIGH = "high"           # Funcionalidad rota
    MEDIUM = "medium"       # Funcionalidad degradada
    LOW = "low"             # Menor, cosmético

@dataclass
class ClassifiedError:
    type: ErrorType
    severity: Severity
    keywords: list[str]
    suggested_solution: str

class ErrorClassifier:
    """Clasifica errores automáticamente"""
    
    PATTERNS = {
        ErrorType.DEPLOYMENT: {
            "keywords": ["desplegar", "deploy", "coolify", "docker", "producción", "403", "404", "500"],
            "severity_map": {"403": Severity.HIGH, "404": Severity.MEDIUM, "500": Severity.CRITICAL},
            "default_solution": "Verificar configuración de despliegue y logs del contenedor"
        },
        ErrorType.FRONTEND: {
            "keywords": ["frontend", "botón", "css", "javascript", "refrescar", "html", "react", "vue"],
            "default_solution": "Revisar consola del navegador y compilar assets"
        },
        ErrorType.BACKEND: {
            "keywords": ["backend", "api", "endpoint", "fastapi", "django", "flask", "python"],
            "default_solution": "Verificar logs del servidor y tests unitarios"
        },
        ErrorType.DATABASE: {
            "keywords": ["database", "postgres", "mysql", "sql", "migración", "tabla"],
            "default_solution": "Verificar conexión y esquema de base de datos"
        },
        ErrorType.CONFIG: {
            "keywords": ["config", "env", "variable", ".env", "settings"],
            "default_solution": "Verificar variables de entorno y archivos de configuración"
        },
        ErrorType.TEST: {
            "keywords": ["test", "pytest", "fallido", "assert", "error de prueba"],
            "default_solution": "Ejecutar tests con verbose y revisar fallos"
        }
    }
    
    @classmethod
    def classify(cls, error_message: str, context: str = "") -> ClassifiedError:
        """Clasifica un error basándose en palabras clave"""
        text = f"{error_message} {context}".lower()
        
        # Buscar coincidencias
        for error_type, config in cls.PATTERNS.items():
            for keyword in config["keywords"]:
                if keyword.lower() in text:
                    # Determinar severidad
                    severity = config.get("default_severity", Severity.MEDIUM)
                    for pattern, sev in config.get("severity_map", {}).items():
                        if pattern.lower() in text:
                            severity = sev
                            break
                    
                    return ClassifiedError(
                        type=error_type,
                        severity=severity,
                        keywords=[kw for kw in config["keywords"] if kw.lower() in text],
                        suggested_solution=config["default_solution"]
                    )
        
        return ClassifiedError(
            type=ErrorType.UNKNOWN,
            severity=Severity.MEDIUM,
            keywords=[],
            suggested_solution="Investigar mensaje de error y contexto"
        )
