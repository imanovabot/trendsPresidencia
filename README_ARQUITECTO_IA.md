# 🏗️ Arquitecto IA - Sistema Completo

## 📋 Descripción

Sistema autónomo de **investigación y código** para arquitecturas de software e IA:

- **🔍 Investigador Automático**: Cada mañana 6:00 AM escanea ArXiv, GitHub, Papers With Code
- **💻 Código Implementable**: Ejemplos completos listos para producción (RAG, Agents, MLOps)
- **📚 Skill Dinámico**: Knowledge base que se actualiza automáticamente

---

## 🚀 Quick Start (3 pasos)

### 1. Ejecutar setup

```bash
bash /workspace/scripts/setup_arquitecto_ia.sh
```

### 2. Iniciar servicios (opcional, para RAG completo)

```bash
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant:latest
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### 3. Verificar

```bash
bash /workspace/scripts/verify_arquitecto_ia.sh
```

---

## 📁 Estructura del Proyecto

```
/workspace/
├── scripts/
│   ├── arquitecto_investigador.py    # Agente investigador (6 AM)
│   ├── setup_arquitecto_ia.sh        # Setup inicial
│   └── verify_arquitecto_ia.sh       # Verificación de estado
├── knowledge_base/
│   ├── reporte_2025-05-08.md        # Reportes generados
│   ├── investigacion_2025-05-08.json
│   └── archived/                     # Histórico
├── logs/
│   └── arquitecto_2025-05-08.log    # Logs del agente
├── cron/
│   └── arquitecto_ia.cron           # Configuración cron
└── skills/                          # Skills de Hermes (actualizados)
    ├── arquitecto-ia-investigador/  # Skill investigador
    ├── arquitecto-ia-codigo/         # Skill código
    └── arquitecto-ia-maestro/        # Skill integrador
```

---

## 🎯 Comandos Principales

### Investigación

```bash
# Ejecutar investigador manualmente
python3 /workspace/scripts/arquitecto_investigador.py

# Ver último reporte
cat /workspace/knowledge_base/reporte_$(date +%Y-%m-%d).md

# Ver logs
tail -f /workspace/logs/arquitecto_$(date +%Y-%m-%d).log

# Ver skill actualizado
tail -n 50 /opt/data/skills/devops/arquitecto-ia-investigador/SKILL.md
```

### Verificación

```bash
# Estado completo del sistema
bash /workspace/scripts/verify_arquitecto_ia.sh

# Verificar cron
crontab -l

# Probar API (si está corriendo)
curl http://localhost:8000/health
```

---

## ⚙️ Configuración

### Variables de Entorno

```bash
# .env (para RAG API)
OPENAI_API_KEY=sk-...
VECTOR_DB_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
```

### Modificar Horario del Cron

```bash
crontab -e
# Cambiar "0 6 * * *" a la hora deseada
```

---

## 📊 Flujo Diario

```
6:00 AM → Cron ejecuta investigador
         ↓
6:05 AM → Busca en 3 fuentes (ArXiv, GitHub, PwC)
         ↓
6:15 AM → Analiza tendencias, frameworks, patrones
         ↓
6:20 AM → Genera reporte Markdown + JSON
         ↓
6:25 AM → Actualiza SKILL.md con nueva sección
         ↓
6:30 AM → FIN → Skill siempre al día
```

---

## 🔧 Troubleshooting

### El cron no ejecuta

```bash
# Verificar que cron está corriendo
sudo systemctl status cron

# Ver logs
sudo grep CRON /var/log/syslog

# Probar manualmente
python3 /workspace/scripts/arquitecto_investigador.py
```

### Skill no actualizado

```bash
# Verificar ruta del skill
ls /opt/data/skills/devops/arquitecto-ia-investigador/

# Si no existe, copiar manualmente:
mkdir -p /opt/data/skills/devops/
# Copiar skill desde /workspace/skills/
```

### Error de rate limit GitHub

Es normal (60 req/hora). El script maneja el error y continúa.

---

## 📚 Skills Creados

| Skill | Descripción | Ruta |
|-------|-------------|------|
| `arquitecto-ia-investigador` | Agente investigador (6 AM) | `/opt/data/skills/devops/` |
| `arquitecto-ia-codigo` | Código implementable | `/opt/data/skills/software-development/` |
| `arquitecto-ia-maestro` | Vista integradora | `/opt/data/skills/software-development/` |

---

## 🎓 Casos de Uso

1. **¿Qué investigó hoy?** → `tail -n 50 /opt/data/skills/devops/arquitecto-ia-investigador/SKILL.md`
2. **¿Cómo implementar RAG?** → Consultar skill `arquitecto-ia-codigo`
3. **¿Qué frameworks nuevos hay?** → Buscar "Frameworks detectados" en el skill
4. **¿Cuándo se ejecutó?** → `ls -lt /workspace/logs/arquitecto_*.log`

---

## 📈 Métricas

- **Fuentes monitoreadas**: 3 (ArXiv, GitHub, Papers With Code)
- **Artículos/día**: 10-50 promedio
- **Latencia**: ~30 segundos
- **Skill actualizado**: Diariamente 6:25 AM

---

## 🐛 Issues

Si algo falla:

1. Revisar logs: `tail -f /workspace/logs/arquitecto_*.log`
2. Ejecutar manualmente: `python3 /workspace/scripts/arquitecto_investigador.py`
3. Verificar skill: `ls /opt/data/skills/devops/arquitecto-ia-investigador/`
4. Abrir issue en repositorio (si aplica)

---

**Versión**: 1.0.0
**Estado**: ✅ Producción Ready
**Modo**: YOLO (sin preguntas, ejecución directa)
