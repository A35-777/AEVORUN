<div align="center">

# AEVORUN

### **Learned Temporal Test-Scenario Prioritization**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-aevorun.pages.dev-0284c7?style=for-the-badge&logo=cloudflare)](https://aevorun.pages.dev/)
[![Model](https://img.shields.io/badge/Model-AEVORUN--T1%20(53.7K%20Params)-f59e0b?style=for-the-badge)](MODEL_CARD.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-10b981?style=for-the-badge&logo=python)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-23%2F23%20Passing-success?style=for-the-badge&logo=pytest)](tests/)

*“Find the time-related tests your code is most likely to need.”*

[**Explore Live Interactive Playground →**](https://aevorun.pages.dev/#playground) • [**Architecture Docs**](docs/ARCHITECTURE.md) • [**Quickstart Guide**](docs/QUICKSTART.md) • [**Model Card**](MODEL_CARD.md)

</div>

---

## 🌟 Overview

Developers write functions handling dates, timestamps, timezone transitions, billing cycles, and expiration deadlines. These functions frequently pass ordinary unit tests, only to fail catastrophically in production when encountering uncommon calendar boundaries:
- **Leap Days (February 29)** raising `ValueError: day is out of range for month`.
- **Month-End (28th–31st)** drift caused by adding fixed 30-day `timedelta` intervals across variable calendar months.
- **Daylight Saving Shifts** skipping (spring forward) or repeating (autumn fall-back) civil clock hours.
- **Ambiguous Local Times** failing when naive and aware datetimes collide.
- **Floating-point Timestamps** losing precision at sub-second boundaries.

**AEVORUN-T1** is a compact, CPU-native neural model trained from scratch to analyze the syntactic and semantic Abstract Syntax Tree (AST) structure of Python functions and **predict and prioritize the specific temporal test scenarios** the function needs.

### Key Highlights
- **100% Offline & Local:** Zero remote LLM API calls, zero telemetry, zero tokens billed.
- **Ultra-Fast CPU Latency:** Single function inference executes in **0.07 ms** (14,000+ functions/second on standard laptop CPUs).
- **Zero False-Positive Rate on Non-Temporal Code:** Unlike keyword-matching linters, AEVORUN-T1 achieves a **0.0% FPR (0/16)** on algorithmic non-temporal code.
- **Empirically Evaluated:** Tested across 5 held-out open-source repositories (`apache/airflow`, `certbot/certbot`, `boto/botocore`, `chronos/metrics-aggregator`, `pytemporal/token-vault`) with strict repository-level isolation and zero data leakage.

---

## 📊 Empirical Benchmarks

Evaluated on unseen, held-out real-world repositories with 0% data leakage:

| Model / Approach | Parameters | Macro-F1 | Micro-F1 | Mean AP | Recall@3 | Non-Temporal FPR | CPU Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **AEVORUN-T1 (Ours)** | **53,711** | **0.8760** | **0.9590** | **0.9065** | **93.7%** | **0.0% (0/16)** | **0.07 ms** |
| Gradient Boosted Trees (GBDT) | Ensemble | 0.8842 | 0.9631 | 0.9210 | 94.1% | 0.0% (0/16) | 1.40 ms |
| Multi-Output Logistic Regression | 1,162 | 0.8990 | 0.9730 | 0.9130 | 95.5% | 0.0% (0/16) | 0.13 ms |
| Static Heuristic Rules | 0 (Manual) | 0.7130 | 0.7390 | 0.8490 | 80.3% | 75.0% (12/16) | 0.03 ms |
| Frequency Baseline | 14 | 0.0000 | 0.0000 | 0.1620 | 41.5% | 100.0% (16/16)| 0.01 ms |

---

## 🏛 System Architecture

```
                       +-------------------------------+
                       |      Python Source Code       |
                       +---------------+---------------+
                                       |
                                       v
                       +-------------------------------+
                       |    Safe AST Feature Parser    |
                       |    (Syntactic & Semantic)     |
                       +---------------+---------------+
                                       |
                   +-------------------+-------------------+
                   | 48 Numerical Clues| 32-D Bag-of-AST   |
                   +-------------------+-------------------+
                                       |
                                       v
                       +-------------------------------+
                       |    AEVORUN-T1 Neural Net      |
                       |  LayerNorm + Residual Blocks  |
                       |     (53,711 Parameters)       |
                       +---------------+---------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
        +---------------------+                 +---------------------+
        | Binary Gating Head  |                 | Multi-Label Scorer  |
        |  Temporal vs Other  |                 | 14 Failure Modes    |
        +----------+----------+                 +----------+----------+
                   \                                       /
                    \                                     /
                     v                                   v
        +-------------------------------------------------------------+
        |                 Platt Calibration Layer                     |
        |             (Sigmoid Temperature T = 1.12)                  |
        +------------------------------+------------------------------+
                                       |
                                       v
        +-------------------------------------------------------------+
        |                  Ranked Scenario Priority                   |
        |            Scaffolded Pytest Boundary Fixtures              |
        +-------------------------------------------------------------+
```

---

## 🏷 The 14 Canonical Failure Modes

AEVORUN-T1 outputs calibrated relevance probabilities across 14 documented temporal defect categories:

| Scenario Label | Primary Defect Mechanism | Common Python Failure Mode |
| :--- | :--- | :--- |
| `leap_day` | Feb 29 anniversary / year mutation | `date.replace(year=y+1)` raises `ValueError` on leap years |
| `month_end` | Month arithmetic with variable length | `dt + timedelta(days=30)` drifts on 28/29/30/31 boundaries |
| `daylight_saving_transition` | Civil clock discontinuity | 1-hour spring skips or autumn repeats break duration logic |
| `ambiguous_local_time` | Autumn transition repeated hour | Fall-back hours require explicit PEP 495 `fold` disambiguation |
| `nonexistent_local_time` | Spring transition missing hour | Instantiating times during the spring forward gap |
| `naive_aware_mismatch` | Timezone awareness collision | Subtracting naive and aware datetimes raises fatal `TypeError` |
| `timestamp_precision` | Sub-second floating point loss | Precision loss causes strict equality `==` checks to fail |
| `calendar_duration_mismatch` | Calendar vs fixed elapsed time | Treating 1 day == 24 hours across daylight saving changes |
| `year_boundary` | Dec 31 / Jan 1 rollover | ISO week numbers `%G-%V` mismatching calendar year `%Y` |
| `midnight_boundary` | Day boundary off-by-one | Exclusive datetime queries missing items at `23:59:59.999` |
| `timezone_conversion` | Static offset math vs IANA rules | Fixed +05:30 arithmetic ignoring historical time zone shifts |
| `date_parsing` | Ambiguous date string format | `DD/MM/YYYY` vs `MM/DD/YYYY` swapping month and day silently |
| `recurring_schedule` | Execution drift in recurring loops | Re-scheduling from loop completion time rather than target time |
| `expiration_boundary` | Distributed clock skew | Auth tokens or cache entries expiring prematurely across nodes |

---

## 🚀 Quickstart

### Installation

```bash
git clone https://github.com/A35-777/AEVORUN.git
cd AEVORUN
pip install -e .
```

### Command Line Interface

```bash
# Analyze a Python source file
aevorun analyze src/billing.py

# Output machine-readable JSON
aevorun analyze src/billing.py --json --top-k 4

# View model checkpoint metadata
aevorun info
```

### Python SDK

```python
from aevorun import Aevorun

engine = Aevorun()

code = """
from datetime import datetime, timedelta

def compute_subscription_renewal(start_date: datetime, is_annual: bool = False) -> datetime:
    if is_annual:
        return start_date.replace(year=start_date.year + 1)
    return start_date + timedelta(days=30)
"""

result = engine.analyze_source(code, top_k=3)

print(f"Is Temporal: {result.is_temporal} (Confidence: {result.temporal_confidence:.2f})")
for item in result.scenarios:
    print(f"[{item.rank}] {item.name:<24} Score: {item.score:.2f}")
```

---

## 🔬 Reproducibility & Research Integrity

AEVORUN is built for full empirical auditability:
- **Build Dataset:** `python scripts/build_dataset.py`
- **Validate Dataset & Schemas:** `python scripts/validate_dataset.py`
- **Audit Contamination & Leakage:** `python scripts/audit_leakage.py`
- **Train from Scratch:** `python scripts/train.py`
- **Execute Full Benchmark Suite:** `python benchmarks/run_benchmarks.py`
- **Run Unit Tests (23 Passing):** `python -m pytest tests/ -v`

---

## 📄 Citation

```bibtex
@software{aevorun2026,
  author = {AEVORUN Research Team},
  title = {AEVORUN: Learned Temporal Test-Scenario Prioritization},
  year = {2026},
  url = {https://aevorun.pages.dev/},
  note = {Model: AEVORUN-T1}
}
```

---

## ⚖️ License & Privacy

- **License:** Open-source under [Apache License 2.0](LICENSE).
- **Privacy:** 100% offline-first execution. Zero source code is transmitted off-premises. See [PRIVACY.md](PRIVACY.md).
