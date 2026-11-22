"""AEVORUN Single Model Evaluation Script.

Evaluates a specific model checkpoint across arbitrary datasets and generates
detailed per-scenario precision, recall, and ranking breakdowns.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any
import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report

REPO_ROOT = Path("d:/AEVORUN")
sys.path.insert(0, str(REPO_ROOT))

from aevorun.taxonomy import NUM_SCENARIOS, SCENARIO_NAMES
from aevorun.features import extract_function_features
from aevorun.model import AevorunModelWrapper

DATA_DIR = REPO_ROOT / "data" / "processed"


def evaluate_split(split_name: str = "test", checkpoint_path: str = None) -> Dict[str, Any]:
    jsonl_path = DATA_DIR / f"{split_name}.jsonl"
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Split file not found: {jsonl_path}")

    chk = checkpoint_path or str(REPO_ROOT / "model" / "checkpoints" / "aevorun_t1.pt")
    wrapper = AevorunModelWrapper.load_checkpoint(chk)

    samples = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))

    scenario_to_idx = {name: i for i, name in enumerate(SCENARIO_NAMES)}
    X = []
    y_true = []

    for s in samples:
        ext = extract_function_features(s["source_code"])[0]
        X.append(ext.feature_vector)
        target = np.zeros(NUM_SCENARIOS, dtype=np.float32)
        for lab in s.get("labels", []):
            if lab in scenario_to_idx:
                target[scenario_to_idx[lab]] = 1.0
        y_true.append(target)

    X_arr = np.array(X, dtype=np.float32)
    y_true_arr = np.array(y_true, dtype=np.float32)

    probs = wrapper.predict_proba(X_arr)
    preds = wrapper.predict(X_arr)

    print(f"\n=======================================================")
    print(f"AEVORUN-T1 Evaluation Report on Split: {split_name} ({len(samples)} samples)")
    print(f"=======================================================")

    macro_f1 = f1_score(y_true_arr, preds, average="macro", zero_division=0)
    micro_f1 = f1_score(y_true_arr, preds, average="micro", zero_division=0)
    print(f"Macro F1: {macro_f1:.4f} | Micro F1: {micro_f1:.4f}\n")

    print(f"{'Scenario Name':<30} | {'Prec':<7} | {'Recall':<7} | {'F1':<7} | {'Support':<7}")
    print("-" * 65)

    per_class = {}
    for c in range(NUM_SCENARIOS):
        c_true = y_true_arr[:, c]
        c_pred = preds[:, c]
        prec = precision_score(c_true, c_pred, zero_division=0)
        rec = recall_score(c_true, c_pred, zero_division=0)
        f1 = f1_score(c_true, c_pred, zero_division=0)
        supp = int(np.sum(c_true))
        per_class[SCENARIO_NAMES[c]] = {"precision": prec, "recall": rec, "f1": f1, "support": supp}
        print(f"{SCENARIO_NAMES[c]:<30} | {prec:<7.3f} | {rec:<7.3f} | {f1:<7.3f} | {supp:<7d}")

    return {
        "split": split_name,
        "macro_f1": float(macro_f1),
        "micro_f1": float(micro_f1),
        "per_class": per_class
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    parser.add_argument("--checkpoint", default=None)
    args = parser.parse_args()
    evaluate_split(args.split, args.checkpoint)

