#!/bin/bash
# Script para configurar DNS de trends.imanova.co
# Ejecutar en el servidor DNS (dns-parking.com)

# Opción 1: Usar API de dns-parking.com (requiere credenciales)
# curl -X POST "https://api.dns-parking.com/v1/domains/imanova.co/records" #   -H "Authorization: Bearer YOUR_API_KEY" #   -H "Content-Type: application/json" #   -d '{"type":"A","name":"trends","value":"187.77.14.245","ttl":3600}'

# Opción 2: Configuración manual en el panel de dns-parking.com
# 1. Login en https://dns-parking.com
# 2. Seleccionar dominio imanova.co
# 3. Agregar registro A: trends → 187.77.14.245
# 4. TTL: 3600
# 5. Guardar

echo "Configuración DNS pendiente: trends.imanova.co → 187.77.14.245"
