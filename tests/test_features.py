"""Unit tests for AST feature extraction."""

import numpy as np
from aevorun.features import (
    extract_function_features,
    extract_features_from_ast,
    FEATURE_DIM,
    FEATURE_NAMES,
)


def test_feature_dimension():
    assert FEATURE_DIM == 82
    assert len(FEATURE_NAMES) == 82


def test_extract_temporal_function():
    code = """
def advance_date(start_dt):
    from datetime import timedelta
    return start_dt + timedelta(days=30)
"""
    results = extract_function_features(code)
    assert len(results) == 1
    feat = results[0]

    assert feat.function_name == "advance_date"
    assert feat.is_valid_syntax is True
    assert feat.is_temporal is True
    assert feat.feature_vector.shape == (FEATURE_DIM,)
    assert feat.feature_dict["call_timedelta"] == 1.0
    assert feat.feature_dict["kwarg_days"] == 1.0
    assert len(feat.evidence) > 0


def test_extract_syntax_error():
    broken_code = """
def bad_func(
    return "unclosed paren"
"""
    results = extract_function_features(broken_code)
    assert len(results) == 1
    feat = results[0]
    assert feat.is_valid_syntax is False
    assert "SyntaxError" in feat.unsupported_reason
    assert feat.feature_vector.shape == (FEATURE_DIM,)
    assert np.all(feat.feature_vector == 0.0)


def test_extract_non_temporal_function():
    code = """
def compute_sum(a, b):
    # Pure arithmetic
    result = a + b
    return result * 2
"""
    results = extract_function_features(code)
    assert len(results) == 1
    feat = results[0]
    assert feat.is_valid_syntax is True
    assert feat.is_temporal is False


def test_extract_multiple_functions():
    code = """
def func_one(t):
    from datetime import datetime
    return datetime.now()

def func_two(x):
    return x * x
"""
    results = extract_function_features(code)
    assert len(results) == 2
    assert results[0].function_name == "func_one"
    assert results[0].is_temporal is True
    assert results[1].function_name == "func_two"
    assert results[1].is_temporal is False

