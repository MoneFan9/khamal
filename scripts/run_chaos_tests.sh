#!/bin/bash
set -e

echo "🚀 Running Chaos Engineering Test Suite..."

# Export path to include current directory
export PYTHONPATH=$PYTHONPATH:.
export DJANGO_SETTINGS_MODULE=khamal.settings.development

# Run pytest on the chaos engineering tests
pytest core/ai/tests_chaos_engineering.py -v --cov=core/ai --cov-report=term-missing

echo "✅ Chaos Engineering tests passed!"
