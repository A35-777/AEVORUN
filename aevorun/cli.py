"""AEVORUN Command Line Interface (CLI).

Find the time-related tests your code is most likely to need.
Usage:
    aevorun analyze <file_path> [--top-k N] [--json] [--function NAME] [--threshold FLOAT]
    aevorun info
    aevorun version
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Optional

from aevorun import __version__, __model_version__
from aevorun.core import Aevorun, AnalysisResult


def print_banner():
    print(f"AEVORUN v{__version__} — Learned Temporal Test-Scenario Prioritization (Model: {__model_version__})")
    print("Find the time-related tests your code is most likely to need.\n")


def cmd_version(args):
    print(f"aevorun version {__version__} (model: {__model_version__})")


def cmd_info(args):
    print_banner()
    repo_root = Path(__file__).resolve().parent.parent
    checkpoint_path = repo_root / "model" / "checkpoints" / "aevorun_t1.pt"
    config_path = repo_root / "model" / "config.json"

    print("Model Configuration:")
    print(f"  Model Name:        {__model_version__}")
    print(f"  Architecture:      Deep Residual MLP (LayerNorm, GELU, Temperature Scaling)")
    print(f"  Execution Engine:  PyTorch CPU Offline Engine (<0.1ms latency)")
    print(f"  Supported Classes: 14 Temporal Scenario Categories")
    print(f"  Checkpoint Path:   {checkpoint_path}")
    print(f"  Checkpoint Exists: {checkpoint_path.exists()}")

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            print(f"  Parameters:        {cfg.get('parameter_count', 'N/A')}")
            print(f"  Checkpoint SHA256: {cfg.get('checkpoint_sha256', 'N/A')[:24]}...")


def cmd_analyze(args):
    target_path = Path(args.target)
    if not target_path.exists():
        print(f"Error: Target file not found: {target_path}", file=sys.stderr)
        sys.exit(1)

    model = Aevorun()
    result: AnalysisResult = model.analyze_file(
        file_path=target_path,
        function_name=args.function,
        top_k=args.top_k,
        threshold=args.threshold
    )

    if args.json:
        print(result.to_json(indent=2))
        return

    # Formatted terminal display
    print_banner()
    print(f"Target: {result.source_target}")
    print(f"Functions Analyzed: {len(result.functions)}\n")

    for fn in result.functions:
        print("=" * 70)
        print(f"Function: {fn.function_name} ({fn.lines_of_code} LOC)")
        print("=" * 70)

        if not fn.is_valid_syntax:
            print(f"[!] SYNTAX ERROR: {fn.unsupported_reason}")
            print("    Skipping scenario prediction for this function.\n")
            continue

        if not fn.is_temporal:
            print("[i] Non-Temporal Function: No significant temporal operations detected.")
            print("    (Suppressed edge-case test recommendations to prevent alert fatigue)\n")
            continue

        if not fn.scenarios:
            print("[i] No edge cases exceeded the confidence threshold for this function.\n")
            continue

        print(f"Prioritized Temporal Test Scenarios (Top-{len(fn.scenarios)}):\n")
        print(f" {'Rank':<5} {'Scenario Name':<28} {'Relevance':<10} {'Suggested Test Boundary'}")
        print("-" * 75)

        for sc in fn.scenarios:
            pct = f"{sc.score * 100:.1f}%"
            sample_date = sc.recommended_test_dates[0] if sc.recommended_test_dates else "N/A"
            print(f" [{sc.rank}]  {sc.name:<28} {pct:<10} {sample_date}")
            print(f"       Description: {sc.description}")

            # Evidence
            if sc.evidence:
                rel_ev = [e for e in sc.evidence if e.line > 0][:2]
                if rel_ev:
                    print(f"       Code Evidence:")
                    for ev in rel_ev:
                        print(f"        • Line {ev.line}: `{ev.snippet}` ({ev.explanation})")
            print()

    print("[NOTE] Recommendations are prioritized test-case scenarios, not proven bugs.")
    print("       Write targeted assertions to verify your code behaves correctly under these conditions.")


def main():
    parser = argparse.ArgumentParser(
        prog="aevorun",
        description="AEVORUN: Learned Temporal Test-Scenario Prioritization"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # analyze
    parser_analyze = subparsers.add_parser("analyze", help="Analyze Python code for temporal test scenarios")
    parser_analyze.add_argument("target", help="Path to Python source file")
    parser_analyze.add_argument("--top-k", type=int, default=5, help="Maximum scenarios to prioritize (default: 5)")
    parser_analyze.add_argument("--threshold", type=float, default=0.20, help="Minimum confidence threshold (default: 0.20)")
    parser_analyze.add_argument("--function", "-f", type=str, default=None, help="Filter to specific function name")
    parser_analyze.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser_analyze.set_defaults(func=cmd_analyze)

    # info
    parser_info = subparsers.add_parser("info", help="Display model architecture and checkpoint information")
    parser_info.set_defaults(func=cmd_info)

    # version
    parser_version = subparsers.add_parser("version", help="Display package and model version")
    parser_version.set_defaults(func=cmd_version)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()

