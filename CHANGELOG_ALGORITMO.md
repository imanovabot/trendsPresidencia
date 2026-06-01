# CHANGELOG — trendsPresidencia

## [0.2.0] — 2026-05-31

### 🎯 Implementación de Algoritmo de Predicción Electoral

**Basado en lecciones calibradas de elecciones Colombia 2022-2026**

#### Backend (FastAPI)

**Nuevo servicio: `prediction_engine.py`**
- Algoritmo de alineación con factores de corrección calibrados
- Factor de desinflado de opinión para candidatos de centro (40%)
- Multiplicador de estabilidad para voto duro (+5%)
- Promedio ponderado del día con ventana de máxima predictividad (12:00-16:00)
- Proyección de segunda vuelta con redistribución de votos de terceros
- Detección de ruido por shocks de audiencia (z-score > 2.5)

**Google Trends service mejorado**
- Soporte para "Temas" (Topics) en lugar de términos exactos — agrupa variantes ortográficas y apodos
- Detección de estabilidad de curva (desviación estándar horaria)
- Series horarias para análisis de ruido
- Ventana de tiempo configurable (default: `now 7-d`)
- Clasificación de consultas relacionadas: electorales vs. ruido

**Nuevos endpoints**
- `POST /api/v1/predictions/runoff` — Pronóstico de segunda vuelta
- `GET /api/v1/trends/related-queries/{candidate}` — Consultas relacionadas clasificadas
- `GET /api/v1/trends/regional/{candidate}` — Interés por departamentos/regiones
- `GET /api/v1/trends/noise-detection/{candidate}` — Detección de picos anómalos
- `GET /api/v1/trends/stability/{candidate}` — Estabilidad horaria del candidato

**Modificado**
- `GET /api/v1/candidates/{id}` — Ahora incluye análisis electoral avanzado en el detalle

#### Frontend (HTML/JS/CSS)

**Nueva sección "Análisis Electoral" en detalle de candidato**
- Indicador de estabilidad de curva (voto duro vs volátil)
- Alerta de ruido detectado con interpretación
- Consultas relacionadas con clasificación visual (electoral/ruido)
- Distribución regional por departamentos (top 5)
- Metadatos: `is_center_candidate`, `historical_stability`, `regional_distribution`

**Metodología actualizada**
- Modal explica ahora: uso de Topics, ventana de tiempo óptima, algoritmo de alineación
- Disclaimer reforzado: no es encuesta de intención de voto

**Estilos**
- Nuevas tarjetas de análisis electoral
- Barras de estabilidad con código de color (verde/amarillo/rojo)
- Etiquetas de consultas (electoral = morado, ruido = rojo tenue)
- Responsive para móvil

#### Datos

**candidates.json actualizado**
- Campos nuevos por candidato:
  - `historical_stability` (desviación estándar horaria)
  - `is_center_candidate` (booleano)
  - `topic_id` (ID de Google Trends Topic)
  - `regional_strength` (distribución por departamentos)
  - `base_support` (porcentaje de voto duro histórico)
  - `related_queries` (lista de búsquedas asociadas)

**Nuevo: `data/trends_config.json`**
- Configuración de Topics oficiales por candidato
- Ventanas de tiempo electorales
- Configuración de detección de ruido

#### Infraestructura

- **start.sh**: Corregido `cd /app/backend` para ejecutar correctamente uvicorn
- **nginx.conf**: Activado proxy a backend en `localhost:8001` con headers correctos
- **app.js**: Ahora usa rutas relativas `/api` (no detecta localhost)
- **Sincronización**: `frontend/html/src` ↔ `src/` mantenidos

---

## Próximos pasos sugeridos

1. **Probar en Coolify**: Verificar que el servicio se despliegue correctamente
2. **Verificar endpoints**: Probar `/health` y `/api/v1/candidates`
3. **Calibrar factores**: Ajustar `opinion_factor` y `stability_multiplier` con datos reales de la segunda vuelta
4. **Añadir histórico**: Implementar almacenamiento de series horarias para calcular estabilidad real
5. **Alertas**: Configurar notificaciones cuando se detecte ruido o cambios bruscos
