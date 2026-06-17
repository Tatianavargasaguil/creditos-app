#!/bin/bash

# Script de actualización rápida
# Uso: bash update.sh

echo "🔄 Actualizando aplicación..."
echo ""

# Ir a directorio del proyecto
cd /root/creditos

# 1. Pull del código
echo "📥 Descargando cambios..."
git pull origin main

# 2. Rebuild de imágenes
echo "🔨 Reconstruyendo imágenes..."
docker-compose -f docker-compose.prod.yml build

# 3. Reiniciar contenedores
echo "🔄 Reiniciando contenedores..."
docker-compose -f docker-compose.prod.yml up -d

# 4. Verificar estado
echo ""
echo "✅ Actualización completada!"
echo ""
echo "Estado actual:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "Logs (Ctrl+C para salir):"
docker-compose -f docker-compose.prod.yml logs -f
