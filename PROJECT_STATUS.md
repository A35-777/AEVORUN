# AEVORUN Project Status

**Project:** AEVORUN  
**Model:** AEVORUN-T1  
**Description:** Learned Temporal Test-Scenario Prioritization  
**Tagline:** "Find the time-related tests your code is most likely to need."  
**Last Updated:** 2026-11-22  
**Target Environment:** Windows 10 x64, AMD PRO A12-9800B, 8 GB RAM, CPU-first training  
**Status:** **ALL 12 PHASES COMPLETE & VERIFIED**

---

## Phase Tracking & Completion Evidence

| Phase | Description | Status | Evidence / Artifacts |
|---|---|---|---|
| **Phase 1** | Research & Competition Audit | **COMPLETE** | `research/COMPETITION_AUDIT.md` (CMU MSR 2025 analysis, gap analysis) |
| **Phase 2** | Dataset Discovery & Licensing Audit | **COMPLETE** | `data/README.md`, `data/dataset_card.md` |
| **Phase 3** | Task Definition & Label Taxonomy | **COMPLETE** | `data/label_schema.json`, `aevorun/taxonomy.py` (14 scenarios) |
| **Phase 4** | Feature Extraction & Baselines | **COMPLETE** | `aevorun/features.py` (82 AST features), `aevorun/baselines.py` |
| **Phase 5** | Dataset Construction & Leakage Checks | **COMPLETE** | `scripts/build_dataset.py`, `scripts/validate_dataset.py`, `scripts/audit_leakage.py` (0% overlap) |
| **Phase 6** | Model Architecture & Training | **COMPLETE** | `aevorun/model.py` (53,711 params), `model/checkpoints/aevorun_t1.pt` (`de78614a...`) |
| **Phase 7** | Independent Evaluation & Error Analysis | **COMPLETE** | `benchmarks/RESULTS.md` (Held-out Recall@3: 93.7%), `benchmarks/ERROR_ANALYSIS.md` |
| **Phase 8** | Inference SDK & CLI | **COMPLETE** | `aevorun/core.py`, `aevorun/cli.py`, `examples/` |
| **Phase 9** | Testing & Reproducibility | **COMPLETE** | `tests/` (23 passed out of 23 unit tests) |
| **Phase 10** | Documentation & Model Card | **COMPLETE** | `MODEL_CARD.md`, `CITATION.cff`, `README.md` |
| **Phase 11** | Website (Static / Cloudflare Pages) | **COMPLETE** | `website/index.html`, `website/styles.css`, `website/app.js` |
| **Phase 12** | GitHub Release Preparation | **COMPLETE** | `.github/workflows/ci.yml`, `pyproject.toml`, `requirements.txt` |

---

## Benchmark Highlights (Held-Out Unseen Repositories)
- **AEVORUN-T1 Macro-F1:** 0.8760 (vs. 0.000 Frequency Baseline, 0.7127 Heuristics)
- **Precision@3 / Recall@3:** 82.1% / 93.7%
- **Negative Sample False-Positive Rate:** 0.0% (vs. 75.0% for static heuristics)
- **Inference Latency:** 0.07 ms per function on CPU
