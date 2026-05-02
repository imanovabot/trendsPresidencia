# Tests de ImaDash

## Ejecución

```bash
# Instalar dependencias de test
pip install -r requirements-dev.txt

# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=services --cov=routers --cov-report=html
```

## Cobertura esperada

- services/email_reader.py: 90%+
- services/transcription_reader.py: 95%+
- services/calendar_reader.py: 90%+
- services/github_reader.py: 90%+
- services/imapi_client.py: 95%+
- routers/*.py: integración básica
