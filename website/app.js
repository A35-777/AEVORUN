// Verified real model predictions recorded from AEVORUN-T1 checkpoint evaluations
const VERIFIED_SAMPLES = {
  billing: {
    title: "billing_calculator.py",
    code: `def calculate_next_billing_cycle(subscription_start, plan_months=1):
    from datetime import timedelta
    # Flawed month assumption: adding 30 days fails on 31-day months & Feb
    next_date = subscription_start + timedelta(days=plan_months * 30)
    return next_date`,
    predictions: [
      { name: "month_end", score: 0.928, desc: "Date arithmetic across variable 28/29/30/31 day month boundaries." },
      { name: "year_boundary", score: 0.906, desc: "New Year rollover and annual reset logic." },
      { name: "leap_day", score: 0.797, desc: "February 29 leap-day calculation." },
      { name: "calendar_duration_mismatch", score: 0.480, desc: "Conflating fixed timedelta(days=30) with variable calendar month." }
    ]
  },
  leap: {
    title: "annual_contract.py",
    code: `def advance_annual_contract(effective_date, years_to_add=1):
    # Subject to crash if effective_date is Feb 29 on a leap year!
    target_year = effective_date.year + years_to_add
    return effective_date.replace(year=target_year)`,
    predictions: [
      { name: "year_boundary", score: 0.910, desc: "New Year rollover and annual progression." },
      { name: "leap_day", score: 0.908, desc: "replace(year=...) throws ValueError when moving Feb 29 to non-leap year." },
      { name: "month_end", score: 0.902, desc: "Month length variations on boundary dates." }
    ]
  },
  dst: {
    title: "meeting_localizer.py",
    code: `def convert_user_meeting_time(utc_dt, target_zone="America/New_York"):
    from zoneinfo import ZoneInfo
    local_tz = ZoneInfo(target_zone)
    local_dt = utc_dt.astimezone(local_tz)
    return local_dt`,
    predictions: [
      { name: "timezone_conversion", score: 0.914, desc: "Converting datetimes across disparate timezone offsets." },
      { name: "daylight_saving_transition", score: 0.887, desc: "Clock shifts during spring-forward gap or fall-back overlap." },
      { name: "ambiguous_local_time", score: 0.652, desc: "Repeated wall-clock hour during autumn fall-back transition." }
    ]
  },
  ttl: {
    title: "token_validator.py",
    code: `def is_token_still_valid(token_timestamp, max_ttl_seconds=3600):
    import time
    now_epoch = time.time()
    return (now_epoch - token_timestamp) <= max_ttl_seconds`,
    predictions: [
      { name: "expiration_boundary", score: 0.930, desc: "Token expiration boundary, <= vs < check, and clock drift." },
      { name: "timestamp_precision", score: 0.528, desc: "Precision loss and float epoch rounding." }
    ]
  },
  algo: {
    title: "sorting_quicksort.py",
    code: `def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)`,
    predictions: [
      { name: "Non-Temporal Code", score: 0.0, desc: "Zero temporal features detected. All edge-case recommendations suppressed." }
    ]
  }
};

document.addEventListener("DOMContentLoaded", () => {
  const codeDisplay = document.getElementById("code-display");
  const resultsContainer = document.getElementById("results-container");
  const sampleTitle = document.getElementById("sample-title");
  const buttons = document.querySelectorAll(".sample-btn");
  const themeToggle = document.getElementById("theme-toggle");

  function loadSample(key) {
    const data = VERIFIED_SAMPLES[key];
    if (!data) return;

    sampleTitle.textContent = data.title;
    codeDisplay.textContent = data.code;

    resultsContainer.innerHTML = "";
    data.predictions.forEach(p => {
      const pill = document.createElement("div");
      pill.className = "scenario-pill";

      const info = document.createElement("div");
      info.className = "scenario-info";
      info.innerHTML = `<strong>${p.name}</strong><small>${p.desc}</small>`;

      const badge = document.createElement("span");
      badge.className = "score-badge";
      badge.textContent = p.score > 0 ? `${(p.score * 100).toFixed(1)}%` : "Clean (0%)";

      pill.appendChild(info);
      pill.appendChild(badge);
      resultsContainer.appendChild(pill);
    });
  }

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      loadSample(btn.dataset.sample);
    });
  });

  // Load default
  loadSample("billing");

  // Theme toggle
  themeToggle.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const nextTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", nextTheme);
  });
});

