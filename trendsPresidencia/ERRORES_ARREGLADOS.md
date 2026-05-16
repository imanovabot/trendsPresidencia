# Errores Arreglados - trendsPresidencia

## Fecha: 2026-05-15

### Frontend (src/app.js)

1. **Elemento inexistente #lastUpdate** (líneas 54-58)
   - Problema: El código buscaba un elemento `lastUpdate` que no existe en el HTML
   - Fix: Eliminado ese código y mantenido solo la actualización de `updateFreq`

2. **División innecesaria en sentimiento** (línea 265)
   - Problema: `(candidate.sources.sentiment / 100) * 100` — el sentimiento ya está en porcentaje 0-100
   - Fix: Usar directamente `candidate.sources.sentiment`

3. **Valor de sentimiento sin formato** (línea 306)
   - Problema: Mostraba número sin `%` y sin `toFixed`
   - Fix: Agregado `.toFixed(1)%` para mostrar con 1 decimal y el símbolo %

4. **Desestructuración sin validación** (línea 268)
   - Problema: `candidate.sentiment_breakdown` podía ser undefined
   - Fix: Agregado fallback `{ positive: 0, neutral: 0, negative: 0 }`

5. **Acceso directo a sources** (líneas 225-227)
   - Problema: Acceso directo a `candidate.sources.google_trends` podía fallar
   - Fix: Usar optional chaining `candidate.sources?.google_trends || 0`

### Backend (main.py)

6. **Cálculo de momentum inconsistente** (líneas 191-199)
   - Problema: Usaba pesos hardcodeados diferentes a los del JSON
   - Fix: Leer pesos desde `data["weights"]` y usar `.get()` con valores por defecto

7. **Mismo issue en endpoint /refresh** (líneas 327-334)
   - Problema: Pesos hardcodeados no coincidían con JSON
   - Fix: Usar misma lógica que endpoint principal

8. **Manejo de fuentes faltantes**
   - Problema: Acceso directo `c["sources"]["tiktok"]` fallaba si no existía
   - Fix: Usar `c["sources"].get("tiktok", 0)`

### Datos (data/candidates.json)

9. **Pesos actualizados a la versión completa**
   ```json
   {
     "google_trends": 0.30,
     "youtube": 0.20,
     "tiktok": 0.15,
     "x": 0.15,
     "instagram": 0.10,
     "sentiment": 0.10
   }
   ```

10. **Agregadas fuentes faltantes a todos los candidatos**
    - Agregados `tiktok: 0`, `x: 0`, `instagram: 0` a cada candidato

### Infraestructura

11. **Dockerfile inseguro**
    - Cambiado `--break-system-packages` por `--user`
    - Razón: Evitar corrupción del sistema de paquetes

### No arreglados (requieren acción manual)

- **Playwright sin navegador**: Necesita `playwright install chromium`
- **Sitio devuelve 403**: Restricción de acceso en el servidor
- **Falta API keys**: YouTube, TikTok, X, Instagram para datos reales

### Tests

- ✅ Backend: 14/14 tests pasan
- ⚠️ Frontend: 7/7 tests fallan por Playwright no instalado
