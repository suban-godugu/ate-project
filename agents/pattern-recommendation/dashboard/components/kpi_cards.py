"""KPI card strip for the Pattern Recommendation dashboard."""

from __future__ import annotations

from typing import Any

import streamlit as st

SECTION_FAILURE = "failure"
SECTION_PATTERNS = "patterns"
SECTION_REMOVAL = "removal"
SECTION_ORDERING = "ordering"
SECTION_REDUNDANCY = "redundancy"
SECTION_GAP = "gap"
SECTION_LOW_POWER = "low_power"
SECTION_COVERAGE = "coverage"
SECTION_DATASETS = "datasets"


def _metric_tile(
    label: str,
    value: str,
    *,
    sublabel: str = "",
    section_key: str | None = None,
    key: str,
) -> None:
    """Render one flat KPI tile; optional click jumps to a detail section."""
    st.markdown(
        f"""
        <div class="kpi-tile">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-sub">{sublabel}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if section_key:
        if st.button("View", key=key, use_container_width=True):
            st.session_state["active_section"] = section_key
            st.session_state["active_tab"] = section_key
            label_map = {
                "removal": "Removal",
                "ordering": "Ordering",
                "redundancy": "Redundancy",
                "gap": "Gap analysis",
                "low_power": "Low-power",
                "coverage": "Coverage",
            }
            if section_key in label_map:
                st.session_state["rec_domain_radio"] = label_map[section_key]
            st.rerun()


def render_kpi_rows(
    *,
    failure: dict[str, Any] | None,
    pattern_stats: dict[str, Any] | None,
    summary: dict[str, Any] | None,
    datasets: dict[str, Any] | None,
    health_ok: bool,
    built_at: str | None,
) -> None:
    """Render KPI rows A–D matching the dashboard plan."""
    st.markdown("### Overview")

    # Row A — Failure health
    st.caption("Failure health")
    fail_summary = (failure or {}).get("summary") or {}
    cols_a = st.columns(5)
    with cols_a[0]:
        _metric_tile(
            "Total logs",
            str(fail_summary.get("total_logs", "—")),
            section_key=SECTION_FAILURE,
            key="kpi_total_logs",
        )
    with cols_a[1]:
        failed = fail_summary.get("failed_logs", "—")
        good = fail_summary.get("good_logs", "—")
        _metric_tile(
            "Failed / Good",
            f"{failed} / {good}",
            section_key=SECTION_FAILURE,
            key="kpi_failed_good",
        )
    with cols_a[2]:
        _metric_tile(
            "Unique failing patterns",
            str(fail_summary.get("unique_patterns", "—")),
            section_key=SECTION_FAILURE,
            key="kpi_unique_patterns",
        )
    with cols_a[3]:
        _metric_tile(
            "Lots covered",
            str(fail_summary.get("total_lots", "—")),
            section_key=SECTION_FAILURE,
            key="kpi_lots",
        )
    with cols_a[4]:
        high = fail_summary.get("severity_high", 0)
        med = fail_summary.get("severity_medium", 0)
        low = fail_summary.get("severity_low", 0)
        _metric_tile(
            "Severity mix",
            f"H {high} · M {med} · L {low}",
            sublabel="HIGH / MEDIUM / LOW",
            section_key=SECTION_FAILURE,
            key="kpi_severity",
        )

    # Row B — Pattern analytics
    st.caption("Pattern analytics")
    summary = summary or {}
    pattern_stats = pattern_stats or {}
    cols_b = st.columns(4)
    with cols_b[0]:
        _metric_tile(
            "Patterns analyzed",
            str(summary.get("patterns_analyzed", pattern_stats.get("patterns", "—"))),
            section_key=SECTION_PATTERNS,
            key="kpi_patterns",
        )
    with cols_b[1]:
        _metric_tile(
            "Clusters",
            str(summary.get("clusters", "—")),
            section_key=SECTION_REDUNDANCY,
            key="kpi_clusters",
        )
    with cols_b[2]:
        avg_fail = pattern_stats.get("average_fail_rate")
        value = f"{avg_fail * 100:.2f}%" if isinstance(avg_fail, (int, float)) else "—"
        _metric_tile(
            "Avg fail rate",
            value,
            section_key=SECTION_PATTERNS,
            key="kpi_avg_fail",
        )
    with cols_b[3]:
        avg_toggle = pattern_stats.get("average_toggle_density")
        value = f"{avg_toggle:.4f}" if isinstance(avg_toggle, (int, float)) else "—"
        _metric_tile(
            "Avg toggle density",
            value,
            section_key=SECTION_PATTERNS,
            key="kpi_avg_toggle",
        )

    # Row C — Recommendation domains
    st.caption("Recommendation domains")
    cols_c = st.columns(5)
    with cols_c[0]:
        _metric_tile(
            "Removal candidates",
            str(summary.get("removal_candidates", "—")),
            sublabel="full",
            section_key=SECTION_REMOVAL,
            key="kpi_removal",
        )
    with cols_c[1]:
        _metric_tile(
            "Ordering candidates",
            str(summary.get("ordering_candidates", "—")),
            sublabel="full",
            section_key=SECTION_ORDERING,
            key="kpi_ordering",
        )
    with cols_c[2]:
        _metric_tile(
            "ATPG gap requests",
            str(summary.get("gap_requests", "—")),
            sublabel="gap_requests_only",
            section_key=SECTION_GAP,
            key="kpi_gap",
        )
    with cols_c[3]:
        _metric_tile(
            "Low-power set",
            str(summary.get("low_power_patterns", "—")),
            sublabel="toggle_activity_proxy",
            section_key=SECTION_LOW_POWER,
            key="kpi_low_power",
        )
    with cols_c[4]:
        _metric_tile(
            "Coverage recs",
            str(summary.get("coverage_recommendations", "—")),
            sublabel="toggle_fail_proxy",
            section_key=SECTION_COVERAGE,
            key="kpi_coverage",
        )

    # Row D — Ops / data readiness
    st.caption("Data readiness")
    datasets = datasets or {}
    cols_d = st.columns(3)
    with cols_d[0]:
        available = datasets.get("available", "—")
        missing = datasets.get("missing", "—")
        invalid = datasets.get("invalid", "—")
        _metric_tile(
            "Datasets",
            f"{available} / {missing} / {invalid}",
            sublabel="available · missing · invalid",
            section_key=SECTION_DATASETS,
            key="kpi_datasets",
        )
    with cols_d[1]:
        _metric_tile(
            "API status",
            "healthy" if health_ok else "down",
            key="kpi_health",
        )
    with cols_d[2]:
        display_built = built_at or "—"
        if built_at and "T" in built_at:
            display_built = built_at.replace("T", " ").split(".")[0] + " UTC"
        _metric_tile(
            "Last built",
            display_built,
            key="kpi_built_at",
        )
