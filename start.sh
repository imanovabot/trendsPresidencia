#!/bin/bash
set -e

# Iniciar backend en background
cd /app/backend
uvicorn main:app --host 0.0.0.0 --port 8001 --log-level info &
BACKEND_PID=$!

# Esperar a que el backend esté listo
sleep 3

# Iniciar nginx en foreground (reemplaza este proceso)
exec nginx -g 'daemon off;'
