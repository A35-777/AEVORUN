# AEVORUN Quickstart Guide

Get up and running with **AEVORUN-T1** in under two minutes.

---

## 1. Installation

Install AEVORUN in your Python environment:

```bash
# Clone the repository
git clone https://github.com/A35-777/AEVORUN.git
cd AEVORUN

# Install in editable mode
pip install -e .

# Or with dev dependencies (for testing and benchmarks)
pip install -e ".[dev]"
```

Verify installation:
```bash
aevorun --version
```

---

## 2. Command Line Interface (CLI)

### Analyze a Single File
Analyze all functions inside a Python module:
```bash
aevorun analyze src/billing.py
```

Output:
```
============================================================
  AEVORUN-T1 Temporal Test-Scenario Prioritization
============================================================
File: src/billing.py (Function: calculate_next_billing)

[✓] Classification: TEMPORAL (Confidence: 0.96)
[✓] AST Clues: datetime.replace, timedelta(days=30), month rollover

Prioritized Test Scenarios:
  #1 [0.96] month_end Variable 28-31 day calendar transition
  #2 [0.94] leap_day Feb 29 leap year boundary (replace(year=...))
  #3 [0.88] calendar_duration Fixed 30-day timedelta vs. calendar arithmetic
  #4 [0.79] recurring_schedule Phase drift across consecutive billing intervals
```

### Analyze an Entire Repository
Scan a whole repository and produce structured reports:
```bash
aevorun scan src/ --format json --output report.json
```

### Generate Pytest Test Fixtures
Auto-scaffold edge case test functions tailored to the top-ranked failure modes:
```bash
aevorun generate-tests src/billing.py --out tests/test_generated_boundaries.py
```

---

## 3. Python SDK

Import `Aevorun` directly into your Python scripts or CI/CD pipelines:

```python
from aevorun import Aevorun

# Initialize local inference engine (zero network calls)
engine = Aevorun()

code = """
from datetime import datetime, timedelta

def advance_billing(current_date: datetime) -> datetime:
    return current_date + timedelta(days=30)
"""

result = engine.analyze_code(code)

print(f"Is Temporal: {result.is_temporal} (Confidence: {result.temporal_confidence:.2f})")
print(f"Detected Clues: {result.ast_clues}")

for item in result.prioritized_scenarios:
    print(f" - [{item.score:.2f}] {item.scenario_id}: {item.description}")
```

---

## 4. Pytest Plugin Integration

AEVORUN automatically registers as a pytest plugin. Use it to ensure critical functions have tests covering their top-ranked failure modes:

```bash
pytest --aevorun-verify --aevorun-threshold=0.85
```

---

## 5. Web Playground

Don't want to install anything yet? Explore real-time AST feature extraction and scenario scoring in our interactive web playground:  
👉 [https://aevorun.pages.dev/#playground](https://aevorun.pages.dev/#playground)

