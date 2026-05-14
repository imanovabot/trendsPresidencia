# Changelog

Todos los cambios significativos se documentan aquí.

## [0.1.0] - 2026-05-13

### Agregado
- Página `index.html` funcional sin dependencias externas.
- Datos en `data/candidates.json` con 4 candidatos de ejemplo.
- Búsqueda local en tiempo real por nombre, partido o descripción.
- Filtro por categoría (partido político).
- Lista de candidatos renderizada con JavaScript nativo.
- Panel de detalle con:
  - Desglose por fuente (Trends 40%, YouTube 30%, Sentimiento 30%)
  - Barras de progreso normalizadas
  - Distribución de sentimiento (positivo/neutral/negativo)
  - Sección de noticias relevantes
- Estado vacío cuando no hay resultados de búsqueda.
- Diseño responsive para móvil y escritorio.
- Tema oscuro con variables CSS (soporte futuro para tema claro).
- Modal con metodología de cálculo.
- Documentación inicial en `README.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`.

### Técnico
- Arquitectura de archivos separados (HTML/CSS/JS/JSON).
- Sin backend, sin framework, sin build, sin instalación.
- Código vanilla JS, compatible con todos los navegadores modernos.
- Fetch API para cargar JSON local (funciona desde file:// en la mayoría de navegadores).

### Corregido
- Ninguno por el momento.

### Eliminado
- Ninguno por el momento.

---

## [0.2.0] - Pendiente

### Planeado
- Separación completa de estilos y scripts (ya completado en v0.1).
- Mejorar accesibilidad (navegación por teclado, ARIA).
- Agregar guía de contribución (`CONTRIBUTING.md`).
- Tests básicos con Jest (unit) y Playwright (E2E).

---

**Formato**: Este archivo sigue [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).
Las versiones siguen [Semantic Versioning](https://semver.org/lang/es/).
