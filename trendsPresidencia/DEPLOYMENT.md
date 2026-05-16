# Despliegue en Coolify — trendsPresidencia

## 📋 Requisitos previos

- Cuenta en Coolify (instancia en 187.77.14.245)
- Dominio `trends.imanova.co` configurado en Cloudflare/dns-parking
- Acceso SSH al servidor (ya configurado)

## 🏗️ Arquitectura

La aplicación consta de **dos servicios**:

1. **Backend API** (FastAPI, puerto 8001) — Consulta APIs reales:
   - Google Trends (pytrends)
   - YouTube Data API v3
   - HuggingFace Sentiment
   - RSS feeds de noticias

2. **Frontend** (Nginx, puerto 80) — Sirve archivos estáticos y consume la API

## 🚀 Opción A: Despliegue automático con Docker Compose

### Paso 1: Clonar repositorio en el servidor

```bash
ssh root@187.77.14.245
cd /data/ima/sites
git clone https://github.com/imanovabot/ImaDash.git trends-presidencia
cd trends-presidencia
git checkout trendsPresidencia
```

### Paso 2: Configurar variables de entorno

```bash
# Crear archivo .env
cp .env.example .env
nano .env  # Agregar API keys si las tienes
```

### Paso 3: Desplegar con Coolify

1. Acceder a Coolify: http://187.77.14.245:8000
2. Crear nuevo proyecto → "Docker Compose"
3. Conectar repositorio: https://github.com/imanovabot/ImaDash.git
4. Rama: `trendsPresidencia`
5. Coolify detectará `docker-compose.yml` automáticamente
6. Configurar variables de entorno en Coolify:
   - `YOUTUBE_API_KEY` (opcional)
   - `HUGGINGFACE_API_KEY` (opcional)
7. Deploy

### Paso 4: Configurar dominio

1. En Coolify, ir al servicio **frontend**
2. Dominios → Agregar `trends.imanova.co`
3. Coolify configurará automáticamente:
   - Proxy inverso (Nginx/Traefik)
   - Certificado SSL (Let's Encrypt)
   - Redirección HTTP → HTTPS

## 🔧 Opción B: Despliegue manual (sin Coolify)

### Usando Docker Compose directamente

```bash
# En el servidor
cd /data/ima/sites/trends-presidencia
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver estado
docker-compose ps
```

### Acceder

- **Frontend**: http://187.77.14.245:8080
- **Backend API**: http://187.77.14.245:8001
- **Docs API**: http://187.77.14.245:8001/docs

## 📝 Variables de entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `YOUTUBE_API_KEY` | API Key de YouTube Data API v3 | Opcional |
| `HUGGINGFACE_API_KEY` | API Key de HuggingFace Inference | Opcional |
| `PYTRENDS_LANGUAGE` | Idioma para Google Trends (default: es-CO) | No |
| `PYTRENDS_REGION` | Región para Google Trends (default: CO) | No |
| `CACHE_TTL_SECONDS` | Tiempo de cache en segundos (default: 21600 = 6h) | No |
| `NEWS_UPDATE_INTERVAL_MINUTES` | Intervalo de actualización de noticias (default: 30) | No |

## 🔍 Health Check

```bash
# Verificar que la API esté funcionando
curl http://localhost:8001/health

# Respuesta esperada:
# {
#   "status": "healthy",
#   "version": "0.1.0",
#   "timestamp": "2025-05-14T...",
#   "services": {
#     "google_trends": "ok",
#     "youtube": "ok" o "configure_youtube_api_key",
#     "sentiment": "ok",
#     "news": "ok"
#   }
# }
```

## 🛠️ Troubleshooting

### El frontend no conecta con el backend

Verificar CORS:
```bash
curl -H "Origin: http://trends.imanova.co" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://187.77.14.245:8001/health -v
```

### Google Trends no responde

pytrends puede ser bloqueado por Google. Soluciones:
- Usar proxies
- Implementar fallback a datos estáticos
- Verificar que no haya rate limits

### YouTube API no configurada

El endpoint `/health` mostrará `"youtube": "configure_youtube_api_key"`. Para habilitarlo:
1. Obtener API Key en Google Cloud Console
2. Configurar variable de entorno `YOUTUBE_API_KEY`

## 📊 Endpoints principales

| Endpoint | Descripción |
|----------|-------------|
| `GET /` | Información de la API |
| `GET /health` | Estado de servicios |
| `GET /api/v1/candidates` | Lista de candidatos (con métricas) |
| `GET /api/v1/candidates/{id}` | Detalle de candidato específico |
| `POST /api/v1/candidates/refresh` | Forzar actualización desde APIs |
| `GET /api/v1/news` | Noticias RSS relacionadas |
| `GET /api/v1/stats` | Estadísticas generales |

## 🔄 Actualizaciones

El backend refresca datos automáticamente cada 6 horas (configurable con `CACHE_TTL_SECONDS`). Para forzar actualización:

```bash
curl -X POST http://localhost:8001/api/v1/candidates/refresh
```

## 📈 Monitoreo

Coolify monitorea automáticamente:
- Estado de contenedores
- Uso de CPU/memoria
- Logs en tiempo real
- Health checks

Para ver logs:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```