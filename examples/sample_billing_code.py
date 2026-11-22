"""Sample Python file containing temporal operations for AEVORUN testing."""

from datetime import datetime, timedelta
import calendar


def calculate_next_billing_cycle(subscription_start: datetime, plan_months: int = 1) -> datetime:
    """Calculates next billing renewal date.

    Notice the month-end and leap-year subtleties:
    Adding 30 days fails on 31-day months and Feb.
    """
    # Flawed duration arithmetic:
    next_date = subscription_start + timedelta(days=plan_months * 30)
    return next_date


def compute_annual_expiration(created_at: datetime, years_valid: int = 1) -> datetime:
    """Computes certificate or contract annual expiration.

    Subject to leap_day failures if created on Feb 29!
    """
    target_year = created_at.year + years_valid
    return created_at.replace(year=target_year)


def is_token_still_valid(token_timestamp: float, max_ttl_seconds: int = 3600) -> bool:
    """Verifies token expiration against current epoch timestamp."""
    import time
    now_epoch = time.time()
    return (now_epoch - token_timestamp) <= max_ttl_seconds

