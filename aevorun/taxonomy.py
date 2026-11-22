"""Taxonomy of temporal test-scenario edge cases for AEVORUN."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json
from pathlib import Path


@dataclass(frozen=True)
class Scenario:
    id: int
    name: str
    description: str
    typical_triggers: List[str]
    recommended_test_dates: List[str]


# Canonical 14 temporal edge-case scenarios
SCENARIO_LIST: List[Scenario] = [
    Scenario(
        id=0,
        name="leap_day",
        description="Calculations involving leap years, February 29th, quadrennial boundaries, or year replacement (e.g. replace(year=y+1)).",
        typical_triggers=["replace(year=...)", "days=365", "timedelta(days=366)", "calendar.isleap", "month == 2", "day == 29"],
        recommended_test_dates=["2024-02-29T12:00:00", "2020-02-29T23:59:59", "2023-02-28T12:00:00"],
    ),
    Scenario(
        id=1,
        name="month_end",
        description="Date arithmetic, month length variations (28, 29, 30, 31 days), or boundary conditions around month ends.",
        typical_triggers=["replace(month=...)", "days=30", "days=31", "monthrange", "day == 31", "day == 30"],
        recommended_test_dates=["2024-01-31T23:59:59", "2024-02-28T12:00:00", "2024-04-30T15:00:00"],
    ),
    Scenario(
        id=2,
        name="year_boundary",
        description="New Year rollovers (December 31 -> January 1), ISO week-numbering annual mismatches, or annual reset logic.",
        typical_triggers=["isocalendar", "strftime('%Y')", "strftime('%G')", "month == 12 and day == 31", "year + 1"],
        recommended_test_dates=["2023-12-31T23:59:59", "2024-01-01T00:00:00", "2024-12-31T23:59:59"],
    ),
    Scenario(
        id=3,
        name="midnight_boundary",
        description="Crossover at midnight (00:00:00 vs 23:59:59.999999), daily aggregation buckets, and inclusive vs exclusive date range endpoints.",
        typical_triggers=["time(0, 0)", "combine", "hour == 0", "hour == 23", "replace(hour=0, minute=0, second=0)", "date() <= end_date"],
        recommended_test_dates=["2024-06-15T00:00:00", "2024-06-15T23:59:59.999999"],
    ),
    Scenario(
        id=4,
        name="timezone_conversion",
        description="Converting datetimes across disparate timezone offsets (UTC, local, zoneinfo) or mixing naive and aware objects.",
        typical_triggers=["astimezone", "ZoneInfo", "timezone.utc", "pytz.timezone", "utcoffset", "tzinfo"],
        recommended_test_dates=["2024-06-15T12:00:00+00:00", "2024-06-15T21:00:00+09:00", "2024-01-15T07:00:00-05:00"],
    ),
    Scenario(
        id=5,
        name="daylight_saving_transition",
        description="Clock shifts during Daylight Saving Time (DST) spring-forward (1-hour gap) or fall-back (1-hour overlap).",
        typical_triggers=["astimezone", "localize", "ZoneInfo('America/New_York')", "ZoneInfo('Europe/London')", "dst()"],
        recommended_test_dates=["2024-03-10T01:59:59", "2024-11-03T01:30:00"],
    ),
    Scenario(
        id=6,
        name="ambiguous_local_time",
        description="Repeated wall-clock time during autumn DST fall-back transition requiring fold parameter resolution (fold=0 vs fold=1).",
        typical_triggers=["fold", "ZoneInfo", "America/New_York", "Europe/Berlin", "wall_time"],
        recommended_test_dates=["2024-11-03T01:30:00 (fold=0)", "2024-11-03T01:30:00 (fold=1)"],
    ),
    Scenario(
        id=7,
        name="nonexistent_local_time",
        description="Skipped wall-clock hour during spring DST transition (e.g. 02:30 AM does not exist in local civil time).",
        typical_triggers=["ZoneInfo", "America/New_York", "Europe/London", "replace(hour=2, minute=30)"],
        recommended_test_dates=["2024-03-10T02:30:00"],
    ),
    Scenario(
        id=8,
        name="naive_aware_mismatch",
        description="Comparing, subtracting, or sorting timezone-naive and timezone-aware datetime objects (which raises TypeError in Python).",
        typical_triggers=["datetime.now()", "datetime.utcnow()", "tzinfo is None", "t1 - t2", "t1 < t2"],
        recommended_test_dates=["Naive: 2024-06-15T12:00:00 vs Aware: 2024-06-15T12:00:00+00:00"],
    ),
    Scenario(
        id=9,
        name="timestamp_precision",
        description="Precision loss, float rounding, or unit scale mismatch (seconds vs milliseconds vs microseconds vs nanoseconds) in Unix epochs.",
        typical_triggers=["timestamp()", "fromtimestamp", "time.time()", "time.time_ns()", "1000", "1000000", "int(ts)"],
        recommended_test_dates=["1718452800.999999", "1718452800123", "0.0", "-1.0"],
    ),
    Scenario(
        id=10,
        name="calendar_duration_mismatch",
        description="Conflating calendar-variable units (months, years) with fixed physical durations (e.g. timedelta(days=30) vs 1 calendar month).",
        typical_triggers=["timedelta(days=30)", "timedelta(days=365)", "relativedelta", "dateutil.relativedelta", "next_month"],
        recommended_test_dates=["2024-01-31 + timedelta(days=30) -> 2024-03-01", "2024-02-01 + timedelta(days=30) -> 2024-03-02"],
    ),
    Scenario(
        id=11,
        name="date_parsing",
        description="Parsing malformed, boundary, or multi-format string dates (ISO 8601, RFC 3339, custom strptime format strings, missing timezone offset).",
        typical_triggers=["strptime", "fromisoformat", "dateutil.parser.parse", "isoformat", "%Y-%m-%d"],
        recommended_test_dates=["2024-02-29T23:59:59Z", "2024-00-01", "2024-12-31T24:00:00", "invalid-date"],
    ),
    Scenario(
        id=12,
        name="recurring_schedule",
        description="Recurring schedules, cron interval evaluation, weekly cadence drift, interval stepping, and weekend/holiday rollovers.",
        typical_triggers=["cron", "interval", "weekday()", "isoweekday()", "timedelta(weeks=...)", "schedule"],
        recommended_test_dates=["Sunday to Monday boundary", "Month crossover on weekly recurrence", "Leap year on annual recurrence"],
    ),
    Scenario(
        id=13,
        name="expiration_boundary",
        description="Token expiration, cache TTL, lease expiration, subscription renewal deadlines, inequality boundaries (< vs <=), and clock skew.",
        typical_triggers=["expires_at", "ttl", "valid_until", "deadline", "now >= expires", "is_expired"],
        recommended_test_dates=["Exact expiration instant (t == expires_at)", "1 millisecond before expiration", "1 millisecond after expiration"],
    ),
]

TAXONOMY: Dict[str, Scenario] = {s.name: s for s in SCENARIO_LIST}
TAXONOMY_BY_ID: Dict[int, Scenario] = {s.id: s for s in SCENARIO_LIST}
SCENARIO_NAMES: List[str] = [s.name for s in SCENARIO_LIST]
NUM_SCENARIOS = len(SCENARIO_LIST)

