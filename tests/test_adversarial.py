"""Adversarial and Out-of-Distribution Tests for AEVORUN."""

import pytest
from aevorun import Aevorun


def test_adversarial_similar_names_different_semantics():
    """Ensure two functions with similar names but different bodies receive different scenario rankings."""
    model = Aevorun()

    code_leap = """
def process_yearly_event(event_dt):
    # Year jump sensitive to leap days
    return event_dt.replace(year=event_dt.year + 1)
"""

    code_tz = """
def process_yearly_event(event_dt):
    # Timezone conversion
    from zoneinfo import ZoneInfo
    return event_dt.astimezone(ZoneInfo("Asia/Tokyo"))
"""

    res_leap = model.analyze_source(code_leap, top_k=3)
    res_tz = model.analyze_source(code_tz, top_k=3)

    scenarios_leap = [s.name for s in res_leap.scenarios]
    scenarios_tz = [s.name for s in res_tz.scenarios]

    assert "leap_day" in scenarios_leap
    assert "timezone_conversion" in scenarios_tz
    # The rankings must NOT be identical
    assert scenarios_leap != scenarios_tz


def test_adversarial_non_temporal_keywords():
    """Ensure functions with variable names like 'delta' or 'timeout' in non-temporal contexts don't get flooded."""
    model = Aevorun()

    math_code = """
def numerical_gradient(f, x, delta=1e-5):
    # Pure mathematical calculus delta, not datetime timedelta!
    return (f(x + delta) - f(x - delta)) / (2 * delta)
"""
    res = model.analyze_source(math_code)
    fn = res.functions[0]
    assert fn.is_temporal is False
    # High-confidence scenarios should not be emitted
    assert len([s for s in fn.scenarios if s.score > 0.5]) == 0


def test_adversarial_malformed_syntax():
    """Ensure invalid syntax is handled safely without throwing uncaught exceptions."""
    model = Aevorun()
    malformed = "def broken(:\n    pass???"
    res = model.analyze_source(malformed)
    assert len(res.functions) == 1
    assert res.functions[0].is_valid_syntax is False
    assert res.functions[0].scenarios == []


def test_adversarial_async_function():
    """Ensure async functions and decorators parse properly."""
    model = Aevorun()
    async_code = """
@some_decorator
async def fetch_scheduled_data(start_time):
    from datetime import timedelta
    next_time = start_time + timedelta(hours=24)
    return await db.fetch(next_time)
"""
    res = model.analyze_source(async_code)
    assert len(res.functions) == 1
    fn = res.functions[0]
    assert fn.function_name == "fetch_scheduled_data"
    assert fn.is_valid_syntax is True
    assert fn.is_temporal is True

