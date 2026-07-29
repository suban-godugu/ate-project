"""Recommendation workbench tabs backed by /recommendations/dashboard."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from dashboard.components.kpi_cards import (
    SECTION_COVERAGE,
    SECTION_GAP,
    SECTION_LOW_POWER,
    SECTION_ORDERING,
    SECTION_REDUNDANCY,
    SECTION_REMOVAL,
)

TAB_KEYS = [
    SECTION_REMOVAL,
    SECTION_ORDERING,
    SECTION_REDUNDANCY,
    SECTION_GAP,
    SECTION_LOW_POWER,
    SECTION_COVERAGE,
]

TAB_LABELS = {
    SECTION_REMOVAL: "Removal",
    SECTION_ORDERING: "Ordering",
    SECTION_REDUNDANCY: "Redundancy",
    SECTION_GAP: "Gap analysis",
    SECTION_LOW_POWER: "Low-power",
    SECTION_COVERAGE: "Coverage",
}

FEASIBILITY_NOTES = {
    SECTION_REMOVAL: "Feasibility: full — removal ranking for redundant near-duplicates.",
    SECTION_ORDERING: "Feasibility: full — early failure detection ordering.",
    SECTION_REDUNDANCY: "Feasibility: full — clustering-based redundancy.",
    SECTION_GAP: "Feasibility: gap_requests_only — ATPG requests only; no vectors generated.",
    SECTION_LOW_POWER: "Feasibility: toggle_activity_proxy — not measured power.",
    SECTION_COVERAGE: "Feasibility: toggle_fail_proxy — not ATPG fault coverage.",
}

TABLE_KEYS = {
    SECTION_REMOVAL: "removal_recommendations",
    SECTION_ORDERING: "ordered_patterns",
    SECTION_REDUNDANCY: "redundant_patterns",
    SECTION_GAP: "additional_pattern_requests",
    SECTION_LOW_POWER: "low_activity_pattern_set",
    SECTION_COVERAGE: "coverage_gap_recommendations",
}

PREFERRED_COLUMNS = {
    SECTION_REMOVAL: [
        "pattern_id",
        "removal_priority",
        "confidence",
        "unique_fail_contribution",
        "cluster_id",
        "representative_pattern",
        "reason_codes",
    ],
    SECTION_ORDERING: [
        "pattern_id",
        "execution_rank",
        "order_score",
        "fail_rate",
        "severity",
        "mean_toggle_coverage",
        "reason_codes",
    ],
    SECTION_REDUNDANCY: [
        "pattern_id",
        "cluster_id",
        "is_representative",
        "redundant_flag",
        "similarity_to_representative",
        "representative_pattern",
    ],
    SECTION_GAP: [
        "request_id",
        "target_chains",
        "target_lots",
        "suggested_fault_model",
        "rationale",
        "request_only",
    ],
    SECTION_LOW_POWER: [
        "pattern_id",
        "activity_score",
        "toggle_metric",
        "representative",
        "coverage_retained",
        "reason_codes",
    ],
    SECTION_COVERAGE: [
        "pattern_id",
        "recommendation_type",
        "priority",
        "affected_chains",
        "affected_lots",
        "reason_codes",
    ],
}


def render_recommendation_tabs(
    dashboard: dict[str, Any] | None,
    *,
    top_n: int = 100,
) -> None:
    """Render one tab per recommendation domain with export and feasibility notes."""
    st.markdown("---")
    st.markdown("### Recommendation Workbench")
    st.caption("Unified tables from GET /recommendations/dashboard.")

    if not dashboard:
        st.warning("Unified recommendations are unavailable. Start the API and refresh.")
        return

    tables = dashboard.get("tables") or {}
    feasibility = dashboard.get("feasibility") or {}
    active = st.session_state.get("active_tab", SECTION_REMOVAL)
    if active not in TAB_KEYS:
        active = SECTION_REMOVAL

    labels = [TAB_LABELS[key] for key in TAB_KEYS]
    if "rec_domain_radio" not in st.session_state:
        st.session_state["rec_domain_radio"] = TAB_LABELS[active]
    elif st.session_state["rec_domain_radio"] not in labels:
        st.session_state["rec_domain_radio"] = TAB_LABELS[active]

    selected_label = st.radio(
        "Domain",
        options=labels,
        horizontal=True,
        key="rec_domain_radio",
    )
    section = next(key for key, label in TAB_LABELS.items() if label == selected_label)
    st.session_state["active_tab"] = section
    st.session_state["active_section"] = section

    note = FEASIBILITY_NOTES.get(section, "")
    if feasibility:
        # Prefer live feasibility payload when present
        mapping = {
            SECTION_REMOVAL: feasibility.get("pattern_removal"),
            SECTION_ORDERING: feasibility.get("pattern_ordering"),
            SECTION_REDUNDANCY: feasibility.get("redundant_patterns"),
            SECTION_GAP: feasibility.get("additional_atpg"),
            SECTION_LOW_POWER: feasibility.get("low_power_sets"),
            SECTION_COVERAGE: feasibility.get("coverage_improvement"),
        }
        live = mapping.get(section)
        if live:
            note = f"Feasibility: `{live}`"
    st.info(note)

    rows = tables.get(TABLE_KEYS[section]) or []
    if not rows:
        st.empty()
        st.write("No rows for this domain yet.")
        return

    df = pd.DataFrame(rows)
    preferred = [c for c in PREFERRED_COLUMNS.get(section, []) if c in df.columns]
    other = [c for c in df.columns if c not in preferred]
    ordered = preferred + other
    display = df[ordered].copy()

    for col in display.columns:
        if display[col].map(lambda v: isinstance(v, list)).any():
            display[col] = display[col].apply(
                lambda v: ", ".join(str(x) for x in v) if isinstance(v, list) else v
            )

    show_all = st.checkbox("Show all rows", value=False, key=f"rec_show_all_{section}")
    visible = display if show_all else display.head(top_n)
    st.dataframe(visible, use_container_width=True, hide_index=True)
    st.caption(
        f"Showing {len(visible)} of {len(display)} rows"
        + (f" (top {top_n})" if not show_all and len(display) > top_n else "")
    )

    csv_bytes = visible.to_csv(index=False).encode("utf-8")
    st.download_button(
        f"Export {TAB_LABELS[section]} (CSV)",
        data=csv_bytes,
        file_name=f"{section}_recommendations.csv",
        mime="text/csv",
        key=f"rec_export_{section}",
    )
