import subprocess
import sys
import os
from pathlib import Path

def run_failing_snippet(name, snippet):
    print(f"--- Simulating: {name} ---")
    try:
        # Run the snippet and capture stderr
        result = subprocess.run(
            [sys.executable, "-c", snippet],
            capture_output=True,
            text=True,
            timeout=5
        )
        # We expect a failure, so we combine stdout and stderr
        full_logs = result.stdout + result.stderr
        print(full_logs)
        return full_logs
    except subprocess.TimeoutExpired:
        print(f"FAILED: {name} timed out")
        return ""

def main():
    snippets = [
        {
            "name": "Python Syntax Error",
            "code": "def hello()\n    print('world')"
        },
        {
            "name": "Missing Dependency",
            "code": "import non_existent_package_123"
        },
        {
            "name": "Database Connection Refused (Mock)",
            "code": "import socket; s = socket.socket(); s.connect(('127.0.0.1', 54321))"
        }
    ]

    log_dir = Path("chaos_logs")
    log_dir.mkdir(exist_ok=True)

    for i, s in enumerate(snippets):
        logs = run_failing_snippet(s["name"], s["code"])
        log_file = log_dir / f"chaos_{i}.log"
        log_file.write_text(logs)
        print(f"Logs saved to {log_file}\n")

if __name__ == "__main__":
    main()
