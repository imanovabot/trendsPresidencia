# Sistema de Aprendizaje de Errores — Engram + Qdrant

Este módulo implementa un sistema de memoria semántica para aprender de errores pasados y no repetirlos.

## Estructura

```
engram-qdrant-learning/
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── memory.py          # Engram: captura y almacena errores
│   ├── qdrant_store.py    # Qdrant: búsqueda semántica de errores
│   ├── error_classifier.py # Clasifica errores por tipo/severidad
│   └── learning_loop.py   # Ciclo de aprendizaje automático
├── tests/
│   └── test_learning.py
└── docker-compose.yml     # Qdrant + servicio de aprendizaje
```

## Instalación

```bash
pip install -r requirements.txt
docker-compose up -d qdrant  # Levantar Qdrant
```

## Uso rápido

```python
from src.memory import MemoryCapture
from src.qdrant_store import QdrantErrorStore

# Capturar un error
capturer = MemoryCapture()
error_id = capturer.capture_error(
    error_type="frontend_refresh_button_missing",
    message="Botón de refrescar no aparece en producción",
    context="Coolify no desplegó rama trendsPresidencia",
    solution="Verificar configuración de rama en Coolify",
    severity="medium"
)

# Buscar errores similares
store = QdrantErrorStore()
similar = store.search_similar("botón refrescar no aparece producción", limit=5)
print(similar)  # Encuentra el error anterior y su solución
```

## Cómo funciona

1. **Engram** captura cada error con contexto, solución y severidad
2. **Qdrant** indexa los errores como vectores semánticos (embedding)
3. Cuando surge un error nuevo, se busca en Qdrant errores similares
4. Se sugiere la solución probada, evitando repetir errores

## Integración con Hermes

Hermes puede usar este sistema antes de reportar un error:
- Capturar el error automáticamente
- Buscar soluciones pasadas
- Incluir soluciones previas en el reporte

## Ejemplos de uso

Ver `tests/test_learning.py` para ejemplos completos.
