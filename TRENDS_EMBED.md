# Google Trends Embed Oficial — Segunda Vuelta Colombia 2026

## 📊 ¿Qué es?

Componente que muestra el gráfico **oficial de Google Trends** directamente en la aplicación, usando la API de embedding pública de Google. No requiere API key, se carga directamente desde los servidores de Google.

## 🔧 Configuración utilizada

```javascript
{
  comparisonItem: [
    {
      keyword: "/g/11bwfmp95b",  // Abelardo de la Espriella (Topic ID oficial)
      geo: "CO",
      time: "now 7-d"             // Ventana de tiempo
    },
    {
      keyword: "/g/1q6jc4dr2",   // Iván Cepeda (Topic ID oficial)
      geo: "CO",
      time: "now 7-d"
    }
  ],
  category: 0,   // 0 = Todas las categorías
  property: "",  // "" = web
  exploreQuery: "date=now%207-d&geo=CO&q=%2Fg%2F11bwfmp95b,%2Fg%2F1q6jc4dr2"
}
```

## 📍 Ubicación en la app

El gráfico aparece en la **sección principal** de `index.html`, justo antes de la lista de candidatos:

```html
<section class="trends-embed-section">
    <div id="trends-second-round-container"></div>
    <div class="trends-timeframe-buttons">...</div>
</section>
```

## 🎯 Características

- ✅ **Topics en lugar de términos**: Usa IDs oficiales de Google Topics, agrupando variantes ortográficas y apodos
- ✅ **Timeframe configurable**: Botones para cambiar entre 24h, 7d, 12h, 4h
- ✅ **Auto-adaptable**: Se redimensiona con la ventana
- ✅ **Carga asíncrona**: No bloquea la página
- ✅ **Fallback**: Si falla, muestra enlace directo a Google Trends

## 🔄 Cambiar timeframe

La función `updateTrendsTimeframe(timeframe)` está disponible globalmente:

```javascript
// Ejemplos:
updateTrendsTimeframe('now 1-d');      // Últimas 24 horas
updateTrendsTimeframe('now 7-d');      // Últimos 7 días (default)
updateTrendsTimeframe('today 12-h');   // Últimas 12 horas
updateTrendsTimeframe('now 4-h');      // Últimas 4 horas
```

## 🎨 Estilos

Los estilos están en `src/styles.css` bajo la sección:

```css
/* GOOGLE TRENDS EMBED — SEGUNDA VUELTA */
.trends-embed-section { ... }
#trends-second-round-container { ... }
.trends-timeframe-buttons { ... }
```

## 📁 Archivos relacionados

- `frontend/html/index.html` — Integración principal
- `frontend/html/src/trends-embed-second-round.js` — Lógica del embed
- `frontend/html/second-round-trends.html` — Página independiente
- `frontend/html/trends-embed.html` — Componente reusable

## 🔍 Topic IDs oficiales

Estos IDs se obtienen de Google Trends cuando buscas un candidato y seleccionas **"Tema"** en el dropdown:

| Candidato | Topic ID | URL de verificación |
|-----------|----------|---------------------|
| Abelardo de la Espriella | `/g/11bwfmp95b` | https://trends.google.es/trends/explore?q=%2Fg%2F11bwfmp95b |
| Iván Cepeda | `/g/1q6jc4dr2` | https://trends.google.es/trends/explore?q=%2Fg%2F1q6jc4dr2 |

Para añadir más candidatos, busca su nombre en Google Trends, cambia a "Tema" y copia el `/g/...` de la URL.

## ⚠️ Limitaciones

- No requiere API key, pero depende del servicio de embedding de Google
- No se puede personalizar los colores (Google controla el diseño)
- El timeframe máximo es de 7 días para la versión gratuita
- Para períodos mayores, usar la API completa de Google Trends

## 📈 Ventana de tiempo electoral

- **now 7-d**: Tendencia estructural de la semana
- **now 1-d**: Impacto de eventos recientes (debates, noticias)
- **today 12-h**: Mediodía del día electoral (máxima predictividad)
- **now 4-h**: Última hora antes de cierre de urnas

## 🚀 Despliegue

No requiere cambios en el backend. Solo:

1. Los archivos JS/CSS se sirven estáticamente por nginx
2. El embed se carga desde `ssl.gstatic.com` (dominio de Google)
3. Funciona en cualquier despliegue (Coolify, Docker, etc.)
