#!/bin/bash
# scripts/run_chaos_tests.sh
# Entry point for Chaos Engineering CI tests.

set -e

echo "🚀 Démarrage de la suite de tests de Chaos Engineering..."

# Configuration de l'environnement
export PYTHONPATH=$(pwd):$(pwd)/core
export DJANGO_SETTINGS_MODULE=khamal.settings.development

# Exécution des tests via pytest
# On se concentre sur les simulations de chaos pour valider LogSage
python3 -m pytest core/ai/tests_chaos_engineering.py -v --cov=core/ai/logsage.py --cov=core/ai/chaos_simulations.py

echo "✅ Tous les scénarios de chaos ont été validés par LogSage."
