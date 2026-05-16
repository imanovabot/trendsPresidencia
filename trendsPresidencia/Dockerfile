# Trends Presidencia - Dockerfile único (backend + frontend)
FROM nginx:alpine AS base

# Instalar Python y dependencias del sistema
RUN apk add --no-cache python3 py3-pip gcc libpq-dev musl-dev

# Crear directorio de trabajo para la app
WORKDIR /app

# Copiar requirements del backend
COPY backend/requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copiar código del backend
COPY backend/ .

# Copiar archivos del frontend a la carpeta de nginx
COPY frontend/html/ /usr/share/nginx/html/

# Copiar configuración personalizada de nginx
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copiar script de inicio
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# Exponer puertos
EXPOSE 80 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8001/health || exit 1

# Usuario no-root
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Iniciar aplicación
CMD ["/usr/local/bin/start.sh"]
