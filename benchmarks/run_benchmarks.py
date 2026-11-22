"""AEVORUN Master Benchmark Runner.

Executes all audits, evaluation passes, and baseline comparisons.
"""

import sys
from pathlib import Path

REPO_ROOT = Path("d:/AEVORUN")
sys.path.insert(0, str(REPO_ROOT))

from benchmarks.compare_baselines import run_benchmark_comparison
from benchmarks.evaluate_model import evaluate_split
from scripts.audit_leakage import audit_leakage


def main():
    print("=" * 60)
    print("STEP 1: AUDITING DATASET LEAKAGE")
    print("=" * 60)
    audit_leakage()

    print("\n" + "=" * 60)
    print("STEP 2: RUNNING COMPREHENSIVE BASELINE COMPARISON")
    print("=" * 60)
    run_benchmark_comparison()

    print("\n" + "=" * 60)
    print("STEP 3: RUNNING AEVORUN-T1 HELD-OUT PER-CLASS EVALUATION")
    print("=" * 60)
    evaluate_split("test")

    print("\n>>> ALL BENCHMARKS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()

