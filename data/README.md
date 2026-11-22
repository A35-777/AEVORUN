# AEVORUN Dataset Specification & Pipeline

## Overview

The AEVORUN dataset is a multi-source, repository-partitioned benchmark and training corpus designed specifically for **Learned Temporal Test-Scenario Prioritization**.

It combines:
1. **Real-world Temporal Bugs & Fixes (MSR 2025 PASTA Study):** Ground truth historical bugs mined from open-source Python repositories (e.g., pandas, home-assistant, arrow, certbot, django, airflow, dateutil).
2. **Controlled Boundary & Pattern Examples:** Functions exercising critical temporal APIs with distinct semantic logic (leap days, month-ends, timezone conversions, DST jumps, midnight aggregation, precision conversion).
3. **Hard Negative Functions:** Non-temporal algorithmic code, general utility functions, and clean temporal functions that should *not* receive irrelevant edge-case recommendations.
4. **Controlled Temporal Mutation Pairs:** Functions with introduced subtle temporal discrepancies (e.g. using `timedelta(days=365)` instead of year arithmetic, naive `datetime.now()` in aware contexts) paired with their verified corrected versions.

---

## Directory Structure

```text
data/
  ├── label_schema.json       # Formal 14-scenario taxonomy and metadata
  ├── README.md               # Dataset pipeline and architecture documentation
  ├── dataset_card.md         # Comprehensive HuggingFace/academic-style dataset card
  ├── raw/                    # Raw mined repositories, bug commits, and curated sources
  └── processed/              # Extracted AST features, labels, and train/val/test splits
      ├── train.jsonl         # Training split (grouped by repository)
      ├── val.jsonl           # Validation split (disjoint repositories)
      ├── test.jsonl          # Held-out benchmark test split (unseen repositories)
      └── dataset_manifest.json # Checksums, split counts, and label distributions
```

---

## Licensing and Attribution

| Data Component | Source Origin | License | Usage in AEVORUN |
|---|---|---|---|
| **MSR 2025 Empirical Corpus** | CMU PASTA Lab (`cmu-pasta/date-time`) | MIT License | Benchmark grounding, empirical bug taxonomy |
| **Open Source Python Bug Commits** | Apache 2.0 / BSD / MIT Python Repositories | Respective Upstream Licenses | Attribution preserved in metadata |
| **Controlled Temporal Synthetics** | AEVORUN Project | MIT License | Augmented coverage of rare calendar boundaries |
| **Negative Samples** | Python Standard Library & Permissive Open Source | Python Software Foundation / MIT | False-positive control |

---

## Split Protocol & Leakage Prevention

To guarantee genuine scientific validity and avoid data leakage:
1. **Repository-Level Partitioning:** No repository present in the training set (`train.jsonl`) appears in the validation (`val.jsonl`) or test (`test.jsonl`) sets.
2. **Buggy/Fixed Pair Co-location:** Buggy versions and their corresponding fixed versions are always assigned to the same partition.
3. **Near-Duplicate AST Filtering:** Normalized AST subtree hashing prevents copy-pasted utility functions from leaking across partitions.
4. **Strict Repository Holdout:** 20% of all distinct repositories are completely quarantined for final benchmark evaluation.

