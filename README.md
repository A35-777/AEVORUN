# AEVORUN

> **Find the time-related tests your code is most likely to need.**

[![CI](https://github.com/aevorun/aevorun/actions/workflows/ci.yml/badge.svg)](https://github.com/aevorun/aevorun/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)](https://python.org)
[![Model: AEVORUN-T1](https://img.shields.io/badge/Model-AEVORUN--T1-orange.svg)](MODEL_CARD.md)

AEVORUN is a machine-learning research project and developer tool for **Learned Temporal Test-Scenario Prioritization**. 

Given a source-code function and its structural AST features, AEVORUN-T1 predicts and ranks temporal edge-case scenarios (leap days, month ends, daylight saving transitions, timezone conversions, expiration boundaries, recurring intervals) that developers should prioritize when writing unit tests.

It is **not** an LLM wrapper, does not require an internet connection, and runs in sub-millisecond latency on standard CPUs.

---

## Benchmark Results (Held-Out Unseen Repositories)

Evaluated on held-out repositories (`apache/airflow`, `certbot/certbot`, `boto/botocore`, `chronos/metrics-aggregator`, `pytemporal/token-vault`) with 0% data leakage:

| Model | Macro F1 | Micro F1 | mAP | Precision@3 | Recall@3 | Neg. FPR | Latency |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Frequency Baseline** | 0.000 | 0.000 | 0.162 | 35.0% | 41.5% | 0.0% | 0.00 ms |
| **Static Heuristics** | 0.713 | 0.739 | 0.849 | 71.5% | 80.3% | 75.0% | 0.03 ms |
| **Logistic Regression** | 0.899 | 0.973 | 0.913 | 84.6% | 95.5% | 0.0% | 0.13 ms |
| **Gradient Boosted Trees** | 0.884 | 0.963 | 0.921 | 82.9% | 94.1% | 0.0% | 1.40 ms |
| **AEVORUN-T1 (Neural)** | **0.876** | **0.959** | **0.907** | **82.1%** | **93.7%** | **0.0%** | **0.07 ms** |

---

## Quickstart

### Installation

```bash
git clone https://github.com/aevorun/aevorun.git
cd aevorun
pip install -e .
```

### Python SDK

```python
from aevorun import Aevorun

model = Aevorun()

code = """
def calculate_next_billing_cycle(subscription_start):
    from datetime import timedelta
    return subscription_start + timedelta(days=30)
"""

result = model.analyze_source(code, top_k=3)

for scenario in result.scenarios:
    print(f"[{scenario.rank}] {scenario.name:<25} (Score: {scenario.score:.2f})")
    print(f"    Suggested Test Boundary: {scenario.recommended_test_dates[0]}")
```

### CLI Interface

```bash
# Analyze a file
aevorun analyze examples/sample_billing_code.py

# Output JSON
aevorun analyze examples/sample_billing_code.py --json --top-k 3

# View model details
aevorun info
```

---

## Reproducibility

1. **Build Dataset:**
   ```bash
   python scripts/build_dataset.py
   python scripts/validate_dataset.py
   python scripts/audit_leakage.py
   ```

2. **Train AEVORUN-T1:**
   ```bash
   python scripts/train.py
   ```

3. **Run Full Benchmark Suite:**
   ```bash
   python benchmarks/run_benchmarks.py
   ```

4. **Run Unit Tests:**
   ```bash
   python -m pytest -v tests/
   ```

---

## Citation

```bibtex
@software{aevorun2026,
  author = {AEVORUN Research Team},
  title = {AEVORUN: Learned Temporal Test-Scenario Prioritization},
  year = {2026},
  url = {https://github.com/aevorun/aevorun}
}
```

## License

MIT License.

