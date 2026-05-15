# trendsPresidencia — Product Requirements Document

## Visión
trendsPresidencia es un dashboard de análisis de datos que mide el **"Momentum" o visibilidad digital** de candidatos presidenciales en Colombia, combinando tres fuentes:

1. **Google Trends (40%)** — Volumen de búsquedas (interés/curiosidad)
2. **YouTube (30%)** — Engagement: visualizaciones, likes, shares
3. **Sentimiento IA (30%)** — Análisis de comentarios en redes (positivo/negativo/neutro)

**NO es una encuesta de intención de voto**. Es un medidor de relevancia en el ecosistema digital.

## Principios

- **Read-Only**: Solo consume APIs, no modifica datos fuente
- **Transparencia**: Metodología visible y reproducible
- **Agregación**: Noticias vinculadas a métricas para contexto
- **Estático primero**: Funciona sin backend mientras sea posible
- **Actualización cíclica**: Datos refrescados cada N horas (configurable)

## Alcance

### Dentro del scope (trendsPresidencia visualiza)
1. **Ranking de candidatos** — Tabla con % momentum, cambio 24h, tendencias
2. **Desglose por fuente** — Barras separadas: Trends (40), YouTube (30), Sentimiento (30)
3. **Evolución temporal** — (futuro) gráfico de línea 7/30 días por candidato
4. **Sentimiento analysis** — Distribución positivo/negativo/neutro
5. **Feed de noticias** — Agregador RSS vinculado a picos de métricas
6. **Comparación** — (futuro) Vista side-by-side de 2-3 candidatos

### Fuera del scope (trendsPresidencia NO hace)
- ❌ Predecir resultados electorales
- ❌ Votación o encuestas de intención
- ❌ Modificar datos de Google/YouTube/redes
- ❌ Generar noticias (solo agregador)
- ❌ Análisis de TV/radio/medios tradicionales
- ❌ Perfiles demográficos de usuarios
- ❌ Backend complejo en v1.0

## Fuentes de datos (actuales y futuras)

|| Fuente | Tipo | endpoint/lectura | Ponderación | Estado ||
||--------|------|------------------|--------------|--------||
|| Google Trends | API REST (pytrends) | `pytrends.interest_over_time()` | 40% | 🔄 Futuro ||
|| YouTube Data API | API REST | `videos.list`, `commentThreads` | 30% | 🔄 Futuro ||
|| Comentarios redes | Scraping/API | Reddit/X/Instagram comments | 30% | 🔄 Futuro ||
|| Noticias | RSS/API | Medios colombianos (RSS) | Contexto | 🔄 Futuro ||
|| JSON local | Archivo estático | `data/candidates.json` | - | ✅ Actual ||

## User Personas

### 1. Analyst (Alejandro / equipo de campaña)
- **Necesita**: Ver quién lidera, detectar tendencias, correlacionar con eventos
- **Ve**: Dashboard con rankings + gráficos + feed de noticias
- **Acciones**: Filtrar por partido, comparar candidatos, exportar datos

### 2. Stakeholder (asesor/estratega)
- **Necesita**: Entender momentum general, identificar riesgos/oportunidades
- **Ve**: Resumen ejecutivo (top 3, cambios % diarios, sentimiento neto)
- **Acciones**: Configurar alertas (ej: "si candidato X sube 10% en 24h")

## Flujos de usuario

### Flujo A: Revisar ranking actual
1. Usuario abre `index.html` en navegador
2. Ve tabla: candidato | % total | Δ24h | iconos fuentes
3. Click en candidato → detalle: gráfico evolución + noticias
4. **Decisión**: Si hay pico → investigar noticias asociadas

### Flujo B: Búsqueda y filtrado
1. Usuario escribe nombre en buscador → lista filtra en tiempo real
2. Usuario selecciona partido en dropdown → lista se actualiza
3. Identifica candidato de interés
4. Click → detalle completo

### Flujo C: Análisis comparativo (futuro)
1. Usuario selecciona 2-3 candidatos (checkboxes)
2. Ve gráfico overlay: líneas de momentum paralelas
3. Identifica divergencias/convergencias
4. Exporta datos (CSV) para análisis externo

## Métricas de éxito (KPIs)

- **Actualización**: Datos refrescados cada 6h (default), <5 min lag cuando haya backend
- **Precisión**: Cálculo reproducible (método documentado)
- **Adopción**: >3 usuarios activos semanales (equipo)
- **Utilidad**: >80% de las preguntas de estrategia respondidas con el dashboard
- **Confiabilidad**: Uptime 99% (cuando esté en servidor)

## Tecnologías

### Frontend (actual)
- **HTML5** + **CSS3** (variables, grid, flexbox)
- **JavaScript** vanilla (ES6+, fetch API)
- Sin frameworks, sin build tools

### Frontend (futuro, opcional)
- React/Vue si se necesita SPA avanzada
- Chart.js / ECharts para gráficos interactivos
- Vite como build tool

### Backend (futuro, v1.0+)
- **FastAPI** (Python) — endpoints REST
- **Redis** — cache de métricas (6h TTL)
- **PostgreSQL** — histórico de métricas diarias
- **Celery/BackgroundTasks** — refresh automático

### APIs externas (futuro)
- `pytrends` (Google Trends no oficial)
- YouTube Data API v3 (clave de desarrollador)
- HuggingFace Inference API o modelo local (sentimiento)
- RSS parsers (noticias)

### Deploy (futuro)
- **Docker Compose** (backend + Redis + PostgreSQL)
- **Coolify** — orquestación en VPS
- **GitHub Pages / Netlify** — frontend estático (v0.4)

## Roadmap por fases

Ver [`docs/ROADMAP.md`](docs/ROADMAP.md) para detalle completo.

### Fase 0 — v0.1 (✅ Hecho)
- HTML estático + CSS + JS separados
- Datos en JSON local
- Búsqueda + filtro + detalle
- Responsive + tema oscuro

### Fase 1 — v0.2 (🔄 Próximo)
- Separación de archivos completada
- Guía de contribución
- Mejoras de accesibilidad

### Fase 2 — v0.3 (Planificado)
- Etiquetas, prioridad, fechas
- Ordenamiento de columnas
- Gráficos mini (canvas/SVG)
- Export CSV

### Fase 3 — v0.4 (Planificado)
- Favoritos en localStorage
- Vista comparativa
- Preparación para hosting estático

### Fase 4 — v1.0 (Futuro)
- Backend FastAPI + APIs reales
- Cache Redis
- Docker + Deploy en Coolify
- Actualización automática cada 6h

## Riesgos

|| Riesgo | Impacto | Mitigación ||
||--------|---------|------------||
|| Google Trends rate limit / ban | Alto | Cache 1h, throttling, usar VPN/proxy si es masivo ||
|| YouTube API quota (10k/día gratis) | Medio | Límite: 10 candidatos × 10 videos = 100 calls/día ||
|| Modelo sentimiento costoso (API paga) | Alto | Modelo local HuggingFace (distilbert) o thresholds simples ||
|| Noticias sin etiquetar (NLP imperfecto) | Medio | Validación manual inicial, regex con nombres conocidos ||
|| Datos inconsistentes entre fuentes | Medio | Normalizar a escala 0-100 por fuente antes de ponderar ||
|| Rate limits RSS | Bajo | Cache 1h, leer solo titulares ||

## Preguntas abiertas (Decisión necesaria)

1. **¿Modelo de sentimiento?**
   - Opción A: API OpenAI ($$$, preciso, fácil)
   - Opción B: Modelo local HuggingFace (gratis, menos preciso, requiere GPU/RAM)
   - Opción C: Heurística simple (palabras positivas/negativas en español)

2. **¿Frecuencia de actualización definitiva?**
   - Cada 6 horas (default, bajo costo)
   - Cada 1 hora (más costoso en APIs)
   - On-demand (solo cuando usuario refresca)

3. **¿Persistencia histórica?**
   - Solo Redis (últimas 24-48h) → suficiente para MVP
   - PostgreSQL histórico → necesario para gráficos 30 días
   - Archivos JSON diarios → backup simple

4. **¿Fuentes de noticias?**
   - RSS de 5-10 medios colombianos (El Tiempo, Semana, Blu, Caracol, RCN)
   - API GNews (gratis limitado, 100req/día)
   - Scraping custom (más trabajo, más control)

5. **¿Número de candidatos?**
   - Fijo: top 5-8 (definido manualmente)
   - Dinámico: detectar nuevos nombres automáticamente (NLP en noticias)

---

## Anexos

- Google Trends unofficial API: https://github.com/GeneralMills/pytrends
- YouTube Data API v3: https://developers.google.com/youtube/v3
- Sentimiento español: `cardiffnlp/twitter-roberta-base-sentiment` (HuggingFace)
- RSS ejemplos Colombia:
  - El Tiempo: https://www.eltiempo.com/rss/
  - Semana: https://www.semana.com/rss
  - Blu Radio: https://bluradio.com/colombia/noticias/rss
