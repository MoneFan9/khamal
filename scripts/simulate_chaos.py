#!/usr/bin/env python3
import sys
import os
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.ai.chaos_simulations import ChaosGenerator
    from core.ai.logsage import LogSagePreprocessor
    from core.ai.rag import RCAPromptBuilder
except ImportError as e:
    print(f"Error: Could not import core modules. Make sure you are running from the project root. ({e})")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Simulate chaos scenarios and visualize LogSage diagnostics.")
    parser.add_argument("scenario", choices=["db", "port", "syntax", "oom", "permission", "all"], help="The chaos scenario to simulate.")
    args = parser.parse_args()

    scenarios = {
        "db": ChaosGenerator.get_db_failure,
        "port": ChaosGenerator.get_port_conflict,
        "syntax": ChaosGenerator.get_syntax_error,
        "oom": ChaosGenerator.get_oom_error,
        "permission": ChaosGenerator.get_permission_error,
    }

    selected_keys = scenarios.keys() if args.scenario == "all" else [args.scenario]

    preprocessor = LogSagePreprocessor()
    builder = RCAPromptBuilder(enable_tools=True)

    for key in selected_keys:
        scenario = scenarios[key]()
        print(f"\n{'='*80}")
        print(f" SIMULATING: {scenario['name']}")
        print(f"{'='*80}")

        print("\n--- [1] RAW LOGS ---")
        print(scenario["logs"].strip())

        print("\n--- [2] LOGSAGE PREPROCESSING (MPPS Algorithm) ---")
        processed = preprocessor.process(scenario["logs"])
        for line in processed:
            score = preprocessor.get_severity_score(line)
            # Simple terminal colors
            color = "\033[91m" if score >= 80 else "\033[93m" if score >= 40 else ""
            reset = "\033[0m"
            print(f"{color}[{score:3}] {line}{reset}")

        print("\n--- [3] LOGSAGE RCA PROMPT (Context Injection) ---")
        prompt = builder.build_prompt(processed, scenario["project_context"])
        # Print a snippet of the system prompt and the full user prompt
        print(f"System: {prompt.system[:100]}...")
        print(f"\nUser:\n{prompt.user}")

        print("\n--- [4] EXPECTED LOGSAGE AUTO-FIX ---")
        print(f"Rationale: {scenario['rationale']}")
        print(f"Target File: {scenario['broken_file']}")
        print(f"Search Block:\n---\n{scenario['search_block']}\n---")
        print(f"Fixed Block:\n---\n{scenario['fixed_block']}\n---")

if __name__ == "__main__":
    main()
