# Servicio de Aprendizaje de Errores — Engram + Qdrant
FROM python:3.13-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY src/ ./src/
COPY tests/ ./tests/

# Exponer puerto
EXPOSE 8002

# Comando por defecto (API)
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8002"]
