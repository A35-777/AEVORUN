"""Unit tests for the Aevorun Python SDK."""

from aevorun import Aevorun, AnalysisResult, PredictedScenario


def test_sdk_basic_analysis():
    model = Aevorun()
    code = """
def is_session_expired(created_at, ttl=3600):
    import time
    return (time.time() - created_at) > ttl
"""
    result = model.analyze_source(code, top_k=3)
    assert isinstance(result, AnalysisResult)
    assert len(result.functions) == 1
    fn = result.functions[0]
    assert fn.function_name == "is_session_expired"
    assert fn.is_temporal is True
    assert len(fn.scenarios) <= 3
    assert len(result.scenarios) > 0

    top_scenario = result.scenarios[0]
    assert isinstance(top_scenario, PredictedScenario)
    assert top_scenario.name in ("expiration_boundary", "timestamp_precision")
    assert top_scenario.score > 0.40
    assert len(top_scenario.recommended_test_dates) > 0


def test_sdk_json_serialization():
    model = Aevorun()
    code = "def f(t):\n    return t.replace(year=2025)\n"
    result = model.analyze_source(code)
    json_str = result.to_json()
    assert '"function_name": "f"' in json_str
    assert '"model_version": "AEVORUN-T1"' in json_str


def test_sdk_file_analysis(tmp_path):
    model = Aevorun()
    py_file = tmp_path / "temp_calc.py"
    py_file.write_text("""
def get_utc_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)
""", encoding="utf-8")

    result = model.analyze_file(py_file)
    assert len(result.functions) == 1
    assert result.functions[0].function_name == "get_utc_now"
    assert result.source_target == str(py_file)

