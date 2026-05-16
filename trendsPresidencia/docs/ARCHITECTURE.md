# Arquitectura — trendsPresidencia

## Decisión actual
La primera versión es **100% estática**: un solo HTML que carga CSS y JS externos, y lee datos desde un archivo JSON. Esto permite validar:
- Diseño y UX
- Lógica de filtrado y búsqueda
- Visualización de métricas
- Metodología de cálculo

No requiere servidor, base de datos ni instalación. Solo abres `index.html` en el navegador.

## Capas

### Presentación
- **Archivo**: `index.html`
- **Responsabilidad**: Estructura semántica, contenedores, modales.
- **Tecnología**: HTML5, sin frameworks.

### Estilos
- **Archivo**: `src/styles.css`
- **Responsabilidad**: Tema, layout, responsividad, colores por candidato.
- **Tecnología**: CSS3 con variables custom (`:root`), grid/flexbox.

### Lógica
- **Archivo**: `src/app.js`
- **Responsabilidad**:
  - Cargar `candidates.json`
  - Filtrar/buscar candidatos
  - Renderizar lista y detalle
  - Manejar interacciones (click, select, modal)
- **Tecnología**: Vanilla JavaScript (ES6+), `fetch()`, `DOM API`.

### Datos
- **Ubicación**: `data/candidates.json`
- **Responsabilidad**: Almacenar métricas de candidatos (estructura fija).
- **Formato**: JSON con schema definido.

## Evolución recomendada

### Fase 1 — Backend ligero (v0.4 → v1.0)
Cuando se necesiten datos reales y automáticos:

```text
backend/
  main.py                 # FastAPI app
  services/
    trends_service.py     # Google Trends via pytrends
    youtube_service.py    # YouTube Data API
    sentiment_service.py  # HuggingFace model / OpenAI
    news_service.py       # RSS parser
  models/
    candidate.py          # Pydantic models
  cache/
    redis_client.py       # Cache de métricas
  config.py
docker-compose.yml
```

Frontend se mantiene igual (HTML+JS) consumiendo endpoints REST:
- `GET /api/candidates` — lista con métricas actualizadas
- `GET /api/candidate/{id}` — detalle + noticias
- `GET /api/history/{id}?days=7` — evolución temporal

### Fase 2 — Desacople frontend (v1.2+)
Separar frontend en su propio repo/proyecto:
- React/Vue/Svelte (opcional)
- O mantener vanilla JS pero en repo separado
- API como servicio independiente

### Fase 3 — Persistencia histórica (v1.5+)
- PostgreSQL para almacenar métricas diarias
- Grafana/Prometheus para monitoreo interno
- Alertas (Telegram/email) si candidato sube/baja 15%

## Principios

1. **Simplicidad primero** — Evitar dependencias hasta necesidad real.
2. **Static-first** — Que funcione sin backend el mayor tiempo posible.
3. **API-first design** — Aunque ahora sea JSON local, diseñar estructura pensando en endpoints futuros.
4. **Cache-aware** — Cuando haya APIs reales, implementar cache Redis agresivo (1-6h).
5. **Read-Only** — Nunca modificar fuentes externas (Google, YouTube, Twitter).

## Flujo de Datos (actual)

```text
candidates.json → fetch() → app.js → render List + Detail
                    ↓
              Búsqueda/Filtrado (en memoria)
                    ↓
              Selección → render Detail Panel
```

## Flujo de Datos (futuro con backend)

```text
[APIs externas]
    ↓
[FastAPI Service] → Redis Cache (6h)
    ↓
[Frontend] ← GET /api/candidates
    ↓
Render + Interacción
```

## Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| API rate limits (Google/YouTube) | Alto | Cache agresivo, throttling, fallback a datos antiguos |
| Modelo de sentimiento lento/costoso | Medio | Batch processing nocturno, modelo local ligero |
| Noticias sin categorizar | Medio | NLP básico + validación manual inicial |
| Escalabilidad de JSON estático | Alto | Migrar a DB cuando >50 candidatos o métricas históricas |
| Dependencia de APIs no oficiales (pytrends) | Alto | Tener Plan B: scraping alternativo o datos manuales |

## Preguntas abiertas

1. **¿Cuándo migrar a backend?** → Cuando se requiera actualización automática (<6h)
2. **¿Backend en mismo repo o separado?** → Mismo repo hasta v1.0, luego separar.
3. **¿Autenticación necesaria?** → Probablemente no (dashboard de lectura pública), pero considerar si se exponen APIs.
4. **¿Histórico necesario?** → Sí, para gráficos de evolución. PostgreSQL inevitable.

---

**Última actualización**: 2026-05-13 — Arquitectura estática validada.
