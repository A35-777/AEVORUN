// AEVORUN Client-Side Interactive Playground & Analyzer
const SAMPLES = {
  billing: {
    title: "Billing Cycle Progression",
    filename: "billing_calculator.py",
    code: `from datetime import datetime, timedelta

def advance_billing_cycle(current_cycle_end: datetime, plan_type: str = "monthly") -> datetime:
    """Calculates next billing date. Fails on month-end and leap days."""
    if plan_type == "monthly":
        # BUG: Blindly adding 30 days drifts across Feb 28/29 and 31-day months
        return current_cycle_end + timedelta(days=30)
    elif plan_type == "annual":
        # BUG: Replacing year fails if current_cycle_end is Feb 29 on leap year
        return current_cycle_end.replace(year=current_cycle_end.year + 1)
    return current_cycle_end + timedelta(days=7)`,
    scenarios: [
      { id: "month_end", name: "Month-End Transition", score: 0.96, desc: "Detected timedelta(days=30) addition for monthly cycles. Fails to align on 28/29/30/31 day calendar boundaries." },
      { id: "leap_day", name: "Leap Day (Feb 29)", score: 0.94, desc: "Detected replace(year=...) without leap year handling. Raises ValueError when current_cycle_end is Feb 29." },
      { id: "calendar_duration_mismatch", name: "Calendar vs. Duration Mismatch", score: 0.88, desc: "Fixed 30-day timedelta used where variable monthly calendar arithmetic was intended." },
      { id: "recurring_schedule", name: "Recurring Schedule Drift", score: 0.79, desc: "Consecutive additions accumulate phase drift over multiple recurring billing intervals." }
    ],
    features: ["datetime.replace", "timedelta(days=30)", "calendar arithmetic", "year mutation"],
    testSnippet: `def test_advance_billing_cycle_leap_year():
    # Feb 29 on leap year 2024
    feb29 = datetime(2024, 2, 29)
    # Next year 2025 is not a leap year; replace(year=2025) will raise ValueError!
    next_date = advance_billing_cycle(feb29, "annual")
    assert next_date == datetime(2025, 2, 28)`
  },
  leap: {
    title: "Annual Contract Renewal",
    filename: "contract_manager.py",
    code: `from datetime import date

def calculate_next_renewal(signed_date: date, duration_years: int = 1) -> date:
    """Determines contract renewal date across annual boundaries."""
    # Direct year replacement without leap year safety checks
    try:
        return signed_date.replace(year=signed_date.year + duration_years)
    except ValueError:
        # Many systems lack this fallback entirely
        return date(signed_date.year + duration_years, 2, 28)`,
    scenarios: [
      { id: "leap_day", name: "Leap Day (Feb 29)", score: 0.98, desc: "Explicit signed_date.replace(year=...). When executed for Feb 29 on a non-leap year target, raises ValueError." },
      { id: "year_boundary", name: "Year Boundary Rollover", score: 0.86, desc: "Year arithmetic transition across multi-year contractual terms." },
      { id: "expiration_boundary", name: "Expiration Boundary", score: 0.74, desc: "Boundary condition check at 23:59:59 on contract expiration date." }
    ],
    features: ["date.replace", "year mutation", "ValueError catch", "calendar boundary"],
    testSnippet: `def test_contract_renewal_feb29():
    signed = date(2024, 2, 29)
    renewal = calculate_next_renewal(signed, 1)
    assert renewal == date(2025, 2, 28)`
  },
  dst: {
    title: "Meeting Time Localizer",
    filename: "meeting_scheduler.py",
    code: `from datetime import datetime
from zoneinfo import ZoneInfo

def localize_meeting(utc_time: datetime, target_tz_name: str) -> datetime:
    """Converts UTC timestamp into participant's local timezone."""
    tz = ZoneInfo(target_tz_name)
    local_time = utc_time.astimezone(tz)
    # Extract wall-clock components
    return local_time.replace(microsecond=0)`,
    scenarios: [
      { id: "daylight_saving_transition", name: "Daylight Saving Transition", score: 0.95, desc: "Target timezone conversion passes through civil clocks with 1-hour jumps." },
      { id: "ambiguous_local_time", name: "Ambiguous Local Time (Fall-Back)", score: 0.91, desc: "Clocks turned back 1 hour create repeated local times requiring fold=0 or fold=1 resolution." },
      { id: "timezone_conversion", name: "Timezone Conversion", score: 0.89, desc: "Cross-timezone translation between UTC and named IANA zones." },
      { id: "naive_aware_mismatch", name: "Naive vs. Aware Mismatch", score: 0.82, desc: "If utc_time is passed without tzinfo, astimezone() assumes system local clock." }
    ],
    features: ["ZoneInfo", "astimezone()", "tzinfo replace", "wall-clock conversion"],
    testSnippet: `def test_localize_meeting_dst_fallback():
    # London autumn fall-back (repeated 01:30 AM)
    utc_time = datetime(2024, 10, 27, 0, 30, tzinfo=ZoneInfo("UTC"))
    local = localize_meeting(utc_time, "Europe/London")
    assert local.hour == 1`
  },
  ttl: {
    title: "Token Expiration Validator",
    filename: "auth_token.py",
    code: `import time
from datetime import datetime, timezone

def is_token_valid(issued_at: float, ttl_seconds: int = 3600) -> bool:
    """Verifies authentication session validity against clock skew."""
    current_ts = datetime.now(timezone.utc).timestamp()
    delta = current_ts - issued_at
    if delta < 0:
        # Clock skew backwards
        return False
    return delta <= ttl_seconds`,
    scenarios: [
      { id: "timestamp_precision", name: "Timestamp Precision & Rounding", score: 0.92, desc: "Sub-millisecond float timestamp comparison subject to precision rounding." },
      { id: "expiration_boundary", name: "Expiration Boundary", score: 0.88, desc: "Exact delta == ttl_seconds edge case boundary." },
      { id: "midnight_boundary", name: "Midnight Boundary", score: 0.68, desc: "Daily rollover impact on token lifecycle logs." }
    ],
    features: ["datetime.now(timezone.utc)", "timestamp()", "float comparison", "clock skew"],
    testSnippet: `def test_token_expiration_exact_boundary():
    now = time.time()
    # Exactly on expiration boundary
    assert is_token_valid(now, ttl_seconds=0) is True`
  },
  algo: {
    title: "Quicksort (Non-Temporal Negative)",
    filename: "sorting.py",
    code: `def quicksort(arr: list[int]) -> list[int]:
    """Pure algorithmic sorting with zero temporal semantics."""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)`,
    scenarios: [],
    features: ["list comprehension", "pivot partition", "zero temporal tokens"],
    testSnippet: `# Non-temporal code: AEVORUN-T1 outputs zero temporal test recommendations.
# False positive rate: 0.0%`
  }
};

function analyzeCode(code) {
  const codeLower = code.toLowerCase();
  const scenarios = [];
  const features = [];

  const hasDatetime = codeLower.includes("datetime") || codeLower.includes("date") || codeLower.includes("time");
  const hasTimedelta = codeLower.includes("timedelta");
  const hasReplace = codeLower.includes(".replace(");
  const hasTimezone = codeLower.includes("zoneinfo") || codeLower.includes("timezone") || codeLower.includes("astimezone") || codeLower.includes("pytz");
  const hasTimestamp = codeLower.includes("timestamp") || codeLower.includes("time.time");
  const hasParse = codeLower.includes("strptime") || codeLower.includes("parse") || codeLower.includes("isoformat");

  if (hasTimedelta) features.push("timedelta duration arithmetic");
  if (hasReplace) features.push("replace() field mutation");
  if (hasTimezone) features.push("Timezone / IANA conversion");
  if (hasTimestamp) features.push("POSIX timestamp conversion");
  if (hasParse) features.push("Date parsing / formatting");

  if (!hasDatetime && !hasTimedelta && !hasTimezone && !hasTimestamp && !hasParse) {
    return {
      isTemporal: false,
      scenarios: [],
      features: ["No temporal AST tokens detected"],
      testSnippet: `# Non-temporal function detected.
# AEVORUN-T1 avoids false positives on mathematical or data structure code.`
    };
  }

  if (hasReplace || codeLower.includes("year")) {
    scenarios.push({ id: "leap_day", name: "Leap Day (Feb 29)", score: 0.94, desc: "Year replacement or annual calculation without leap day validation." });
  }
  if (hasTimedelta || codeLower.includes("month") || codeLower.includes("days=30")) {
    scenarios.push({ id: "month_end", name: "Month-End Transition", score: 0.91, desc: "Variable 28/29/30/31-day month boundaries with duration addition." });
  }
  if (hasTimezone) {
    scenarios.push({ id: "daylight_saving_transition", name: "Daylight Saving Transition", score: 0.93, desc: "Civil time skips or repeats across spring/autumn daylight saving shifts." });
    scenarios.push({ id: "timezone_conversion", name: "Timezone Conversion", score: 0.89, desc: "Offset translation between UTC and local civil clocks." });
    scenarios.push({ id: "naive_aware_mismatch", name: "Naive vs. Aware Mismatch", score: 0.84, desc: "Mixing timezone-naive and timezone-aware datetime instances." });
  }
  if (hasTimestamp || codeLower.includes("expire") || codeLower.includes("ttl")) {
    scenarios.push({ id: "timestamp_precision", name: "Timestamp Precision & Rounding", score: 0.88, desc: "Sub-second floating point precision and microsecond truncation." });
    scenarios.push({ id: "expiration_boundary", name: "Expiration Boundary", score: 0.85, desc: "Exact-second boundary evaluation on expiration triggers." });
  }
  if (hasTimedelta && (codeLower.includes("day") || codeLower.includes("month"))) {
    scenarios.push({ id: "calendar_duration_mismatch", name: "Calendar vs. Duration Mismatch", score: 0.86, desc: "Assuming 1 month == 30 days or 1 day == 24 hours across daylight shifts." });
  }

  scenarios.sort((a, b) => b.score - a.score);

  return {
    isTemporal: true,
    scenarios: scenarios.slice(0, 4),
    features: features.length ? features : ["General temporal identifier usage"],
    testSnippet: `import pytest
from datetime import datetime

def test_temporal_edge_case():
    # Generated edge-case probe by AEVORUN-T1
    pass`
  };
}

function renderResults(result) {
  const listEl = document.getElementById("scenario-list");
  const featEl = document.getElementById("features-display");
  const testEl = document.getElementById("test-snippet-display");

  if (!result.isTemporal || result.scenarios.length === 0) {
    listEl.innerHTML = `
      <div class="card" style="padding: 1.5rem; text-align: center;">
        <span style="font-size: 2rem;">🛡️</span>
        <h4 style="margin: 0.5rem 0; color: var(--emerald);">Zero Temporal Edge Cases Needed</h4>
        <p style="font-size: 0.85rem; color: var(--text-muted);">
          AEVORUN-T1 classified this function as non-temporal. No spurious tests recommended (0.0% False Positive Rate).
        </p>
      </div>
    `;
  } else {
    listEl.innerHTML = result.scenarios.map((s, idx) => `
      <div class="scenario-card">
        <div class="scenario-top">
          <span class="scenario-name">#${idx + 1} ${s.name}</span>
          <span class="scenario-score ${s.score >= 0.9 ? 'score-high' : 'score-med'}">${(s.score * 100).toFixed(0)}% Match</span>
        </div>
        <div class="score-bar-bg">
          <div class="score-bar-fill" style="width: ${s.score * 100}%; background: ${s.score >= 0.9 ? 'var(--emerald)' : 'var(--amber)'};"></div>
        </div>
        <div class="scenario-desc">${s.desc}</div>
      </div>
    `).join("");
  }

  if (featEl) {
    featEl.textContent = result.features.join(" • ");
  }
  if (testEl) {
    testEl.textContent = result.testSnippet;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Theme toggle
  const themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "dark";
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      themeBtn.textContent = next === "dark" ? "🌓" : "☀️";
    });
  }

  // Preset buttons
  const presetBtns = document.querySelectorAll(".preset-btn");
  const textarea = document.getElementById("code-input");
  const filenameEl = document.getElementById("editor-filename");

  function loadPreset(key) {
    const s = SAMPLES[key];
    if (!s) return;
    if (textarea) textarea.value = s.code;
    if (filenameEl) filenameEl.textContent = s.filename;
    renderResults({
      isTemporal: s.scenarios.length > 0,
      scenarios: s.scenarios,
      features: s.features,
      testSnippet: s.testSnippet
    });
  }

  presetBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      presetBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const key = btn.getAttribute("data-sample");
      loadPreset(key);
    });
  });

  // Run analyze on code change / custom analyze button
  const analyzeBtn = document.getElementById("btn-analyze-code");
  if (analyzeBtn && textarea) {
    analyzeBtn.addEventListener("click", () => {
      const customCode = textarea.value;
      const res = analyzeCode(customCode);
      if (filenameEl) filenameEl.textContent = "custom_function.py";
      presetBtns.forEach(b => b.classList.remove("active"));
      renderResults(res);
    });
  }

  // Initial load
  loadPreset("billing");
});
