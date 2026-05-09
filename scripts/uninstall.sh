#!/bin/bash

# Khamal : Uninstallation Script
# This script stops and removes Khamal-managed services and resources.

set -e

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🦁 Uninstalling Khamal${NC}"
echo "----------------------------------"

# Function to confirm action
confirm() {
    read -r -p "${1:-Are you sure? [y/N]} " response
    case "$response" in
        [yY][eE][sS]|[yY])
            true
            ;;
        *)
            false
            ;;
    esac
}

# 1. Stop and remove Docker containers
echo -e "${BLUE}🛑 Stopping and removing Docker containers...${NC}"

# Remove specific infrastructure containers
for container in khamal-traefik docker-socket-proxy; do
    if docker ps -a --format '{{.Names}}' | grep -q "^$container$"; then
        echo "🗑️  Removing $container..."
        docker stop "$container" >/dev/null 2>&1 || true
        docker rm "$container" >/dev/null 2>&1 || true
    fi
done

# Remove all managed containers
MANAGED_CONTAINERS=$(docker ps -a --filter "label=khamal.managed=true" --quiet)
if [ -n "$MANAGED_CONTAINERS" ]; then
    echo "🗑️  Removing managed project containers..."
    docker stop $MANAGED_CONTAINERS >/dev/null 2>&1 || true
    docker rm $MANAGED_CONTAINERS >/dev/null 2>&1 || true
fi

# 2. Remove Docker network
if docker network ls --format '{{.Name}}' | grep -q "^khamal-proxy$"; then
    echo -e "${BLUE}🌐 Removing khamal-proxy network...${NC}"
    docker network rm khamal-proxy >/dev/null 2>&1 || true
fi

# 3. Virtual Environment
if [ -d "venv" ]; then
    if confirm "Do you want to remove the virtual environment (venv)? [y/N]"; then
        echo -e "${BLUE}📦 Removing virtual environment...${NC}"
        rm -rf venv
    fi
fi

# 4. Database
if [ -f "core/db.sqlite3" ] || [ -f "db.sqlite3" ]; then
    if confirm "Do you want to remove the database (db.sqlite3)? [y/N]"; then
        echo -e "${BLUE}🗄️  Removing database...${NC}"
        rm -f core/db.sqlite3 db.sqlite3
    fi
fi

# 5. Environment file
if [ -f ".env" ]; then
    if confirm "Do you want to remove the .env file? [y/N]"; then
        echo -e "${BLUE}📝 Removing .env file...${NC}"
        rm -f .env
    fi
fi

echo "----------------------------------"
echo -e "${GREEN}✅ Khamal has been uninstalled.${NC}"
echo "----------------------------------"
