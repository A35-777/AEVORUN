"""Unit tests for AEVORUN taxonomy definition and scenario metadata."""

import json
from pathlib import Path
from aevorun.taxonomy import (
    SCENARIO_LIST,
    TAXONOMY,
    TAXONOMY_BY_ID,
    SCENARIO_NAMES,
    NUM_SCENARIOS,
)

SCHEMA_FILE = Path("d:/AEVORUN/data/label_schema.json")


def test_taxonomy_count():
    assert NUM_SCENARIOS == 14
    assert len(SCENARIO_LIST) == 14
    assert len(TAXONOMY) == 14
    assert len(TAXONOMY_BY_ID) == 14
    assert len(SCENARIO_NAMES) == 14


def test_taxonomy_ids_contiguous():
    ids = sorted([s.id for s in SCENARIO_LIST])
    assert ids == list(range(14))


def test_schema_json_sync():
    assert SCHEMA_FILE.exists()
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema = json.load(f)

    assert schema["num_classes"] == 14
    schema_names = [s["name"] for s in schema["scenarios"]]
    assert schema_names == SCENARIO_NAMES


def test_scenario_fields():
    for s in SCENARIO_LIST:
        assert s.name
        assert s.description
        assert len(s.typical_triggers) > 0
        assert len(s.recommended_test_dates) > 0

