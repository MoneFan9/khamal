#!/bin/bash

# Khamal : Plug & Play Installation Script
# This script automates the setup of the Khamal PaaS & AI Diagnostic Orchestrator.

set -e

echo "🦁 Welcome to Khamal Installation"
echo "----------------------------------"

# 1. Prerequisite Checks
echo "🔍 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and try again."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

if ! command -v nixpacks &> /dev/null; then
    echo "⚠️  Nixpacks is not installed. It is required for building images."
    echo "👉 Install it via: curl -sSL https://nixpacks.com/install.sh | bash"
fi

# 2. Environment Setup
echo "📁 Setting up environment..."
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp core/.env.example .env
    # Generate a secret key using Python for portability (avoiding sed -i issues)
    SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
    python3 -c "
import sys
content = open('.env').read().replace('your-secret-key-here', '$SECRET')
with open('.env', 'w') as f:
    f.write(content)
"
    echo "✅ .env created. Please review it later for custom configurations."
else
    echo "ℹ️  .env file already exists, skipping."
fi

# 3. Dependency Installation
echo "📦 Installing dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r core/requirements.txt

# 4. Database Migrations
echo "🗄️  Running database migrations..."
export PYTHONPATH=core:.
python3 core/manage.py migrate

# 5. Core Services Initialization
echo "🚀 Initializing core services..."

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
echo "✅ Khamal installation completed successfully!"
echo "✨ To start the server, run: source venv/bin/activate && python3 core/manage.py runserver"
echo "✨ To monitor containers, run: python3 core/manage.py monitor_containers"
echo "----------------------------------"
