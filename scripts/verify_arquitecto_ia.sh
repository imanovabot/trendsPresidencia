#!/bin/bash
# Verificación de estado del Arquitecto IA

echo "🔍 VERIFICANDO ESTADO DEL ARQUITECTO IA"
echo "========================================"
echo ""

# 1. Verificar skills
echo "📚 Skills:"
if [ -f "/opt/data/skills/devops/arquitecto-ia-investigador/SKILL.md" ]; then
    echo "  ✓ Investigador: OK"
    LAST_UPDATE=$(grep -m1 'Actualización Automática' /opt/data/skills/devops/arquitecto-ia-investigador/SKILL.md | head -1 | sed 's/^[[:space:]]*//')
    echo "    $LAST_UPDATE"
else
    echo "  ✗ Investigador: NO ENCONTRADO"
fi

if [ -f "/opt/data/skills/software-development/arquitecto-ia-codigo/SKILL.md" ]; then
    echo "  ✓ Código: OK"
else
    echo "  ✗ Código: NO ENCONTRADO"
fi

if [ -f "/opt/data/skills/software-development/arquitecto-ia-maestro/SKILL.md" ]; then
    echo "  ✓ Maestro: OK"
else
    echo "  ✗ Maestro: NO ENCONTRADO"
fi

# 2. Verificar reportes
echo ""
echo "📄 Últimos reportes:"
ls -lt /workspace/knowledge_base/reporte_*.md 2>/dev/null | head -5 | awk '{print "  "$NF" ("$5" "$6" "$7")"}'

# 3. Verificar cron
echo ""
echo "⏰ Cron job:"
if crontab -l 2>/dev/null | grep -q "arquitecto_investigador"; then
    echo "  ✓ Configurado:"
    crontab -l 2>/dev/null | grep "arquitecto_investigador" | sed 's/^/    /'
else
    echo "  ✗ No configurado"
    echo "    Ejecuta: crontab /workspace/cron/arquitecto_ia.cron"
fi

# 4. Verificar logs de hoy
echo ""
echo "📋 Logs de hoy:"
TODAY=$(date +%Y-%m-%d)
LOG_FILE="/workspace/logs/arquitecto_${TODAY}.log"
if [ -f "$LOG_FILE" ]; then
    echo "  ✓ Existe: $LOG_FILE"
    echo "  Tamaño: $(du -h "$LOG_FILE" | cut -f1)"
    echo "  Últimas líneas:"
    tail -3 "$LOG_FILE" | sed 's/^/    /'
else
    echo "  ⚠ No hay logs de hoy (ejecución manual pendiente)"
fi

# 5. Verificar script
echo ""
echo "🔧 Script investigador:"
if [ -x "/workspace/scripts/arquitecto_investigador.py" ]; then
    echo "  ✓ Ejecutable: OK"
    echo "  Tamaño: $(du -h /workspace/scripts/arquitecto_investigador.py | cut -f1)"
else
    echo "  ✗ No ejecutable o no existe"
fi

# 6. Servicios Docker
echo ""
echo "🐳 Contenedores (Qdrant/Redis):"
docker ps --filter "name=qdrant" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | tail -n +2 | sed 's/^/    /'
docker ps --filter "name=redis" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | tail -n +2 | sed 's/^/    /'

echo ""
echo "================================"
echo "✅ Verificación completada"
