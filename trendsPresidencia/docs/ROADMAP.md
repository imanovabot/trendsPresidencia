# Roadmap — trendsPresidencia

## Version 0.1 - Base funcional (✅ COMPLETADO)
**Estado**: Completado

- Página HTML estática funcional.
- Datos de ejemplo en `candidates.json`.
- Búsqueda local por nombre/partido/descripción.
- Filtro por categoría (partido).
- Lista de candidatos con métricas resumidas.
- Panel de detalle con desglose por fuente.
- Estado vacío cuando no hay resultados.
- Diseño responsive móvil y escritorio.
- Tema oscuro con variables CSS.
- Documentación inicial (README, PRD, ARCHITECTURE).

## Version 0.2 - Orden del proyecto (🔄 SIGUIENTE)
**Estado**: Próximo

**Objetivo**: Separar responsabilidades y preparar para crecimiento.

- [ ] Mover todo JS a `src/app.js` (hecho en v0.1)
- [ ] Mover todo CSS a `src/styles.css` (hecho en v0.1)
- [ ] Mover datos a `data/candidates.json` (hecho en v0.1)
- [ ] Crear guía de contribución: cómo agregar candidatos
- [ ] Mejorar accesibilidad (teclado, ARIA labels)
- [ ] Agregar tests básicos (Jest/Playwright) — opcional
- [ ] Validar en múltiples navegadores

**Criterio de éxito**: Archivos separados, repo ordenado, guía clara.

## Version 0.3 - Curaduría y enriquecimiento
**Estado**: Planificado

**Objetivo**: Mejorar calidad de datos y usabilidad.

- [ ] Agregar etiquetas a candidatos (ej: "independiente", " Coalición", "Uribismo")
- [ ] Agregar nivel de impacto o prioridad (alta/media/baja)
- [ ] Agregar fecha de última actualización por candidato
- [ ] Agregar ordenamiento (por momentum, por cambio 24h, por nombre)
- [ ] Mostrar gráfico mini de evolución (canvas simple o SVG)
- [ ] Exportar datos a CSV (botón)
- [ ] Modo claro/oscuro toggle

**Criterio de éxito**: Dashboard útil para análisis diario.

## Version 0.4 - Producto
**Estado**: Planificado

**Objetivo**: Funcionalidades de usuario y preparación para publicación.

- [ ] Guardar favoritos en `localStorage`
- [ ] Vista comparativa (2-3 candidatos en un mismo gráfico)
- [ ] Compartir enlace con filtros aplicados (URL params)
- [ ] Preparar estructura para publicar en GitHub Pages, Netlify o Vercel
- [ ] Agregar meta tags OG para redes sociales
- [ ] PWA básica (manifest, icons, offline)

**Criterio de éxito**: Se puede publicar en un hosting estático y usuarios pueden comparar candidatos.

## Version 1.0 - App estable
**Estado**: Futuro

**Objetivo**: Datos reales + automatización.

- [ ] Conectar a Google Trends (pytrends) — backend Python
- [ ] Conectar a YouTube Data API (métricas reales)
- [ ] Implementar modelo de sentimiento (HuggingFace local o API)
- [ ] Agregar feed de noticias (RSS parser + NLP para extraer candidatos)
- [ ] Backend FastAPI para agregación y cache
- [ ] Dockerizar (backend + frontend estático)
- [ ] Deploy en Coolify/VPS
- [ ] API REST pública (`/api/momentum`)
- [ ] Autenticación básica (si se necesita privacidad)
- [ ] Tests automatizados (backend + frontend)
- [ ] Monitoreo (Prometheus/Grafana)

**Criterio de éxito**: Datos automáticos, actualizados cada 6h, desplegado en producción.

## Version 1.5 - Escala
**Estado**: Futuro

- [ ] Histórico en PostgreSQL (métricas diarias por candidato)
- [ ] Gráficos interactivos con Chart.js o ECharts
- [ ] Alertas por Telegram/email (umbrales configurables)
- [ ] Multi-país (adaptar a otras elecciones)
- [ ] API versionada (v1, v2)
- [ ] Documentación técnica completa (OpenAPI)

## Version 2.0 - Plataforma
**Estado**: Futuro

- [ ] Múltiples elecciones simultáneas
- [ ] Panel de administración (agregar candidatos manual)
- [ ] Dashboard interactivo con filtros avanzados
- [ ] Exportación avanzada (PDF, Excel)
- [ ] Integración con WhatsApp (bot de consultas)
- [ ] Modelo predictivo (regresión vs encuestas reales)

---

## Notas

- **Cada versión debe ser desplegable** (ninguna debe ser "solo código").
- **Backward compatible** — La API JSON debe mantener compatibilidad.
- **Documentar cambios** en `CHANGELOG.md` después de cada release.
- **Taggear** en git: `v0.1.0`, `v0.2.0`, etc.
