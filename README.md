# trendsPresidencia

Dashboard de análisis de **Momentum Digital** para candidatos presidenciales en Colombia 2026.

> ⚠️ **Aclaración importante**: Esto **NO es una encuesta de intención de voto**. Es un medidor de visibilidad en el ecosistema digital que combina Google Trends, engagement en YouTube y análisis de sentimiento con IA.

## 🚀 Inicio Rápido

**No requiere instalación ni servidor.** Solo abre `index.html` en tu navegador:

```bash
# Desde la terminal
open trendsPresidencia/index.html
# o
xdg-open trendsPresidencia/index.html
# o doble clic en el archivo
```

La página funciona 100% estática, cargando datos desde `data/candidates.json`.

## 📊 Metodología

El **Momentum Score** se calcula como un promedio ponderado:

| Fuente | Peso | Descripción |
|--------|------|-------------|
| Google Trends | 40% | Volumen de búsquedas (interés/curiosidad) |
| YouTube | 30% | Visualizaciones, likes, shares de videos |
| Sentimiento IA | 30% | Análisis de comentarios (positivo/negativo/neutro) |

Cada fuente se normaliza a escala 0-100 antes de promediar.

## 📁 Estructura del Proyecto

```text
trendsPresidencia/
  index.html           # App principal (carga CSS + JS)
  data/
    candidates.json    # Datos de candidatos (editable)
  src/
    styles.css         # Estilos (tema oscuro/claro)
    app.js            # Lógica: búsqueda, filtrado, detalle
  docs/
    PRD.md            # Requerimientos del producto
    ARCHITECTURE.md   # Decisiones técnicas
    ROADMAP.md        # Plan de fases
    CHANGELOG.md      # Historial de cambios
  README.md
```

## 🎯 Funcionalidades (v0.1)

- ✅ Lista de candidatos con métricas en tiempo real
- ✅ Búsqueda por nombre, partido o descripción
- ✅ Filtro por categoría (partido político)
- ✅ Panel de detalle con:
  - Desglose por fuente (Trends/YouTube/Sentimiento)
  - Barras de progreso normalizadas
  - Distribución de sentimiento
  - Noticias relevantes vinculadas
- ✅ Diseño responsive (móvil + escritorio)
- ✅ Tema oscuro por defecto (soporte tema claro)

## 🔧 Personalización

### Agregar/editar candidatos

Edita `data/candidates.json`:

```json
{
  "id": "nuevo-candidato",
  "name": "Nombre Completo",
  "party": "Partido Político",
  "momentum": 25.5,
  "change_24h": 1.2,
  "sources": {
    "google_trends": 80,
    "youtube": 60,
    "sentiment": 45.5
  },
  "sentiment_breakdown": {
    "positive": 60,
    "neutral": 25,
    "negative": 15
  },
  "top_news": ["Noticia 1", "Noticia 2"],
  "description": "Breve descripción del candidato",
  "color": "#8b5cf6"
}
```

### Cambiar pesos de la fórmula

En `data/candidates.json`, modificar `weights`:

```json
"weights": {
  "google_trends": 0.40,   // 40%
  "youtube": 0.30,         // 30%
  "sentiment": 0.30        // 30%
}
```

### Modificar frecuencia de actualización

Cambiar `update_frequency_hours` en el JSON.

## 📈 Roadmap

Ver [`docs/ROADMAP.md`](docs/ROADMAP.md) para el plan detallado de fases:

- **v0.1** (actual) — MVP estático
- **v0.2** — Separar CSS/JS, mover datos a JSON
- **v0.3** — Curaduría: etiquetas, prioridad, fechas
- **v0.4** — Favoritos, exportación, vista comparativa
- **v1.0+** — Backend FastAPI + APIs reales + deploy Coolify

## 🛠️ Stack Tecnológico

- **Frontend**: HTML5, CSS3, JavaScript (vanilla, sin frameworks)
- **Datos**: JSON estático
- **Deploy (futuro)**: Docker + Coolify
- **Backend (futuro)**: FastAPI + Python
- **APIs externas (futuro)**: Google Trends, YouTube Data API, HuggingFace

## ⚠️ Limitaciones Actuales

- Datos embebidos (manuales, no automáticos)
- Sin conexión a APIs reales (por ahora)
- Sin persistencia (favoritos no guardan)
- Sin autenticación
- Actualización manual de JSON

## 📄 Licencia

Uso educativo y de análisis. No redistribuir como producto electoral.

---

**Estado**: v0.1.0 — Funcional, estático, listo para usar.
