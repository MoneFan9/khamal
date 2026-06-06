#!/bin/bash
# Khamal Chaos Engineering CI Job
# This script simulates a CI job that runs chaos simulations and verifies LogSage's resiliency.

set -e

echo "🚀 Starting Khamal Chaos Engineering Test Suite..."

# 1. Environment Setup
export PYTHONPATH=core:.
export DJANGO_SETTINGS_MODULE=khamal.settings.development

# 2. Run Chaos Simulations
echo "🛠️ Running Chaos Simulations via Pytest..."
python3 -m pytest core/ai/tests_chaos_engineering.py --cov=core/ai --cov-report=term-missing

# 3. Final Status
echo "✅ Chaos Engineering tests passed successfully. LogSage is resilient."
