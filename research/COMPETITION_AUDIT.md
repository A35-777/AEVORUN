# AEVORUN Competition and Research Audit

**Project:** AEVORUN (Learned Temporal Test-Scenario Prioritization)  
**Model:** AEVORUN-T1  
**Author:** AEVORUN Core Research & Engineering Team  
**Date of Audit:** November 22, 2026  
**Status:** Complete  

---

## 1. Executive Summary

Date and time handling is a notoriously deceptive source of software defects. Even in mature codebases, functions frequently pass standard unit tests but fail unexpectedly on calendar boundaries (such as leap days, month ends, year rollovers, midnight boundaries), daylight saving time (DST) transitions, ambiguous/nonexistent local times, naive versus aware datetime comparisons, or calendar-vs-duration arithmetic.

**AEVORUN-T1** is designed to address a precise, unfilled research and engineering need:
> **Given a source-code function and its structural AST features, predict and rank the temporal edge-case test scenarios that developers should write or execute for that specific function.**

This audit conducts a thorough, honest investigation across academic publications, open-source repositories, static analysis tools, test-generation engines, and commercial developer tools to determine whether this task has already been solved, what adjacent technologies exist, and where the precise research gap lies.

---

## 2. Methodology & Queries

We executed systematic searches across Google Scholar, arXiv, PyPI, GitHub, and Hugging Face between November 20, 2026, and November 22, 2026.

Queries executed:
1. `"date time bugs" OR "datetime bugs" "python" empirical study paper dataset`
2. `"cmu-pasta/date-time" github`
3. `"test scenario prioritization" learned machine learning code repository OR "temporal testing"`
4. `site:pypi.org "aevorun"`
5. `site:github.com "aevorun"`
6. `"temporal test" prioritization machine learning code`
7. `"flake8-datetimez" OR "flake8-datetime-utcnow" OR "semgrep" datetime rules`
8. `property based testing "temporal" OR "datetime" edge cases hypothesis`

---

## 3. Projects and Products Investigated

### 3.1 Academic Literature
1. **"It's About Time: An Empirical Study of Date and Time Bugs in Open-Source Python Software"** (MSR 2025, ACM SIGSOFT Distinguished Paper Award)
   - *Authors:* Shrey Tiwari, Serena Chen, Alexander Joukov, Peter Vandervelde, Ao Li, Rohan Padhye (Carnegie Mellon University PASTA Lab).
   - *Artifacts:* `cmu-pasta/date-time` on GitHub.
   - *Capabilities:* Manually curated dataset of 151 real-world date/time bugs and fixes across open-source Python projects. Developed open-coding taxonomy covering 7 dimensions (conceptual categories, programmatic operations, root causes, obscurity, severity, fix size, fix complexity). Formulated static CodeQL queries to detect naive datetime usage and UTC mismatches.
   - *Relevance to AEVORUN:* Serves as the primary empirical benchmark and empirical grounding for real-world temporal bug patterns in Python. Confirms that ~58.9% of bugs originate in object construction, that bugs are localized to single functions, and that timezones, DST, and calendar math are primary root causes.
   - *Distinction:* The CMU paper provides an empirical study and static CodeQL queries; it does *not* formulate or train a machine learning model to prioritize test scenarios for arbitrary user functions.

2. **Classic Test Case Prioritization (TCP) Research**
   - *Foundational Works:* Rothermel et al. (IEEE TSE 2001), Elbaum et al. (ACM TOSEM 2002), Do et al. (Empirical Software Engineering 2006).
   - *Techniques:* Code coverage-based prioritization, mutation-based prioritization, delta-history ranking.
   - *Capabilities:* Orders an *already-existing* test suite in Continuous Integration (CI) so that tests with higher historical likelihood of failure run earlier.
   - *Distinction:* Traditional TCP reorders existing tests in a CI suite based on execution logs and commit churn. It does *not* inspect an un-tested or newly written function to predict which unwritten temporal edge-case scenarios are relevant.

3. **Learning-to-Rank and Reinforcement Learning for Test Selection**
   - *Key Works:* Spieker et al. ("Reinforcement Learning for Automatic Test Case Prioritization", ISSTA 2017), Bertolino et al. ("Learning-to-rank for test case prioritization", 2020).
   - *Capabilities:* Trains ML/RL agents on CI historical build logs (pass/fail history, runtime, commit size) to schedule test jobs.
   - *Distinction:* Requires extensive historical execution logs of existing tests; zero understanding of datetime semantics or source-code AST features.

4. **Automated Search-Based and Property-Based Testing**
   - *Search-Based:* Pynguin (Lukasczyk et al., ICSE 2021) for Python; EvoSuite (Fraser & Arcuri) for Java.
   - *Property-Based:* Hypothesis (MacIver et al.), QuickCheck (Claessen & Hughes).
   - *Capabilities:* Pynguin generates unit tests using genetic algorithms to maximize line/branch coverage. Hypothesis generates randomized inputs against user-defined property invariants.
   - *Distinction:* Pynguin explores randomly / coverage-guided and struggles to stumble upon narrow calendar boundaries (e.g. Feb 29 on leap years or 02:30 during daylight saving change) unless specifically guided. Hypothesis requires the human developer to design the temporal property and search strategy. Neither provides learned scenario prioritization from AST code features.

### 3.2 Open-Source Static Analysis Tools & Linters
1. **`flake8-datetimez` / `flake8-datetime-utcnow`**
   - *Capabilities:* Flake8 plugin that flags calls to `datetime.datetime.now()` or `datetime.datetime.utcnow()` without a timezone parameter (`tzinfo`).
   - *Limitations:* Rigid syntactic pattern matching. Emits binary lint errors. Does not handle arithmetic, month boundaries, leap years, expiration logic, or schedule recurrence.

2. **Semgrep Rule Packs (Datetime Rules)**
   - *Capabilities:* Pattern-matching AST rules (e.g., python `datetime-naive`, deprecated `utcnow()`).
   - *Limitations:* Cannot rank scenarios, cannot assess semantic relevance, produces high false-positive rates for valid localized scripts, and cannot predict edge cases for complex multi-operation functions.

3. **CodeQL (CMU PASTA queries & GitHub security queries)**
   - *Capabilities:* Taint tracking and query-based analysis of naive/aware datetime mixing.
   - *Limitations:* Requires compiling CodeQL database; rule-based queries with high engineering overhead; does not provide confidence-calibrated rankings over edge-case scenarios.

### 3.3 Commercial & Developer Tools
1. **Meta Predictive Test Selection / Google TAP Test Selection**
   - *Capabilities:* Internal proprietary ML models that predict which regression tests to run based on file diffs and commit metadata.
   - *Limitations:* Closed-source; regression-suite filtering only; not scenario recommendation.

2. **LLM-Based Coding Assistants (GitHub Copilot, ChatGPT, Claude Code)**
   - *Capabilities:* Generates entire test files via generative prompting.
   - *Limitations:* High inference cost, remote cloud dependency, non-deterministic, hallucinates assertions, lacks calibrated confidence scores, and does not provide a structured, lightweight scenario ranking vector for local developer tooling.

---

## 4. Direct vs. Adjacent Competition Matrix

| Category | Representative Tools | Input | Output | Can Prioritize Unwritten Scenarios? | Understands Temporal Semantics? | Fully Offline & Compact? |
|---|---|---|---|:---:|:---:|:---:|
| **Empirical Study** | CMU PASTA (`date-time`) | GitHub Commits | Descriptive statistics & CodeQL rules | No | Yes (Taxonomy) | N/A |
| **Linters / Rules** | `flake8-datetimez`, Semgrep | AST / Pattern | Binary lint error | No | Superficial (Syntactic) | Yes |
| **CI Test Prioritizers** | Retesteth, RL-TCP | CI logs, commit churn | Reordered existing test list | No (Requires existing tests) | No (Pure log statistics) | Yes |
| **Test Generators** | Pynguin, EvoSuite | Python / Java bytecode | Generated test suite | No (Coverage-driven) | No (Unaware of dates) | Yes |
| **Property Testers** | Hypothesis, Freezegun | Human-written test harness | Fuzzing inputs | No (Requires human specification) | Partial (Strategy generators) | Yes |
| **LLM Assistants** | GitHub Copilot, Cursor | Source prompt | Free-form code text | Partial (Uncalibrated, noisy) | Latent (Probabilistic) | No (Cloud API, heavy) |
| **AEVORUN-T1 (This Work)** | **AEVORUN** | **Source AST & structural features** | **Calibrated ranking of temporal scenarios + evidence** | **YES** | **YES (Learned multi-label model)** | **YES (< 500k params, CPU-native)** |

---

## 5. The Exact Proposed Research Gap

While existing tools either:
1. Enforce blunt binary linter checks on single API calls (e.g., banning naive `now()`), or
2. Reorder massive existing CI test suites based on commit churn, or
3. Rely on multi-billion parameter cloud LLMs to hallucinate test code,

**No existing system provides lightweight, learned, offline, code-specific prioritization of temporal test scenarios.**

Developers writing temporal logic (billing intervals, token expiration, cron schedules, cache TTLs, calendar math) need to know:
* *"For this specific function, what are the top 3 temporal boundary scenarios I must verify?"*
* E.g., does this function need a `leap_day` test? A `month_end` test? A `dst_transition` test? A `calendar_duration_mismatch` test?

AEVORUN-T1 fills this gap by training a compact neural model directly on AST structural features extracted from real-world temporal bug fixes, curated edge cases, controlled mutations, and non-temporal negative samples.

---

## 6. What Could Invalidate the Hypothesis?

The core research hypothesis:
> *A compact neural model can learn code-specific temporal test-scenario relevance and prioritize useful scenarios for previously unseen functions better than generic scenario selection and simple static heuristics.*

Conditions that would scientifically falsify or invalidate this hypothesis:
1. **Heuristic Dominance:** If hand-crafted static heuristics (e.g. `if "days" in code: recommend month_end`) achieve equal or superior Macro-F1 and Top-3 Precision compared to the learned neural model on a strict repository-level holdout.
2. **Frequency Dominance:** If a simple baseline that always predicts the most frequent temporal scenarios in the training set matches the model's ranking performance on unseen repositories.
3. **AST Invariance / Semantic Opacity:** If temporal bugs depend entirely on runtime dynamic values that leave no detectable signature in the static AST and call graph, causing the model to perform no better than random guessing on unseen code.
4. **Poor Generalization Across Repositories:** If the model memorizes repository-specific variable names or API idioms and collapses when evaluated on previously unseen open-source repositories.

If our benchmark experiments show that heuristics or frequency baselines outperform AEVORUN-T1, we will document that result honestly and analyze the failure modes.

---

## 7. Namespace Availability Check

- **PyPI:** Checked November 22, 2026. The package name `aevorun` is **unregistered and available** on PyPI.
- **GitHub:** Checked November 22, 2026. No repository or organization named `aevorun` exists for developer tools (only unrelated fiction/media lore references).
- **Trademark:** No trademark conflict found for `aevorun` in the software testing or developer tools categories.

---

## 8. Audit Conclusion

The research gap is genuine, unaddressed by existing open-source and commercial tooling, and well-motivated by recent empirical software engineering findings (notably Tiwari et al., MSR 2025). We proceed to Phase 2 (Dataset Discovery and Licensing Audit) and Phase 3 (Taxonomy Definition).

