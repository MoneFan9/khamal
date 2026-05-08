#!/bin/bash

# Khamal : Plug & Play Installation Script
# This script automates the setup of the Khamal PaaS & AI Diagnostic Orchestrator.

set -e

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🦁 Welcome to Khamal Installation${NC}"
echo "----------------------------------"

# 1. Prerequisite Checks
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker and try again.${NC}"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running. Please start Docker and try again.${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

if ! command -v nixpacks &> /dev/null; then
    echo -e "${YELLOW}⚠️  Nixpacks is not installed. It is required for building images.${NC}"
    echo "👉 Install it via: curl -sSL https://nixpacks.com/install.sh | bash"
fi

# 2. Environment Setup
echo -e "${BLUE}📁 Setting up environment...${NC}"
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp core/.env.example .env
    # Generate a secret key using Python for portability
    SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
    python3 -c "
import sys
content = open('.env').read().replace('your-secret-key-here', '$SECRET')
with open('.env', 'w') as f:
    f.write(content)
"
    echo -e "${GREEN}✅ .env created. Please review it later for custom configurations.${NC}"
else
    echo "ℹ️  .env file already exists, skipping."
fi

# 3. Dependency Installation
echo -e "${BLUE}📦 Installing dependencies...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r core/requirements.txt

# 4. Database Migrations
echo -e "${BLUE}🗄️  Running database migrations...${NC}"
export PYTHONPATH=core:.
python3 core/manage.py migrate

# 5. Core Services Initialization
echo -e "${BLUE}🚀 Initializing core services...${NC}"

# Start docker-socket-proxy if not running (simple version for single-node)
# Binds to 127.0.0.1 for security.
if ! docker ps --filter "name=docker-socket-proxy" --quiet | grep -q . ; then
    echo "🛡️  Starting docker-socket-proxy for secure Docker API access..."
    docker run -d \
        --name docker-socket-proxy \
        --restart always \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        -p 127.0.0.1:2375:2375 \
        -e CONTAINERS=1 \
        -e NETWORKS=1 \
        -e IMAGES=1 \
        -e VOLUMES=1 \
        -e POST=1 \
        -e DELETE=1 \
        tecnativa/docker-socket-proxy
fi

# Setup Traefik via management command
echo "🌐 Setting up Traefik proxy..."
python3 core/manage.py setup_traefik

echo "----------------------------------"
echo -e "${GREEN}✅ Khamal installation completed successfully!${NC}"
echo -e "${BLUE}✨ Next steps:${NC}"
echo -e "  1. Activate the environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "  2. Start the Khamal server:  ${YELLOW}python3 core/manage.py runserver${NC}"
echo -e "  3. Monitor your containers:  ${YELLOW}python3 core/manage.py monitor_containers${NC}"
echo -e "  4. Access the dashboard:     ${BLUE}http://localhost:8000${NC}"
echo "----------------------------------"
