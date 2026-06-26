#!/bin/bash

# Khamal : Plug & Play Installation Script
# "One-liner" installation: curl -sSL https://raw.githubusercontent.com/your-repo/khamal/main/scripts/install.sh | bash
# This script automates the setup of the Khamal PaaS & AI Diagnostic Orchestrator.

set -e

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🦁 Welcome to Khamal Installation (Plug & Play)${NC}"
echo "----------------------------------------------------"

# Handle "curl | bash" execution by cloning if not in a khamal directory
if [ ! -d "core" ] || [ ! -f "core/manage.py" ]; then
    echo -e "${BLUE}📦 Not in a Khamal directory. Cloning the repository...${NC}"
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git is not installed. Please install git and try again.${NC}"
        exit 1
    fi
    git clone https://github.com/your-repo/khamal.git
    cd khamal
fi

# 1. Prerequisite Checks
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker and try again.${NC}"
    echo "Visit: https://docs.docker.com/get-docker/"
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
    echo "👉 Installing Nixpacks for you..."
    curl -sSL https://nixpacks.com/install.sh | bash
fi

# 2. Environment Setup
echo -e "${BLUE}📁 Setting up environment...${NC}"
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    if [ -f core/.env.example ]; then
        cp core/.env.example .env
    else
        echo "DATABASE_URL=sqlite:///db.sqlite3" > .env
    fi

    # Generate a secret key using Python for portability
    SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
    python3 -c "
import sys
import os
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        content = f.read()
    content = content.replace('your-secret-key-here', '$SECRET')
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
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(f'{key}={value}\n')
        return True
    with open('.env', 'a+') as f:
        f.seek(0)
        content = f.read()
        if key not in content:
            if not content.endswith('\n') and content:
                f.write('\n')
            f.write(f'{key}={value}')
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
echo -e "${BLUE}📦 Installing dependencies...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r core/requirements.txt

# 5. Database Migrations
echo -e "${BLUE}🗄️  Running database migrations...${NC}"
export PYTHONPATH=core:.
python3 core/manage.py migrate

# 6. Initialize System Admin
echo -e "${BLUE}👤 Setting up system administrator...${NC}"
# Use python to load .env safely to avoid shell word-splitting issues
export SYSTEM_ADMIN_USERNAME=$(python3 -c "import os; from environ import Env; env = Env(); Env.read_env('.env'); print(env('SYSTEM_ADMIN_USERNAME', default=''))")
export SYSTEM_ADMIN_PASSWORD=$(python3 -c "import os; from environ import Env; env = Env(); Env.read_env('.env'); print(env('SYSTEM_ADMIN_PASSWORD', default=''))")

python3 core/manage.py create_system_admin

# 7. Core Services Initialization
echo -e "${BLUE}🚀 Initializing core services...${NC}"

# Ensure global proxy network exists first so we can connect the proxy to it
if ! docker network inspect khamal-proxy &> /dev/null; then
    docker network create khamal-proxy
fi

# Start docker-socket-proxy if not running
if ! docker ps --filter "name=docker-socket-proxy" --quiet | grep -q . ; then
    echo "🛡️  Starting docker-socket-proxy for secure Docker API access..."
    docker run -d \
        --name docker-socket-proxy \
        --restart always \
        --network khamal-proxy \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        -p 127.0.0.1:2375:2375 \
        -e CONTAINERS=1 \
        -e NETWORKS=1 \
        -e IMAGES=1 \
        -e VOLUMES=1 \
        -e POST=1 \
        -e DELETE=1 \
        tecnativa/docker-socket-proxy
else
    # Ensure it's connected to the network
    if ! docker network inspect khamal-proxy | grep -q "docker-socket-proxy"; then
        docker network connect khamal-proxy docker-socket-proxy || true
    fi
fi

# Setup Traefik via management command
echo "🌐 Setting up Traefik proxy..."
python3 core/manage.py setup_traefik

echo "----------------------------------"
echo -e "${GREEN}✅ Khamal installation completed successfully!${NC}"
echo -e "${BLUE}✨ SECURITY INFORMATION (Save this!):${NC}"
ADMIN_PATH=$(python3 -c "from environ import Env; env = Env(); Env.read_env('.env'); print(env('ADMIN_URL', default=''))")
ADMIN_USER=$(python3 -c "from environ import Env; env = Env(); Env.read_env('.env'); print(env('SYSTEM_ADMIN_USERNAME', default=''))")
ADMIN_PASS=$(python3 -c "from environ import Env; env = Env(); Env.read_env('.env'); print(env('SYSTEM_ADMIN_PASSWORD', default=''))")

echo -e "  Admin URL:      ${YELLOW}http://localhost:8000/$ADMIN_PATH/${NC}"
echo -e "  Admin User:     ${YELLOW}$ADMIN_USER${NC}"
echo -e "  Admin Password: ${YELLOW}$ADMIN_PASS${NC}"
echo "----------------------------------"
echo -e "${BLUE}🚀 Next steps:${NC}"
echo -e "  1. Activate the environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "  2. Start the Khamal server:  ${YELLOW}python3 core/manage.py runserver${NC}"
echo "----------------------------------"
