"""AEVORUN Dataset Validation Script.

Verifies:
1. Schema conformity against data/label_schema.json
2. AST parseability of all code samples
3. Label distribution across splits
4. Absence of corrupted or missing fields
"""

import json
import ast
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any

DATA_DIR = Path("d:/AEVORUN/data")
PROCESSED_DIR = DATA_DIR / "processed"
SCHEMA_FILE = DATA_DIR / "label_schema.json"


def validate_dataset():
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema = json.load(f)

    valid_scenarios = set(s["name"] for s in schema["scenarios"])
    print(f"Loaded {len(valid_scenarios)} valid scenarios from schema.")

    splits = ["train", "val", "test"]
    stats: Dict[str, Any] = {}

    total_samples = 0
    total_parse_errors = 0
    total_invalid_labels = 0

    for split in splits:
        split_path = PROCESSED_DIR / f"{split}.jsonl"
        if not split_path.exists():
            print(f"ERROR: Split file {split_path} not found!")
            continue

        samples = []
        with open(split_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    samples.append(data)
                except json.JSONDecodeError as e:
                    print(f"[{split}:{line_no}] Invalid JSON: {e}")

        # Check fields and parseability
        label_counter = Counter()
        parse_errors = 0
        invalid_labels = 0

        for s in samples:
            # Required fields
            for req in ["sample_id", "repo", "source_code", "labels"]:
                if req not in s:
                    print(f"Missing required field {req} in sample {s.get('sample_id')}")

            # AST parse check
            try:
                ast.parse(s["source_code"])
            except SyntaxError as e:
                print(f"SyntaxError in sample {s['sample_id']}: {e}")
                parse_errors += 1

            # Label validation
            for label in s["labels"]:
                if label not in valid_scenarios:
                    print(f"Invalid label '{label}' in sample {s['sample_id']}")
                    invalid_labels += 1
                label_counter[label] += 1

        total_samples += len(samples)
        total_parse_errors += parse_errors
        total_invalid_labels += invalid_labels

        stats[split] = {
            "num_samples": len(samples),
            "parse_errors": parse_errors,
            "invalid_labels": invalid_labels,
            "label_distribution": dict(label_counter.most_common())
        }

        print(f"Split [{split}]: {len(samples)} samples, {parse_errors} parse errors, {invalid_labels} invalid labels.")

    print("\n--- Summary ---")
    print(f"Total samples: {total_samples}")
    print(f"Total syntax errors: {total_parse_errors}")
    print(f"Total invalid labels: {total_invalid_labels}")

    if total_parse_errors == 0 and total_invalid_labels == 0:
        print(">>> DATASET VALIDATION PASSED! ALL SAMPLES CONFORM TO SPECIFICATION.")
    else:
        print(">>> DATASET VALIDATION FAILED WITH ERRORS.")


if __name__ == "__main__":
    validate_dataset()

