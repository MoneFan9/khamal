#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Chaos Engineering Tests for LogSage...${NC}"

# Ensure we are in the root directory
cd "$(dirname "$0")/.."

# Set PYTHONPATH to include core
export PYTHONPATH=$PYTHONPATH:$(pwd)/core

# Run the chaos tests
echo -e "${BLUE}Running pytest core/ai/tests_chaos_engineering.py...${NC}"
python3 -m pytest -c /dev/null core/ai/tests_chaos_engineering.py

echo -e "${GREEN}Chaos Engineering Tests Passed Successfully!${NC}"
