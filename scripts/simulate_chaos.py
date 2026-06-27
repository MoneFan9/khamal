#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add root to sys.path for absolute imports
sys.path.append(os.getcwd())

from core.ai.chaos_simulations import ChaosGenerator
from core.ai.logsage import LogSagePreprocessor
from core.ai.rag import RCAPromptBuilder

def run_simulation(scenario_name):
    print(f"\n--- 🧪 Simulation Chaos: {scenario_name} ---")

    # Select scenario
    if scenario_name == "db":
        scenario = ChaosGenerator.get_db_failure()
    elif scenario_name == "port":
        scenario = ChaosGenerator.get_port_conflict()
    elif scenario_name == "syntax":
        scenario = ChaosGenerator.get_syntax_error()
    elif scenario_name == "oom":
        scenario = ChaosGenerator.get_oom_error()
    elif scenario_name == "permission":
        scenario = ChaosGenerator.get_permission_error()
    else:
        print(f"Erreur: Scénario '{scenario_name}' inconnu.")
        return

    # 1. Raw Logs
    print("\n[1] 📝 Logs Bruts du Crash:")
    print("-" * 40)
    print(scenario["logs"].strip())
    print("-" * 40)

    # 2. LogSage Preprocessing
    preprocessor = LogSagePreprocessor(max_output_lines=10)
    processed_logs = preprocessor.process(scenario["logs"])
    print("\n[2] 🧠 Analyse LogSage (Filtrage & Priorisation):")
    for line in processed_logs:
        print(f"  > {line}")

    # 3. RCA Prompt Generation
    builder = RCAPromptBuilder(enable_tools=True)
    prompt = builder.build_prompt(processed_logs, scenario["project_context"])

    print("\n[3] 🤖 Prompt de Diagnostic Généré (Extrait):")
    print(f"Context: {scenario['project_context']['project_name']} ({scenario['project_context']['language']})")
    print(f"User Message: {prompt.user[:200]}...")

    print(f"\n✅ Simulation '{scenario['name']}' terminée avec succès.\n")

if __name__ == "__main__":
    scenarios = ["db", "port", "syntax", "oom", "permission"]

    if len(sys.argv) > 1:
        run_simulation(sys.argv[1])
    else:
        print("Usage: python3 scripts/simulate_chaos.py [db|port|syntax|oom|permission]")
        print("\nExécution de tous les scénarios par défaut...\n")
        for s in scenarios:
            run_simulation(s)
