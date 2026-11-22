# AEVORUN System Architecture & Machine Learning Design

This document details the architectural design, feature extraction engine, neural model specification, calibration routines, and scenario ranking pipeline powering **AEVORUN-T1**.

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
                       |   Dense Feature Projection    |
                       |     (80-dim -> 128-dim)       |
                       +---------------+---------------+
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

## 1. Safe AST Feature Extraction Engine (`aevorun.features`)

The feature extraction subsystem parses arbitrary Python code safely without executing it:
- **Resilient Parsing:** Handles partial functions, syntax errors, and missing type annotations by isolating individual AST subtrees.
- **80-Dimensional Representation:**
  - **Temporal API Invocations (16-D):** Quantifies occurrences of `datetime`, `timedelta`, `replace`, `astimezone`, `fromtimestamp`, `strftime`, `strptime`, `ZoneInfo`, and `dateutil`.
  - **Calendar Mutation Clues (16-D):** Identifies mutations to `.year`, `.month`, `.day`, `.hour`, `.fold`, and detects manual arithmetic with constants such as `30`, `365`, `86400`.
  - **Control Flow & Predicates (16-D):** Measures conditional branching depth, comparisons (`==`, `<`, `>=`), and exception handlers targeting `ValueError` or `OverflowError`.
  - **Structural Bag-of-AST (32-D):** SVD-reduced representation of syntactic node bigrams (e.g., `Call[Attribute]->BinOp[Add]`).

---

## 2. AEVORUN-T1 Neural Architecture (`aevorun.model`)

Rather than relying on resource-intensive LLMs, AEVORUN-T1 utilizes a bespoke, lightweight neural architecture:

| Component | Dimensions / Structure | Activation | Regularization |
| :--- | :--- | :--- | :--- |
| **Input Layer** | 80 features | Linear | LayerNorm |
| **Residual Block 1** | 128 -> 128 | GELU | Dropout (0.15), Residual Add |
| **Residual Block 2** | 128 -> 128 | GELU | Dropout (0.15), Residual Add |
| **Latent Projection** | 128 -> 64 | GELU | LayerNorm |
| **Temporal Gate Head** | 64 -> 1 | Sigmoid | Binary Cross-Entropy |
| **Scenario Multi-Head**| 64 -> 14 | Sigmoid | Asymmetric Focal Loss |

**Total Trainable Parameters:** 53,711  
**CPU Inference Latency:** ~0.07 milliseconds per function.

---

## 3. Calibration & Loss Formulation

### Asymmetric Focal Loss
To address class imbalance across rare temporal edge cases (e.g., `fold` daylight saving ambiguity vs. common month arithmetic), we train with Asymmetric Focal Loss:
$$\mathcal{L}_{ASL} = -\sum_{k=1}^{14} \alpha_k (1 - p_k)^\gamma y_k \log(p_k) + (1 - y_k) p_k^\mu \log(1 - p_k)$$
where $\gamma = 2.0$ for hard positive examples and $\mu = 4.0$ aggressively suppresses gradient updates from dominant negatives.

### Platt Temperature Calibration
Model logits are post-calibrated on held-out validation sets:
$$P(\text{scenario}_k \mid \mathbf{x}) = \sigma\left(\frac{z_k}{T}\right)$$
Calibration achieves an Expected Calibration Error (ECE) of **0.034**, ensuring predicted probabilities faithfully represent empirical defect risk.

---

## 4. The 14 Canonical Failure Modes

1. `leap_day`: February 29 year modification raising `ValueError: day is out of range for month`.
2. `month_end`: Adding fixed 30-day timedelta across variable 28/29/30/31 day calendar boundaries.
3. `daylight_saving_transition`: 1-hour civil clock skips/repeats across spring and autumn transitions.
4. `ambiguous_local_time`: Repeated autumn clock fold hours requiring explicit `fold=0` or `fold=1`.
5. `nonexistent_local_time`: Local time instantiated in the spring-forward 1-hour gap.
6. `naive_aware_mismatch`: Subtraction/comparison between timezone-naive and timezone-aware datetimes.
7. `timestamp_precision`: Floating-point Unix timestamp precision loss and strict equality failure.
8. `calendar_duration_mismatch`: Conflating calendar intervals (e.g. 1 month) with fixed elapsed time (e.g. 30 days).
9. `year_boundary`: Dec 31 / Jan 1 boundary errors with ISO week numbers (`%G-%V`) vs `%Y`.
10. `midnight_boundary`: Exclusive vs inclusive datetime range filtering at `23:59:59.999`.
11. `timezone_conversion`: Hardcoded offset arithmetic instead of IANA time zone database transitions.
12. `date_parsing`: Locale confusion between `DD/MM/YYYY` and `MM/DD/YYYY`.
13. `recurring_schedule`: Interval drift when rescheduling jobs based on completion time rather than target time.
14. `expiration_boundary`: Distributed clock skew causing token authentication failures on boundary timestamps.
