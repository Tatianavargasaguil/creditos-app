#!/bin/bash

# Script de Deployment para Hostinger VPS
# Uso: bash deploy.sh

set -e

echo "================================"
echo "🚀 Deployment Créditos - Hostinger"
echo "================================"
echo ""

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Actualizar sistema
echo -e "${BLUE}[1/7] Actualizando sistema...${NC}"
apt-get update && apt-get upgrade -y

# 2. Instalar dependencias
echo -e "${BLUE}[2/7] Instalando dependencias...${NC}"
apt-get install -y curl git nano

# 3. Verificar Docker
echo -e "${BLUE}[3/7] Verificando Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker no instalado, instalando...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo -e "${GREEN}✓ Docker ya instalado${NC}"
fi

# 4. Verificar Docker Compose
echo -e "${BLUE}[4/7] Verificando Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Docker Compose no instalado, instalando...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo -e "${GREEN}✓ Docker Compose ya instalado${NC}"
fi

# 5. Clonar repositorio (si no existe)
echo -e "${BLUE}[5/7] Verificando código...${NC}"
if [ ! -d "/root/creditos" ]; then
    echo -e "${YELLOW}Clonando repositorio...${NC}"
    cd /root
    git clone https://github.com/TU_USUARIO/creditos.git
    cd creditos
else
    echo -e "${GREEN}✓ Código ya existe, actualizando...${NC}"
    cd /root/creditos
    git pull origin main
fi

# 6. Configurar variables
echo -e "${BLUE}[6/7] Configurando variables de entorno...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creando archivo .env...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Por favor, edita .env con tus valores reales:${NC}"
    echo -e "${YELLOW}    nano .env${NC}"
    exit 1
else
    echo -e "${GREEN}✓ .env ya existe${NC}"
fi

# 7. Iniciar contenedores
echo -e "${BLUE}[7/7] Iniciando contenedores...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Verificar estado
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ Deployment completado!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "📊 Estado de contenedores:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "📝 Logs:"
echo "  Backend:  docker-compose -f docker-compose.prod.yml logs -f creditos_backend"
echo "  Frontend: docker-compose -f docker-compose.prod.yml logs -f creditos_frontend"
echo "  DB:       docker-compose -f docker-compose.prod.yml logs -f creditos_db"
echo ""
echo "🔗 URLs de acceso:"
echo "  Frontend:  http://2.24.194.52:4210"
echo "  Backend:   http://2.24.194.52:8010"
echo "  API Docs:  http://2.24.194.52:8010/docs"
echo ""
