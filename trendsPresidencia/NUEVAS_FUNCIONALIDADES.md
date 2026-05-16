# 🆕 Nuevas Funcionalidades - v0.2

## Botón de Refrescar (Frontend)

### ¿Qué hace?
El botón **"🔄 Refrescar"** permite actualizar los datos manualmente desde las APIs externas.

### Características
- ✅ Muestra estado de carga mientras actualiza
- ✅ Deshabilitado durante la actualización (previene doble clic)
- ✅ Notificación visual de éxito/error
- ✅ Recarga la lista de candidatos automáticamente

### Ubicación
Se encuentra en la barra de controles, junto al buscador y filtro de categoría.

### Comportamiento
1. Al hacer clic, envía una petición POST a `/api/v1/candidates/refresh`
2. El backend consulta todas las APIs configuradas
3. Los nuevos datos se guardan en `candidates.json`
4. El frontend recarga la lista automáticamente
5. Muestra una notificación con el resultado

---

## Auto-Refresh (Backend)

### ¿Qué hace?
Actualiza los datos **automáticamente cada 30 minutos** (configurable) sin intervención del usuario.

### Configuración

Variables de entorno en `.env` o `docker-compose.yml`:

```bash
# Habilitar/deshabilitar auto-refresh
AUTO_REFRESH_ENABLED=true

# Intervalo en minutos
AUTO_REFRESH_INTERVAL_MINUTES=30
```

### Características
- ✅ Se ejecuta en segundo plano (no bloquea la API)
- ✅ Inicia automáticamente al arrancar el servidor
- ✅ Logs detallados de cada ciclo
- ✅ Manejo de errores (no se detiene si una fuente falla)
- ✅ Actualiza: Google Trends, YouTube, Sentimiento

### Fuentes que se actualizan
| Fuente | Estado |
|--------|--------|
| Google Trends | ✅ Incluido |
| YouTube | ✅ Incluido |
| Sentimiento (IA) | ✅ Incluido |
| TikTok | ⚠️ Requiere API key |
| X/Twitter | ⚠️ Requiere Bearer Token |
| Instagram | ⚠️ Requiere Access Token |
| Noticias RSS | ✅ Incluido |

### Logs
```
⏰ Iniciando refresco automático de datos (cada 30 min)...
✅ Refresco automático completado: {
  'google_trends': 'ok',
  'youtube': 'ok',
  'sentiment': 'ok'
}
```

---

## Endpoints API

### POST /api/v1/candidates/refresh
Fuerza actualización manual de datos.

**Request:**
```bash
curl -X POST http://localhost:8001/api/v1/candidates/refresh
```

**Response:**
```json
{
  "refreshed": 4,
  "candidates": ["Abelardo de la Espriella", "Iván Cepeda", ...],
  "results": {
    "google_trends": {"Abelardo de la Espriella": 85.2, ...},
    "youtube": {"Abelardo de la Espriella": 45.0, ...},
    "sentiment": {"Abelardo de la Espriella": {"positive": 65.0, ...}, ...}
  },
  "timestamp": "2026-05-15T15:30:00"
}
```

### GET /api/v1/candidates?refresh=true
Alternativa para forzar refresh desde el frontend.

---

## Despliegue

### Docker
```bash
docker-compose up -d
```

El auto-refresh se activa automáticamente. Para desactivarlo:
```bash
docker-compose up -d -e AUTO_REFRESH_ENABLED=false
```

### Desarrollo
```bash
uvicorn main:app --reload
```

El auto-refresh también funciona en modo desarrollo.

---

## Notas Técnicas

- La tarea de background usa `asyncio.create_task()` de FastAPI
- El intervalo se respeta incluso si el refresh anterior tarda más
- Los errores se capturan y logean sin detener el ciclo
- Los datos se guardan en `data/candidates.json` después de cada refresh
- El frontend no necesita cambios para funcionar con auto-refresh
