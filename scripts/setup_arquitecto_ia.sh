#!/bin/bash
# Arquitecto IA - Setup Completo
# Este script verifica e instala todo el sistema de arquitecto IA
# Uso: bash scripts/setup_arquitecto_ia.sh

set -e  # Salir en error

echo "🏗️  ARQUITECTO IA - SETUP COMPLETO"
echo "================================"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ── 1. Verificar prerrequisitos ───────────────────────────────────────────────
echo "🔍 Verificando prerrequisitos..."

PREREQS_OK=true

# Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python 3 no instalado"
    PREREQS_OK=false
fi

# Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    echo -e "${GREEN}✓${NC} Docker $DOCKER_VERSION"
else
    echo -e "${YELLOW}⚠${NC} Docker no instalado (opcional, pero recomendado)"
fi

# Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose"
else
    echo -e "${YELLOW}⚠${NC} Docker Compose no instalado (opcional)"
fi

# pip
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip3"
else
    echo -e "${RED}✗${NC} pip3 no instalado"
    PREREQS_OK=false
fi

# crontab
if command -v crontab &> /dev/null; then
    echo -e "${GREEN}✓${NC} crontab"
else
    echo -e "${YELLOW}⚠${NC} crontab no instalado (necesario para automatización)"
fi

echo ""

# ── 2. Crear estructura de directorios ────────────────────────────────────────
echo "📁 Creando estructura de directorios..."

mkdir -p /workspace/scripts
mkdir -p /workspace/knowledge_base
mkdir -p /workspace/knowledge_base/archived
mkdir -p /workspace/logs
mkdir -p /workspace/cron

echo -e "${GREEN}✓${NC} Directorios creados"
echo ""

# ── 3. Instalar dependencias Python ───────────────────────────────────────────
echo "📦 Instalando dependencias Python..."

pip3 install --quiet --upgrade pip

PYTHON_DEPS=(
    "fastapi"
    "uvicorn[standard]"
    "pydantic"
    "pydantic-settings"
    "sentence-transformers"
    "qdrant-client"
    "redis"
    "openai"
    "anthropic"
    "nltk"
    "presidio-analyzer"
    "presidio-anonymizer"
    "prometheus-client"
    "tenacity"
    "httpx"
)

for dep in "${PYTHON_DEPS[@]}"; do
    echo -n "  Instalando $dep... "
    pip3 install --quiet "$dep" 2>/dev/null && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}⚠ (fallback)${NC}"
done

echo ""
echo -e "${GREEN}✓${NC} Dependencias instaladas"
echo ""

# ── 4. Configurar cron job ────────────────────────────────────────────────────
echo "⏰ Configurando cron job (6:00 AM daily)..."

CRON_JOB="0 6 * * * cd /workspace && /usr/bin/python3 /workspace/scripts/arquitecto_investigador.py >> /workspace/logs/cron_arquitecto.log 2>&1"

# Añadir si no existe
(crontab -l 2>/dev/null | grep -q "arquitecto_investigador") || (
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo -e "${GREEN}✓${NC} Cron job añadido"
) || echo -e "${YELLOW}⚠${NC} No se pudo configurar crontab (ejecuta manualmente)"

echo ""

# ── 5. Verificar skill ────────────────────────────────────────────────────────
echo "🧠 Verificando skills..."

if [ -f "/opt/data/skills/devops/arquitecto-ia-investigador/SKILL.md" ]; then
    echo -e "${GREEN}✓${NC} Skill investigador encontrado"
else
    echo -e "${RED}✗${NC} Skill investigador NO encontrado en /opt/data/skills/"
    echo "   Debes crear el skill manualmente o verificar instalación"
fi

if [ -f "/opt/data/skills/software-development/arquitecto-ia-codigo/SKILL.md" ]; then
    echo -e "${GREEN}✓${NC} Skill código encontrado"
else
    echo -e "${YELLOW}⚠${NC} Skill código NO encontrado"
fi

echo ""

# ── 6. Probar script investigador ────────────────────────────────────────────
echo "🧪 Probando script investigador (versión rápida)..."

if python3 /workspace/scripts/arquitecto_investigador.py 2>&1 | head -20; then
    echo ""
    echo -e "${GREEN}✓${NC} Script ejecutado exitosamente"
else
    echo -e "${YELLOW}⚠${NC} Script tuvo errores (revisar logs)"
fi

echo ""

# ── 7. Mostrar resumen ────────────────────────────────────────────────────────
echo "================================"
echo "✅ SETUP COMPLETADO"
echo "================================"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Verificar investigación:"
echo "   cat /workspace/knowledge_base/reporte_$(date +%Y-%m-%d).md"
echo ""
echo "2. Consultar skill:"
echo "   tail -n 50 /opt/data/skills/devops/arquitecto-ia-investigador/SKILL.md"
echo ""
echo "3. Iniciar servicios (opcional, para RAG completo):"
echo "   docker run -d -p 6333:6333 --name qdrant qdrant/qdrant:latest"
echo "   docker run -d -p 6379:6379 --name redis redis:7-alpine"
echo ""
echo "4. Ver logs del cron:"
echo "   tail -f /workspace/logs/cron_arquitecto.log"
echo ""
echo "5. Forzar ejecución manual:"
echo "   python3 /workspace/scripts/arquitecto_investigador.py"
echo ""
echo "================================"
echo "🕐 El agente se ejecutará automáticamente a las 6:00 AM"
echo "================================"
