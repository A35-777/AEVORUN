"""Independent baseline models for temporal test-scenario prioritization.

Implements:
1. Frequency-based scenario prediction (empirical class priors)
2. Hand-crafted static heuristic baseline (AST & token rule-based scoring)
3. Classical Logistic Regression baseline
4. Gradient-Boosted Trees baseline (HistGradientBoosting / RandomForest)
"""

from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.multioutput import MultiOutputClassifier

from aevorun.taxonomy import NUM_SCENARIOS, SCENARIO_NAMES
from aevorun.features import FEATURE_NAMES, FEATURE_INDEX_MAP


class FrequencyBaseline:
    """Predicts fixed empirical prior probabilities learned from the training set."""

    def __init__(self):
        self.frequencies: np.ndarray = np.zeros(NUM_SCENARIOS, dtype=np.float32)

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit empirical class frequencies."""
        # y is shape (N, NUM_SCENARIOS)
        if len(y) > 0:
            self.frequencies = np.mean(y, axis=0).astype(np.float32)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return broadcasted prior frequencies for each sample."""
        n_samples = len(X)
        return np.tile(self.frequencies, (n_samples, 1))

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        proba = self.predict_proba(X)
        return (proba >= threshold).astype(np.int32)


class HeuristicBaseline:
    """Hand-crafted rule-based static heuristic model using AST features."""

    def __init__(self):
        pass

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Static heuristics do not require training weights."""
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Compute rule-based scenario scores from AST feature vectors."""
        n_samples = len(X)
        probs = np.zeros((n_samples, NUM_SCENARIOS), dtype=np.float32)

        for i in range(n_samples):
            vec = X[i]

            def f(name: str) -> float:
                return vec[FEATURE_INDEX_MAP[name]]

            # 0: leap_day
            s_leap = 0.0
            if f("call_replace_year") > 0:
                s_leap += 0.85
            if f("call_calendar_isleap") > 0:
                s_leap += 0.90
            if f("const_365_or_366") > 0:
                s_leap += 0.60
            if f("name_leap_feb") > 0:
                s_leap += 0.50
            probs[i, 0] = min(s_leap, 0.99)

            # 1: month_end
            s_month = 0.0
            if f("call_replace_month") > 0:
                s_month += 0.80
            if f("call_monthrange") > 0:
                s_month += 0.85
            if f("const_28_to_31") > 0:
                s_month += 0.55
            if f("name_month_year_annual") > 0 and (f("call_timedelta") > 0 or f("call_relativedelta") > 0):
                s_month += 0.65
            probs[i, 1] = min(s_month, 0.99)

            # 2: year_boundary
            s_yr = 0.0
            if f("const_365_or_366") > 0:
                s_yr += 0.50
            if f("name_month_year_annual") > 0:
                s_yr += 0.35
            if f("call_strftime") > 0 and f("name_month_year_annual") > 0:
                s_yr += 0.55
            probs[i, 2] = min(s_yr, 0.99)

            # 3: midnight_boundary
            s_mid = 0.0
            if f("const_23_or_24") > 0 or f("const_0") > 0:
                s_mid += 0.40
            if f("name_midnight_night_day") > 0:
                s_mid += 0.50
            if f("call_replace_hour") > 0:
                s_mid += 0.70
            probs[i, 3] = min(s_mid, 0.99)

            # 4: timezone_conversion
            s_tz = 0.0
            if f("call_astimezone") > 0:
                s_tz += 0.90
            if f("call_zoneinfo") > 0 or f("import_zoneinfo") > 0 or f("import_pytz") > 0:
                s_tz += 0.75
            if f("name_utc_tz_zone_offset") > 0:
                s_tz += 0.60
            probs[i, 4] = min(s_tz, 0.99)

            # 5: daylight_saving_transition
            s_dst = 0.0
            if f("name_fold_dst_ambiguous") > 0:
                s_dst += 0.80
            if (f("call_zoneinfo") > 0 or f("import_zoneinfo") > 0) and f("call_astimezone") > 0:
                s_dst += 0.70
            probs[i, 5] = min(s_dst, 0.99)

            # 6: ambiguous_local_time
            s_ambig = 0.0
            if f("kwarg_fold") > 0:
                s_ambig += 0.95
            if f("name_fold_dst_ambiguous") > 0:
                s_ambig += 0.60
            probs[i, 6] = min(s_ambig, 0.99)

            # 7: nonexistent_local_time
            s_nonexist = 0.0
            if f("name_fold_dst_ambiguous") > 0 and f("call_replace") > 0:
                s_nonexist += 0.70
            probs[i, 7] = min(s_nonexist, 0.99)

            # 8: naive_aware_mismatch
            s_naive = 0.0
            if f("call_datetime_now") > 0 and f("name_utc_tz_zone_offset") > 0:
                s_naive += 0.85
            if f("call_datetime_utcnow") > 0:
                s_naive += 0.80
            if f("call_replace_tzinfo") > 0:
                s_naive += 0.75
            probs[i, 8] = min(s_naive, 0.99)

            # 9: timestamp_precision
            s_ts = 0.0
            if f("call_timestamp") > 0 or f("call_fromtimestamp") > 0 or f("call_time_time") > 0:
                s_ts += 0.80
            if f("const_1000") > 0 or f("kwarg_milliseconds") > 0 or f("kwarg_microseconds") > 0:
                s_ts += 0.70
            if f("name_timestamp_epoch") > 0:
                s_ts += 0.50
            probs[i, 9] = min(s_ts, 0.99)

            # 10: calendar_duration_mismatch
            s_cal = 0.0
            if f("call_timedelta") > 0 and (f("const_365_or_366") > 0 or f("const_28_to_31") > 0 or f("kwarg_days") > 0):
                s_cal += 0.85
            if f("name_month_year_annual") > 0 and f("call_timedelta") > 0:
                s_cal += 0.75
            probs[i, 10] = min(s_cal, 0.99)

            # 11: date_parsing
            s_parse = 0.0
            if f("call_strptime") > 0 or f("call_fromisoformat") > 0:
                s_parse += 0.90
            if f("name_parse_format_iso") > 0:
                s_parse += 0.65
            probs[i, 11] = min(s_parse, 0.99)

            # 12: recurring_schedule
            s_sched = 0.0
            if f("name_schedule_cron_interval") > 0:
                s_sched += 0.80
            if f("call_weekday_or_iso") > 0:
                s_sched += 0.75
            if f("op_modulo") > 0 and f("call_timedelta") > 0:
                s_sched += 0.70
            probs[i, 12] = min(s_sched, 0.99)

            # 13: expiration_boundary
            s_exp = 0.0
            if f("name_expire_ttl_deadline") > 0:
                s_exp += 0.85
            if (f("op_compare_lt_le") > 0 or f("op_compare_gt_ge") > 0) and (f("call_datetime_now") > 0 or f("call_time_time") > 0):
                s_exp += 0.75
            probs[i, 13] = min(s_exp, 0.99)

        # Baseline background noise calibration
        probs = np.clip(probs, 0.01, 0.99)
        return probs

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(np.int32)


class LogisticRegressionBaseline:
    """Multi-label Logistic Regression baseline with L2 regularization."""

    def __init__(self, C: float = 1.0, random_state: int = 42):
        self.model = MultiOutputClassifier(
            LogisticRegression(C=C, max_iter=500, random_state=random_state, class_weight="balanced")
        )

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        # MultiOutputClassifier.predict_proba returns a list of arrays [(N, 2), ...]
        proba_list = self.model.predict_proba(X)
        n_samples = len(X)
        probs = np.zeros((n_samples, NUM_SCENARIOS), dtype=np.float32)
        for j, p in enumerate(proba_list):
            if p.shape[1] == 2:
                probs[:, j] = p[:, 1]
            else:
                # If a class had only 1 label in train
                probs[:, j] = 0.0
        return probs

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(np.int32)


class GradientBoostedTreeBaseline:
    """Multi-label Random Forest / Gradient Boosted baseline."""

    def __init__(self, n_estimators: int = 60, max_depth: int = 8, random_state: int = 42):
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            class_weight="balanced_subsample",
            n_jobs=-1
        )

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        proba_list = self.model.predict_proba(X)
        n_samples = len(X)
        probs = np.zeros((n_samples, NUM_SCENARIOS), dtype=np.float32)
        for j, p in enumerate(proba_list):
            if p.shape[1] == 2:
                probs[:, j] = p[:, 1]
            else:
                probs[:, j] = 0.0
        return probs

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(np.int32)

