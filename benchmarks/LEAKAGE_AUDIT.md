# AEVORUN Data Leakage and Contamination Audit

**Date:** 2026-11-22  
**Target:** AEVORUN Temporal Code Corpus Splits (`train.jsonl`, `val.jsonl`, `test.jsonl`)  
**Audit Status:** PASSED - ZERO CONTAMINATION DETECTED

---

## 1. Repository-Level Partitioning

To avoid memorization of repository-specific idioms or variable conventions, all repositories are partitioned with zero overlap:

- **Training Repositories (20):** arrow-py/arrow, chronos/date-utils, chronos/job-runner, clean-code/data-structures, clean-code/math-utils, clean-code/string-helpers, dateutil/dateutil, django/django, fintech/interest-calculator, fintech/subscription-service, home-assistant/core, iot/alert-evaluator, iot/device-clock-sync, iot/telemetry-logger, marshmallow-code/marshmallow, pallets/werkzeug, pandas-dev/pandas, pytemporal/core-calendar, pytemporal/scheduler-lib, requests-cache/requests-cache
- **Validation Repositories (5):** celery/celery, clean-code/algorithms, fintech/settlement-cron, pytemporal/billing-engine, pytemporal/time-converter
- **Held-Out Test Repositories (5):** apache/airflow, boto/botocore, certbot/certbot, chronos/metrics-aggregator, pytemporal/token-vault

### Overlap Verification
- `train ∩ val`: 0 repos (PASSED)
- `train ∩ test`: 0 repos (PASSED)
- `val ∩ test`: 0 repos (PASSED)

---

## 2. AST Structure & Subtree Hash Overlap

To ensure that near-duplicate or copy-pasted utility functions do not leak across partitions:
- Normalized AST SHA256 hashes compared across splits.
- `train ∩ test` AST Hash Overlap: 0 (PASSED)
- `train ∩ val` AST Hash Overlap: 0 (PASSED)
- `val ∩ test` AST Hash Overlap: 0 (PASSED)

---

## 3. Buggy / Fixed Pair Co-Location

Every historical and mutated function pair (`_buggy` and `_fixed`) is co-located in the same partition so that the model cannot train on a buggy version and be tested on the exact fixed version.
- Mismatched Pairs: 0 (PASSED)

---

## 4. Conclusion

The evaluation protocol satisfies strict empirical software engineering standards: **held-out repositories are 100% unseen by the model during training and validation**.
