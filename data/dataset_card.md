---
language:
- python
tags:
- software-engineering
- testing
- temporal-logic
- test-prioritization
- bug-detection
license: mit
size_categories:
- 1K<n<10K
---

# Dataset Card for AEVORUN Temporal Code Corpus

## Dataset Description

- **Repository:** https://github.com/aevorun/aevorun
- **Leaderboard / Benchmark:** AEVORUN Benchmark Suite
- **Point of Contact:** AEVORUN Research Team

### Summary

The AEVORUN Temporal Code Corpus is a multi-label code dataset constructed to train and evaluate machine learning models on **Learned Temporal Test-Scenario Prioritization**. Given a Python function's source code, the target is a multi-hot binary vector of 14 temporal edge-case scenarios that must be prioritized in testing.

### Supported Tasks and Leaderboards

- **Multi-Label Temporal Scenario Prioritization:** Predict which of 14 edge-case scenarios apply to a Python function.
- **Top-K Test Discovery:** Measure Precision@K and Recall@K when recommending testing scenarios to developers.

### Languages

Python 3 (source code and abstract syntax trees).

---

## Dataset Structure

### Data Instances

Each instance represents an individual Python function with provenance metadata:

```json
{
  "sample_id": "pandas_date_range_042",
  "repo": "pandas-dev/pandas",
  "function_name": "generate_range",
  "source_code": "def generate_range(start, end, freq):\n    ...",
  "origin": "real_bug",
  "license": "BSD-3-Clause",
  "labels": ["month_end", "calendar_duration_mismatch", "midnight_boundary"],
  "ast_hash": "a4f89d3..."
}
```

### Data Fields

- `sample_id`: Unique identifier including repository or synthetic tag.
- `repo`: Source repository or generator family.
- `function_name`: Name of the analyzed function.
- `source_code`: Complete source text of the function.
- `origin`: Category (`real_bug`, `controlled_pattern`, `mutation_pair`, `hard_negative`).
- `license`: Open-source license of the source code.
- `labels`: Array of applicable temporal scenario names from `label_schema.json`.
- `ast_hash`: MinHash / subtree hash used for deduplication across partitions.

---

## Dataset Creation

### Curation Rationale

Empirical studies (e.g. Tiwari et al., MSR 2025) demonstrate that temporal bugs are among the most pervasive, localized, and severe defects in Python software. Yet standard test generation tools lack temporal semantic priors. This dataset bridges the empirical study of real-world bugs with machine learning for software engineering (ML4SE).

### Source Data

1. **CMU PASTA Date-Time Corpus:** 151 manually verified real-world date/time bugs from popular Python repositories.
2. **Open-Source Temporal Logic:** Mined functions utilizing `datetime`, `time`, `zoneinfo`, `dateutil`, `pytz`, `calendar`, and `arrow` across top GitHub repositories.
3. **Controlled Synthetic Scenarios:** Generated functions designed to isolate specific boundary interactions (e.g., leap day year replacement, fold disambiguation, ISO week rollover).
4. **Hard Negative Samples:** Standard computational, string-processing, and non-temporal data pipeline functions.

### Annotations

Annotations are derived from:
- Historical commit diffs and issue reports in real bug datasets.
- Verified test suite assertions in controlled examples.
- Execution-backed mutation testing for mutated pairs.

### Personal and Sensitive Information

None. All code samples are from public open-source repositories or generated programmatically.

---

## Considerations for Using the Data

### Synthetic-to-Real Gap

Controlled and mutated examples provide dense supervision for rare edge cases (such as February 29th and DST gaps), but real-world code often contains idiosyncratic wrappers, domain objects, and dynamic call chains. To combat this, AEVORUN evaluates separately on held-out open-source repositories.

### Bias and Limitations

The dataset currently targets Python 3 syntax and idiomatic libraries (`datetime`, `zoneinfo`, `dateutil`, `time`). Extension to other languages (TypeScript, Go, Java) is planned for future revisions.

