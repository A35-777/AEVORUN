# Contributing to AEVORUN

We welcome contributions to AEVORUN and the AEVORUN-T1 research suite.

## Development Workflow

1. Fork and clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```
3. Run the unit test suite:
   ```bash
   python -m pytest -v tests/
   ```
4. Verify dataset leakage invariants if modifying data pipelines:
   ```bash
   python scripts/audit_leakage.py
   ```

## Ground Rules

- **Zero Data Leakage:** Any new dataset examples must follow strict repository partitioning. Test repositories must remain strictly unseen by training pipelines.
- **Scientific Honesty:** Never manipulate benchmark splits, metrics, or comparison baselines.

