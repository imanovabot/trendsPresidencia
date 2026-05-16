# Backend API - FastAPI
# Usa Python 3.13 slim como base
FROM python:3.13-slim AS builder

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/deps -r requirements.txt

# Imagen final
FROM python:3.13-slim

# Instalar solo lo necesario en runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias desde builder
COPY --from=builder /deps /usr/local/lib/python3.13/site-packages
COPY --from=builder /deps/bin /usr/local/bin

# Copiar aplicación
WORKDIR /app
COPY . .

# Crear usuario no-root
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "info"]