"""
Patient Remote Monitoring - Customer Health Scoring Platform
============================================================

A single-file, production-ready Streamlit application for a B2B2C Patient
Remote Monitoring company. It scores the health of every clinic (B2B customer)
using three telemetry signals:

    * B2C Sync Compliance  (45%) - % of patients syncing their devices
    * B2B Alert Triage     (35%) - avg hours for staff to triage clinical alerts
    * Seat Utilization     (20%) - active clinician logins vs licensed seats

Each account is categorized as Stable, At-Risk, or Critical.

Run locally:
    pip install streamlit pandas
    streamlit run app.py

Unit tests: see the commented-out pytest suite at the very bottom of this file.
"""

from __future__ import annotations

import os
import random
import sqlite3
from datetime import date, timedelta

# NOTE: pandas and streamlit are imported lazily inside the functions that use
# them. This keeps the pure calculation engine (and its unit tests) importable
# with zero third-party dependencies installed.


# ---------------------------------------------------------------------------
# Configuration & constants
# ---------------------------------------------------------------------------

# SQLite database file location (overridable for tests / deployments).
DB_PATH = os.environ.get("PRM_DB_PATH", "patient_monitoring.db")

# Amount of historical telemetry generated per clinic during seeding.
TELEMETRY_DAYS = 30

# Composite health-score weights. These MUST sum to 1.0.
WEIGHT_SYNC = 0.45     # B2C patient sync compliance
WEIGHT_TRIAGE = 0.35   # B2B alert triage responsiveness
WEIGHT_SEAT = 0.20     # Seat / license utilization

# Alert-triage SLA thresholds (hours) used to normalize triage time into a
# 0-100 score. Meeting the TARGET (or faster) scores 100; hitting the MAX
# (or slower) scores 0.
TRIAGE_TARGET_HOURS = 2.0
TRIAGE_MAX_HOURS = 24.0

# Health-score category thresholds (inclusive lower bounds).
STABLE_THRESHOLD = 80.0    # score >= 80       -> Stable
AT_RISK_THRESHOLD = 60.0   # 60 <= score < 80  -> At-Risk
                           # score < 60        -> Critical

# Deterministic seed so the mock dataset is reproducible across runs.
RANDOM_SEED = 42

# Trend classification: a recent-vs-prior health-score delta inside this band
# reads as "flat" rather than a real improvement/decline.
TREND_FLAT_THRESHOLD = 2.0

# Sort priority for the attention list: worse status first, and within a
# status, higher-value plans first (an Enterprise account slipping is a
# bigger deal than a Starter account at the same health score).
STATUS_PRIORITY = {"Critical": 0, "At-Risk": 1, "Stable": 2}
PLAN_PRIORITY = {"Enterprise": 0, "Growth": 1, "Starter": 2}

# Static clinic roster used to seed the database. Each profile defines the
# behavioral "center of gravity" for that account's generated telemetry:
#   (name, plan_tier, licensed_seats, sync_mean, triage_mean_hours, login_ratio)
CLINIC_PROFILES = [
    ("Cascade Family Health",      "Enterprise", 25, 93.0,  1.5, 0.90),
    ("Harbor Point Cardiology",    "Enterprise", 18, 86.0,  3.0, 0.80),
    ("Ridgeline Community Clinic", "Growth",      12, 74.0,  7.5, 0.62),
    ("Sunset Valley Medical",      "Growth",      10, 56.0, 14.0, 0.45),
    ("Metro Wellness Group",       "Starter",      8, 66.0, 10.0, 0.55),
]


# ---------------------------------------------------------------------------
# Calculation engine (pure functions - unit tested at the bottom of this file)
# ---------------------------------------------------------------------------

def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Constrain *value* to the inclusive range [low, high]."""
    return max(low, min(high, value))


def score_sync(compliance_pct: float) -> float:
    """Score B2C patient sync compliance.

    Compliance is already a percentage, so the score is simply the value
    clamped into the valid 0-100 range.
    """
    return clamp(compliance_pct)


def score_triage(hours: float,
                 target_hours: float = TRIAGE_TARGET_HOURS,
                 max_hours: float = TRIAGE_MAX_HOURS) -> float:
    """Score B2B alert-triage responsiveness (fewer hours == better).

    Triage time is normalized linearly: <= target -> 100, >= max -> 0.
    """
    span = max_hours - target_hours
    if span <= 0:
        # Degenerate configuration guard: avoid divide-by-zero.
        return 100.0 if hours <= target_hours else 0.0
    return clamp(100.0 * (max_hours - hours) / span)


def score_seat_utilization(avg_logins: float, licensed_seats: int) -> float:
    """Score seat utilization (active clinician logins vs licensed seats)."""
    if licensed_seats <= 0:
        # No licensed seats means there is nothing to utilize.
        return 0.0
    return clamp(100.0 * avg_logins / licensed_seats)


def weighted_health_score(sync: float, triage: float, seat: float) -> float:
    """Combine the three sub-scores into a single weighted composite (0-100)."""
    composite = WEIGHT_SYNC * sync + WEIGHT_TRIAGE * triage + WEIGHT_SEAT * seat
    return round(composite, 2)


def categorize(score: float) -> str:
    """Map a composite health score to an account-health category."""
    if score >= STABLE_THRESHOLD:
        return "Stable"
    if score >= AT_RISK_THRESHOLD:
        return "At-Risk"
    return "Critical"


def trend_label(delta: float) -> str:
    """Convert a recent-vs-prior health-score delta into a compact label."""
    if delta >= TREND_FLAT_THRESHOLD:
        return f"↑ +{delta:.1f}"
    if delta <= -TREND_FLAT_THRESHOLD:
        return f"↓ {delta:.1f}"
    return "→ flat"


# ---------------------------------------------------------------------------
# Database layer (auto-initialize + seed)
# ---------------------------------------------------------------------------

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection with dict-like row access."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create the schema if it does not already exist."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS clinics (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT    NOT NULL UNIQUE,
            plan_tier      TEXT    NOT NULL,
            licensed_seats INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS telemetry (
            id                       INTEGER PRIMARY KEY AUTOINCREMENT,
            clinic_id                INTEGER NOT NULL,
            metric_date              TEXT    NOT NULL,
            patient_sync_compliance  REAL    NOT NULL,  -- percent (0-100)
            alert_triage_hours       REAL    NOT NULL,  -- avg hours to triage
            clinician_login_count    INTEGER NOT NULL,  -- daily active logins
            FOREIGN KEY (clinic_id) REFERENCES clinics (id),
            UNIQUE (clinic_id, metric_date)
        );
        """
    )
    conn.commit()


def seed_db(conn: sqlite3.Connection) -> None:
    """Populate mock clinics + telemetry, but only when the DB is empty."""
    already_seeded = conn.execute("SELECT COUNT(*) FROM clinics").fetchone()[0]
    if already_seeded:
        return  # Idempotent: never double-seed an existing database.

    rng = random.Random(RANDOM_SEED)
    today = date.today()

    for name, plan_tier, seats, sync_mean, triage_mean, login_ratio in CLINIC_PROFILES:
        cursor = conn.execute(
            "INSERT INTO clinics (name, plan_tier, licensed_seats) VALUES (?, ?, ?)",
            (name, plan_tier, seats),
        )
        clinic_id = cursor.lastrowid

        for offset in range(TELEMETRY_DAYS):
            metric_day = today - timedelta(days=(TELEMETRY_DAYS - 1 - offset))

            # Generate noisy-but-plausible daily telemetry around the profile.
            sync = clamp(rng.gauss(sync_mean, 4.0))
            triage = max(0.1, rng.gauss(triage_mean, 1.5))
            logins = int(round(clamp(rng.gauss(login_ratio * seats, 1.2), 0, seats)))

            conn.execute(
                """
                INSERT INTO telemetry (
                    clinic_id, metric_date, patient_sync_compliance,
                    alert_triage_hours, clinician_login_count
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (clinic_id, metric_day.isoformat(), round(sync, 2),
                 round(triage, 2), logins),
            )

    conn.commit()


def ensure_database(db_path: str = DB_PATH) -> None:
    """Idempotently create and seed the database (safe to call every run)."""
    conn = get_connection(db_path)
    try:
        init_db(conn)
        seed_db(conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Scorecard aggregation (raw telemetry -> per-account health scores)
# ---------------------------------------------------------------------------

def build_scorecard(db_path: str = DB_PATH) -> pd.DataFrame:
    """Aggregate telemetry per clinic, compute weighted health scores, and
    derive a trend (recent-half vs. prior-half average) for each account.

    Returned rows are sorted worst-health-first so downstream views default
    to surfacing risk instead of alphabetical order.
    """
    import pandas as pd

    conn = get_connection(db_path)
    try:
        clinics = pd.read_sql_query(
            "SELECT id, name, plan_tier, licensed_seats FROM clinics", conn
        )
        telemetry = pd.read_sql_query("SELECT * FROM telemetry", conn)
    finally:
        conn.close()

    telemetry = telemetry.merge(clinics, left_on="clinic_id", right_on="id")
    telemetry["metric_date"] = pd.to_datetime(telemetry["metric_date"])
    telemetry["health_row"] = telemetry.apply(
        lambda r: weighted_health_score(
            score_sync(r["patient_sync_compliance"]),
            score_triage(r["alert_triage_hours"]),
            score_seat_utilization(r["clinician_login_count"], r["licensed_seats"]),
        ),
        axis=1,
    )

    records = []
    for _, group in telemetry.groupby("clinic_id"):
        group = group.sort_values("metric_date")
        midpoint = len(group) // 2
        older_half, recent_half = group.iloc[:midpoint], group.iloc[midpoint:]
        trend_delta = (
            recent_half["health_row"].mean() - older_half["health_row"].mean()
            if len(older_half) and len(recent_half)
            else 0.0
        )

        clinic_row = group.iloc[0]
        avg_sync = group["patient_sync_compliance"].mean()
        avg_triage_hours = group["alert_triage_hours"].mean()
        avg_logins = group["clinician_login_count"].mean()
        licensed_seats = clinic_row["licensed_seats"]

        sync_score = score_sync(avg_sync)
        triage_score = score_triage(avg_triage_hours)
        seat_score = score_seat_utilization(avg_logins, licensed_seats)
        health = weighted_health_score(sync_score, triage_score, seat_score)

        records.append(
            {
                "Clinic": clinic_row["name"],
                "Plan": clinic_row["plan_tier"],
                "Sync Compliance %": round(avg_sync, 1),
                "Triage Hours": round(avg_triage_hours, 1),
                "Seat Utilization %": round(seat_score, 1),
                "Sync Score": round(sync_score, 1),
                "Triage Score": round(triage_score, 1),
                "Health Score": health,
                "Trend": trend_label(trend_delta),
                "Status": categorize(health),
            }
        )

    scorecard = pd.DataFrame.from_records(records)
    return scorecard.sort_values("Health Score", ascending=True).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Streamlit presentation layer
# ---------------------------------------------------------------------------

# Status colors: fixed, never reused for anything else on the page, so a
# status color always means the same thing wherever it appears.
STATUS_HEX = {
    "Stable": "#0ca30c",
    "At-Risk": "#fab219",
    "Critical": "#d03b3b",
}

# Low-opacity tints of the same hues, for cell/badge backgrounds — a wash,
# not a saturated block, so text stays the loud element.
STATUS_TINT = {
    "Stable": "rgba(12, 163, 12, 0.14)",
    "At-Risk": "rgba(250, 178, 25, 0.22)",
    "Critical": "rgba(208, 59, 59, 0.14)",
}

# Global styling: one small design system (tokens + a KPI card + table
# polish) so the whole page reads as one surface instead of a stack of
# mismatched Streamlit defaults and ad hoc inline styles.
APP_CSS = """
<style>
:root {
    --prm-surface: #ffffff;
    --prm-border: rgba(11, 11, 11, 0.10);
    --prm-text-primary: #0b0b0b;
    --prm-text-secondary: #52514e;
    --prm-accent-neutral: #c3c2b7;
}
@media (prefers-color-scheme: dark) {
    :root {
        --prm-surface: #1a1a19;
        --prm-border: rgba(255, 255, 255, 0.14);
        --prm-text-primary: #ffffff;
        --prm-text-secondary: #c3c2b7;
        --prm-accent-neutral: #383835;
    }
}

html, body, [class*="css"] {
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
}

.prm-kpi {
    background: var(--prm-surface);
    border: 1px solid var(--prm-border);
    border-left: 4px solid var(--kpi-accent, var(--prm-accent-neutral));
    border-radius: 10px;
    padding: 14px 16px;
}
.prm-kpi__label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--prm-text-secondary);
    margin-bottom: 6px;
}
.prm-kpi__dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--kpi-accent, var(--prm-accent-neutral));
    flex: 0 0 auto;
}
.prm-kpi__value {
    font-size: 1.85rem;
    font-weight: 700;
    color: var(--prm-text-primary);
    line-height: 1.15;
}

[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
</style>
"""


def _kpi_card(label: str, value: str, accent: str | None = None) -> str:
    """HTML for one KPI tile. `accent` colors the left border + identity dot;
    left unset, the tile reads as neutral so color stays reserved for the
    two counts that actually need to grab attention (Critical, At-Risk)."""
    style = f"--kpi-accent: {accent};" if accent else ""
    return (
        f'<div class="prm-kpi" style="{style}">'
        f'<div class="prm-kpi__label"><span class="prm-kpi__dot"></span>{label}</div>'
        f'<div class="prm-kpi__value">{value}</div>'
        f"</div>"
    )


def _style_status_column(column: pd.Series) -> list[str]:
    """Return per-cell CSS for the Status column (helper for Styler.apply):
    a tinted background with the status hue carried in the text, the same
    soft-badge pattern issue trackers use rather than a solid color block."""
    return [
        f"background-color: {STATUS_TINT.get(v, '')}; "
        f"color: {STATUS_HEX.get(v, '')}; font-weight: 600;"
        for v in column
    ]


def _format_status_badge(value: str) -> str:
    """Prefix a status value with a colored bullet for display — an icon
    alongside the label, so status is never conveyed by color alone."""
    return f"● {value}"


def render_sidebar() -> list[str]:
    """Render sidebar controls and return the selected status filter.

    The filter comes first since it's the control used every session;
    the scoring methodology below it is static reference material.
    """
    import streamlit as st

    all_statuses = ["Stable", "At-Risk", "Critical"]
    status_filter = st.sidebar.multiselect(
        "Filter by status", options=all_statuses, default=all_statuses
    )

    st.sidebar.divider()
    st.sidebar.header("Scoring Model")
    st.sidebar.markdown(
        f"""
        **Composite weights**
        - B2C Sync Compliance - **{WEIGHT_SYNC:.0%}**
        - B2B Alert Triage - **{WEIGHT_TRIAGE:.0%}**
        - Seat Utilization - **{WEIGHT_SEAT:.0%}**

        **Categories**
        - 🟢 Stable &nbsp;&ge; {STABLE_THRESHOLD:.0f}
        - 🟠 At-Risk &nbsp;{AT_RISK_THRESHOLD:.0f}-{STABLE_THRESHOLD:.0f}
        - 🔴 Critical &nbsp;&lt; {AT_RISK_THRESHOLD:.0f}
        """
    )
    return status_filter


def render_kpis(scorecard: pd.DataFrame) -> None:
    """Render the top KPI row as one consistent card component, most urgent
    counts first (left to right). Only Critical/At-Risk carry a color accent
    — color stays reserved for what's actually urgent instead of decorating
    every tile."""
    import streamlit as st

    total = len(scorecard)
    avg_health = scorecard["Health Score"].mean() if total else 0.0
    avg_sync = scorecard["Sync Compliance %"].mean() if total else 0.0
    at_risk = int((scorecard["Status"] == "At-Risk").sum())
    critical = int((scorecard["Status"] == "Critical").sum())

    tiles = [
        ("Critical", str(critical), STATUS_HEX["Critical"] if critical else None),
        ("At-Risk", str(at_risk), STATUS_HEX["At-Risk"] if at_risk else None),
        ("Accounts", str(total), None),
        ("Avg health score", f"{avg_health:.1f}", None),
        ("Avg sync compliance", f"{avg_sync:.1f}%", None),
    ]
    for col, (label, value, accent) in zip(st.columns(5), tiles):
        col.markdown(_kpi_card(label, value, accent), unsafe_allow_html=True)


def render_attention(scorecard: pd.DataFrame, status_filter: list[str]) -> None:
    """Render the prioritized action list: filtered like the rest of the
    page, worst status first, and within a status, higher-value plans
    first so a slipping Enterprise account outranks a Starter account at
    the same health score.
    """
    import streamlit as st

    attention = scorecard[
        (scorecard["Status"] != "Stable") & (scorecard["Status"].isin(status_filter))
    ].copy()

    st.subheader("Accounts Needing Attention")
    if attention.empty:
        st.success("No accounts currently need attention.")
        return

    attention["_status_rank"] = attention["Status"].map(STATUS_PRIORITY)
    attention["_plan_rank"] = attention["Plan"].map(PLAN_PRIORITY).fillna(99)
    attention = attention.sort_values(["_status_rank", "_plan_rank", "Health Score"])

    display_cols = ["Clinic", "Plan", "Status", "Health Score", "Trend"]
    styled = (
        attention[display_cols]
        .style.apply(_style_status_column, subset=["Status"])
        .format({"Health Score": "{:.1f}", "Status": _format_status_badge})
    )
    with st.container(border=True):
        st.dataframe(styled, use_container_width=True, hide_index=True)


def render_health_chart(filtered: pd.DataFrame) -> None:
    """Bar chart colored by Status so it reads consistently with the table,
    ordered worst-to-best to match the scorecard's default sort. Thin,
    rounded bars with hairline gridlines and direct value labels — mark
    specs kept restrained so the data is the loud element, not the chrome."""
    import altair as alt
    import streamlit as st

    order = filtered["Clinic"].tolist()
    base = alt.Chart(filtered)

    bars = base.mark_bar(size=22, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X(
            "Clinic:N", sort=order, title=None,
            axis=alt.Axis(labelColor="#898781", labelFontSize=11, domainColor="#c3c2b7"),
        ),
        y=alt.Y(
            "Health Score:Q", title="Health score",
            axis=alt.Axis(gridColor="#e1e0d9", domainOpacity=0, labelColor="#898781", tickCount=5),
        ),
        color=alt.Color(
            "Status:N",
            scale=alt.Scale(
                domain=["Critical", "At-Risk", "Stable"],
                range=[STATUS_HEX["Critical"], STATUS_HEX["At-Risk"], STATUS_HEX["Stable"]],
            ),
            legend=alt.Legend(title=None, orient="top", labelFontSize=11),
        ),
        tooltip=["Clinic", "Plan", "Health Score", "Status", "Trend"],
    )
    labels = base.mark_text(dy=-8, fontSize=11, color="#52514e").encode(
        x=alt.X("Clinic:N", sort=order),
        y="Health Score:Q",
        text=alt.Text("Health Score:Q", format=".0f"),
    )

    chart = (
        (bars + labels)
        .properties(height=320)
        .configure_view(strokeWidth=0)
        .configure(background="transparent", font="system-ui")
    )
    with st.container(border=True):
        st.altair_chart(chart, use_container_width=True)


def render_dashboard(scorecard: pd.DataFrame, status_filter: list[str]) -> None:
    """Render KPIs, the prioritized attention list, then the full scorecard
    table and chart as supporting detail."""
    import streamlit as st

    st.title("Patient Remote Monitoring - Customer Health")
    st.caption(
        "B2B2C account health across patient sync compliance, alert-triage "
        f"responsiveness, and seat utilization - trailing {TELEMETRY_DAYS} days."
    )

    render_kpis(scorecard)
    st.divider()

    render_attention(scorecard, status_filter)
    st.divider()

    filtered = scorecard[scorecard["Status"].isin(status_filter)]

    left, right = st.columns((3, 2))
    with left:
        st.subheader("Full Account Scorecard")
        if filtered.empty:
            st.info("No accounts match the selected status filter.")
        else:
            styled = (
                filtered.style
                .apply(_style_status_column, subset=["Status"])
                .format(
                    {
                        "Sync Compliance %": "{:.1f}",
                        "Triage Hours": "{:.1f}",
                        "Seat Utilization %": "{:.1f}",
                        "Sync Score": "{:.1f}",
                        "Triage Score": "{:.1f}",
                        "Health Score": "{:.1f}",
                        "Status": _format_status_badge,
                    }
                )
            )
            with st.container(border=True):
                st.dataframe(styled, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Health Score by Account")
        if not filtered.empty:
            render_health_chart(filtered)


def main() -> None:
    """Application entry point (executed by `streamlit run app.py`)."""
    import streamlit as st

    st.set_page_config(
        page_title="PRM Customer Health",
        page_icon="🩺",
        layout="wide",
    )
    st.markdown(APP_CSS, unsafe_allow_html=True)  # Shared design tokens + KPI card styles.
    ensure_database(DB_PATH)                 # Auto-initialize + seed on startup.
    scorecard = build_scorecard(DB_PATH)     # Aggregate telemetry -> scores.
    status_filter = render_sidebar()         # Sidebar controls.
    render_dashboard(scorecard, status_filter)


# `streamlit run app.py` sets __name__ == "__main__", so the dashboard renders.
# `import app` (e.g. from the test suite) does NOT trigger any Streamlit calls.
if __name__ == "__main__":
    main()


# ===========================================================================
# UNIT TESTS (pytest) - copy the block below into `test_app.py` beside app.py
# ---------------------------------------------------------------------------
# Run with:
#     pip install pytest streamlit pandas
#     pytest -q
# ---------------------------------------------------------------------------
#
# """Unit tests for the PRM health-scoring engine (calculation boundaries)."""
#
# import pytest
#
# from app import (
#     AT_RISK_THRESHOLD,
#     STABLE_THRESHOLD,
#     categorize,
#     score_seat_utilization,
#     score_sync,
#     score_triage,
#     weighted_health_score,
# )
#
#
# def test_sync_score_upper_clamp():
#     # Compliance above 100% is clamped down to the 100 ceiling.
#     assert score_sync(120.0) == 100.0
#
#
# def test_sync_score_lower_clamp():
#     # Negative compliance is clamped up to the 0 floor.
#     assert score_sync(-10.0) == 0.0
#
#
# def test_triage_score_meets_sla():
#     # Triage at (or faster than) the SLA target earns a perfect score.
#     assert score_triage(2.0) == 100.0
#     assert score_triage(0.5) == 100.0
#
#
# def test_triage_score_breaches_max():
#     # Triage at (or beyond) the max threshold earns zero.
#     assert score_triage(24.0) == 0.0
#     assert score_triage(40.0) == 0.0
#
#
# def test_triage_score_linear_midpoint():
#     # 13h is the midpoint between the 2h target and 24h max -> 50.
#     assert score_triage(13.0) == pytest.approx(50.0)
#
#
# def test_seat_utilization_full_and_overflow():
#     # Logins equal to seats -> 100; logins above seats stay clamped at 100.
#     assert score_seat_utilization(10, 10) == 100.0
#     assert score_seat_utilization(15, 10) == 100.0
#
#
# def test_seat_utilization_handles_zero_seats():
#     # Zero licensed seats must not divide by zero; it scores 0.
#     assert score_seat_utilization(5, 0) == 0.0
#
#
# def test_weighted_health_score_matches_manual():
#     # 0.45*80 + 0.35*60 + 0.20*50 = 36 + 21 + 10 = 67.0
#     assert weighted_health_score(80.0, 60.0, 50.0) == pytest.approx(67.0)
#
#
# def test_categorize_stable_and_at_risk_boundaries():
#     # 80 is the inclusive Stable boundary; just below falls to At-Risk.
#     assert categorize(STABLE_THRESHOLD) == "Stable"
#     assert categorize(79.99) == "At-Risk"
#     assert categorize(AT_RISK_THRESHOLD) == "At-Risk"
#
#
# def test_categorize_critical_boundary():
#     # Anything below the At-Risk floor is Critical.
#     assert categorize(59.99) == "Critical"
#     assert categorize(0.0) == "Critical"
