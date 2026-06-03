"""
run_pipeline.py
---------------
Orchestrates the full pipeline in order:
  1. validate_data.py   – detect issues, produce clean CSV
  2. transform_load.py  – normalise and load into SQLite
  3. generate_report.py – query DB and write Excel report

Run from the project root:
    python run_pipeline.py
"""

import subprocess
import sys
import os
import time

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")

STEPS = [
    ("Step 1 – Data Validation",           os.path.join(SCRIPTS_DIR, "validate_data.py")),
    ("Step 2 – Transform & Load to DB",     os.path.join(SCRIPTS_DIR, "transform_load.py")),
    ("Step 3 – Excel Report Generation",    os.path.join(SCRIPTS_DIR, "generate_report.py")),
]


def run_step(label: str, script: str):
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")
    t0     = time.time()
    result = subprocess.run([sys.executable, script], capture_output=False, text=True)
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f"\n[FATAL] {label} failed (exit code {result.returncode}). Aborting pipeline.")
        sys.exit(result.returncode)
    print(f"\n  ✓ Completed in {elapsed:.2f}s")


def main():
    print("\n" + "=" * 60)
    print("  Student Performance Pipeline")
    print("=" * 60)
    start = time.time()

    for label, script in STEPS:
        run_step(label, script)

    print("\n" + "=" * 60)
    print(f"  Pipeline finished in {time.time() - start:.2f}s")
    print("  Output: reports/student_performance_report.xlsx")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
