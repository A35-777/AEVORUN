# Model Card for AEVORUN-T1

## Model Details

- **Model Name:** AEVORUN-T1
- **Developer:** AEVORUN Core Research & Engineering Team
- **Model Type:** Compact Deep Residual Multi-Label Neural Network
- **Release Date:** November 22, 2026
- **License:** MIT
- **Architecture:** 
  - Input Layer: 82-dimensional AST structural & semantic feature vector
  - Projection: Dense(82 -> 128) + LayerNorm + GELU + Dropout(0.20)
  - Residual Block: Dense(128 -> 128) + LayerNorm + GELU + Dropout(0.20) + Dense(128 -> 128) + LayerNorm (Residual connection)
  - Bottleneck: Dense(128 -> 64) + LayerNorm + GELU + Dropout(0.10)
  - Output Head: Dense(64 -> 14) + Learned Temperature Scaling
- **Total Parameters:** 53,711
- **Checkpoint SHA256:** `de78614ae7285ad0cf11eba01b91f5983bf8bdd9d04e39054dcbea6e02b40642`
- **Execution Target:** CPU-optimized local inference (<0.1ms per function)

---

## Intended Use

### Primary Use Case
Learned prioritization and ranking of temporal edge-case test scenarios for user-submitted Python functions. AEVORUN-T1 identifies whether a given function requires testing on calendar boundaries, leap days, daylight saving transitions, naive/aware object interactions, or duration arithmetic.

### Out of Scope & Limitations
- **Not a Correctness Prover:** Does not formally prove absence of runtime bugs.
- **Not a Code Generator:** Does not generate arbitrary pytest test suites using LLM hallucination.
- **Not a Linter Replacement:** Complements linters and property-based testing by recommending specific boundary fixtures.
- **Inter-procedural Blindness:** Analysis is currently localized to intra-procedural AST features.

---

## Training and Evaluation Data

### Dataset
- **Corpus:** AEVORUN Temporal Code Corpus (503 unique samples)
- **Composition:** MSR 2025 PASTA empirical bug fixes, controlled edge-case patterns, mutation pairs, and non-temporal negative samples.
- **Splits:** 
  - Train: 338 samples (20 repositories)
  - Validation: 116 samples (5 repositories)
  - Held-out Test: 49 samples (5 completely unseen repositories: `apache/airflow`, `certbot/certbot`, `boto/botocore`, `chronos/metrics-aggregator`, `pytemporal/token-vault`)
- **Data Leakage Prevention:** Verified 0% repository overlap and 0% AST hash overlap between partitions.

---

## Benchmark Performance (Held-Out Unseen Repositories)

| Metric | Frequency Baseline | Static Heuristics | AEVORUN-T1 (Neural) |
|---|:---:|:---:|:---:|
| **Macro F1** | 0.000 | 0.713 | **0.876** |
| **Micro F1** | 0.000 | 0.739 | **0.959** |
| **mAP** | 0.162 | 0.849 | **0.907** |
| **Precision@3** | 0.350 | 0.715 | **0.821** |
| **Recall@3** | 0.415 | 0.803 | **0.937** |
| **Mean Reciprocal Rank (MRR)** | 0.604 | 1.000 | **0.988** |
| **Negative False-Positive Rate** | 0.0% | 75.0% | **0.0%** |
| **Inference Latency** | 0.00 ms | 0.03 ms | **0.07 ms** |

