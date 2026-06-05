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

if ! command -v usbguard &> /dev/null; then
    echo -e "${YELLOW}⚠️  usbguard is not installed. It is recommended for secure physical ingestion.${NC}"
    echo "ℹ️  Continuing installation without physical security hardening."
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
    echo -e "${GREEN}✅ .env created.${NC}"
else
    echo "ℹ️  .env file already exists."
fi

# 3. Security Hardening (Hidden Admin)
echo -e "${BLUE}🛡️  Configuring secure admin access...${NC}"
python3 -c "
import os
import secrets

def update_env(key, value):
    with open('.env', 'a+') as f:
        f.seek(0)
        content = f.read()
        if key not in content:
            f.write(f'\n{key}={value}')
            return True
    return False

# Generate hidden admin path
admin_path = 'admin-' + secrets.token_urlsafe(16)
if update_env('ADMIN_URL', admin_path):
    print(f'✅ Generated hidden admin URL path.')

# Generate system admin credentials
username = 'khamal_master'
password = secrets.token_urlsafe(24)
if update_env('SYSTEM_ADMIN_USERNAME', username):
    update_env('SYSTEM_ADMIN_PASSWORD', password)
    print(f'✅ Generated system admin credentials.')
"

# 4. Dependency Installation
echo -e "${BLUE}📦 [Phase 1/3] Installing Python dependencies...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r core/requirements.txt

# 5. Database Migrations
echo -e "${BLUE}🗄️  [Phase 2/3] Running database migrations...${NC}"
export PYTHONPATH=core:.
python3 core/manage.py migrate

# 6. Initialize System Admin
echo -e "${BLUE}👤 [Phase 3/3] Setting up system administrator...${NC}"
# Load from .env manually
export $(grep -v '^#' .env | xargs)
python3 core/manage.py create_system_admin

# 7. Core Services Initialization
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
echo -e "${BLUE}✨ SECURITY INFORMATION (Save this!):${NC}"
ADMIN_PATH=$(grep ADMIN_URL .env | cut -d '=' -f2)
ADMIN_USER=$(grep SYSTEM_ADMIN_USERNAME .env | cut -d '=' -f2)
ADMIN_PASS=$(grep SYSTEM_ADMIN_PASSWORD .env | cut -d '=' -f2)
echo -e "  Admin URL:      ${YELLOW}http://localhost:8000/$ADMIN_PATH/${NC}"
echo -e "  Admin User:     ${YELLOW}$ADMIN_USER${NC}"
echo -e "  Admin Password: ${YELLOW}$ADMIN_PASS${NC}"
echo "----------------------------------"
echo -e "${BLUE}🚀 Next steps:${NC}"
echo -e "  1. Activate the environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "  2. Start the Khamal server:  ${YELLOW}python3 core/manage.py runserver${NC}"
echo "----------------------------------"
