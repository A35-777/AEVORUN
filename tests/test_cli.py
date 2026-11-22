"""Unit tests for the AEVORUN CLI."""

import subprocess
import sys
import json
from pathlib import Path

CLI_MODULE = "aevorun.cli"
REPO_ROOT = Path("d:/AEVORUN")


def run_cli(*args):
    cmd = [sys.executable, "-m", CLI_MODULE] + list(args)
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    return res


def test_cli_version():
    res = run_cli("version")
    assert res.returncode == 0
    assert "0.1.0" in res.stdout
    assert "AEVORUN-T1" in res.stdout


def test_cli_info():
    res = run_cli("info")
    assert res.returncode == 0
    assert "Deep Residual MLP" in res.stdout
    assert "14 Temporal Scenario Categories" in res.stdout


def test_cli_analyze_file():
    res = run_cli("analyze", "examples/sample_billing_code.py", "--top-k", "3")
    assert res.returncode == 0
    assert "calculate_next_billing_cycle" in res.stdout
    assert "compute_annual_expiration" in res.stdout
    assert "is_token_still_valid" in res.stdout


def test_cli_analyze_json():
    res = run_cli("analyze", "examples/sample_billing_code.py", "--json")
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert "functions" in data
    assert len(data["functions"]) == 3

