#!/usr/bin/env python3
import sys
import os

# Add core to PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

try:
    from ai.chaos_simulations import ChaosGenerator
    from ai.logsage import LogSagePreprocessor
except ImportError:
    print("Error: Could not import LogSage modules. Make sure you are running from the project root.")
    sys.exit(1)

def run_simulation():
    scenarios = [
        ChaosGenerator.get_db_failure(),
        ChaosGenerator.get_port_conflict(),
        ChaosGenerator.get_syntax_error(),
        ChaosGenerator.get_oom_failure(),
        ChaosGenerator.get_permission_denied()
    ]

    print("=" * 60)
    print("LOGSAGE CHAOS ENGINEERING SIMULATOR")
    print("=" * 60)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[{i}] Scenario: {scenario['name']}")
        print(f"    Target File: {scenario['broken_file']}")

    choice = input("\nSelect a scenario to simulate [1-5] (or 'q' to quit): ")
    if choice.lower() == 'q':
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(scenarios):
            scenario = scenarios[idx]
        else:
            print("Invalid choice.")
            return
    except ValueError:
        print("Invalid input.")
        return

    print(f"\n--- SIMULATING: {scenario['name']} ---")
    print("\nRAW LOGS:")
    print("-" * 20)
    print(scenario['logs'].strip())
    print("-" * 20)

    preprocessor = LogSagePreprocessor(max_output_lines=10)
    processed = preprocessor.process(scenario['logs'])

    print("\nLOGSAGE PREPROCESSED LOGS (Prioritized for LLM):")
    print("-" * 20)
    for line in processed:
        print(line)
    print("-" * 20)

    print("\nPROPOSED RCA RATIONALE:")
    print(f"> {scenario['rationale']}")

    print("\nPROPOSED FIX:")
    print(f"File: {scenario['broken_file']}")
    print("-" * 20)
    print(f"SEARCH:\n{scenario['search_block']}")
    print(f"REPLACE WITH:\n{scenario['fixed_block']}")
    print("-" * 20)

if __name__ == "__main__":
    run_simulation()
