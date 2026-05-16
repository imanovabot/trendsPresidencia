# Frontend - Nginx sirviendo archivos estáticos
FROM nginx:alpine

# Copiar archivos estáticos
COPY html/ /usr/share/nginx/html/

# Configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=2s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1