"""Unit tests for the PRM health-scoring engine (calculation boundaries)."""

import pytest

from app import (
    AT_RISK_THRESHOLD,
    STABLE_THRESHOLD,
    categorize,
    score_seat_utilization,
    score_sync,
    score_triage,
    weighted_health_score,
)


def test_sync_score_upper_clamp():
    # Compliance above 100% is clamped down to the 100 ceiling.
    assert score_sync(120.0) == 100.0


def test_sync_score_lower_clamp():
    # Negative compliance is clamped up to the 0 floor.
    assert score_sync(-10.0) == 0.0


def test_triage_score_meets_sla():
    # Triage at (or faster than) the SLA target earns a perfect score.
    assert score_triage(2.0) == 100.0
    assert score_triage(0.5) == 100.0


def test_triage_score_breaches_max():
    # Triage at (or beyond) the max threshold earns zero.
    assert score_triage(24.0) == 0.0
    assert score_triage(40.0) == 0.0


def test_triage_score_linear_midpoint():
    # 13h is the midpoint between the 2h target and 24h max -> 50.
    assert score_triage(13.0) == pytest.approx(50.0)


def test_seat_utilization_full_and_overflow():
    # Logins equal to seats -> 100; logins above seats stay clamped at 100.
    assert score_seat_utilization(10, 10) == 100.0
    assert score_seat_utilization(15, 10) == 100.0


def test_seat_utilization_handles_zero_seats():
    # Zero licensed seats must not divide by zero; it scores 0.
    assert score_seat_utilization(5, 0) == 0.0


def test_weighted_health_score_matches_manual():
    # 0.45*80 + 0.35*60 + 0.20*50 = 36 + 21 + 10 = 67.0
    assert weighted_health_score(80.0, 60.0, 50.0) == pytest.approx(67.0)


def test_categorize_stable_and_at_risk_boundaries():
    # 80 is the inclusive Stable boundary; just below falls to At-Risk.
    assert categorize(STABLE_THRESHOLD) == "Stable"
    assert categorize(79.99) == "At-Risk"
    assert categorize(AT_RISK_THRESHOLD) == "At-Risk"


def test_categorize_critical_boundary():
    # Anything below the At-Risk floor is Critical.
    assert categorize(59.99) == "Critical"
    assert categorize(0.0) == "Critical"
