"""Basic SDK demonstration for AEVORUN."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aevorun import Aevorun

def main():
    model = Aevorun()

    code = """
def shift_billing_date(current_date):
    # Potential month-end rollover and duration mismatch
    return current_date + timedelta(days=30)
"""
    print("Analyzing source code with AEVORUN-T1...")
    result = model.analyze_source(code, top_k=3)

    for scenario in result.scenarios:
        print(f"Rank {scenario.rank}: {scenario.name:<25} (Score: {scenario.score:.4f})")
        print(f"  Description: {scenario.description}")
        print(f"  Recommended Test Dates: {scenario.recommended_test_dates[:2]}")

if __name__ == "__main__":
    main()

