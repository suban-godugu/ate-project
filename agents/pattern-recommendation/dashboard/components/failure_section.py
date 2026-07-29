"""Failure Aggregation section — ranked patterns, filters, severity chips."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def render_failure_section(failure: dict[str, Any] | None) -> None:
    """Render failure health chips + filterable ranked pattern grid."""
    st.markdown("---")
    st.markdown("### Failure Aggregation")
    st.caption("Output of the log → aggregate pipeline across ATE lots.")

    if not failure:
        st.warning("Failure summary is unavailable. Run the aggregation agent or refresh.")
        return

    summary = failure.get("summary") or {}
    patterns = failure.get("patterns") or []

    chip_cols = st.columns(4)
    with chip_cols[0]:
        st.metric("Failed logs", summary.get("failed_logs", 0))
    with chip_cols[1]:
        st.metric("Good logs", summary.get("good_logs", 0))
    with chip_cols[2]:
        st.metric(
            "Severity HIGH / MED / LOW",
            f"{summary.get('severity_high', 0)} / "
            f"{summary.get('severity_medium', 0)} / "
            f"{summary.get('severity_low', 0)}",
        )
    with chip_cols[3]:
        st.metric("Pattern occurrences", summary.get("total_pattern_occurrences", 0))

    if not patterns:
        st.info("No failing patterns in the current failure summary.")
        return

    df = pd.DataFrame(patterns)
    all_lots: list[str] = sorted(
        {
            str(lot)
            for lots in df.get("affected_lots", pd.Series(dtype=object))
            for lot in (lots if isinstance(lots, list) else [])
        }
    )
    severities = sorted({str(s).upper() for s in df.get("severity", pd.Series(dtype=object))})

    filter_cols = st.columns([2, 2, 2, 2, 1])
    with filter_cols[0]:
        search = st.text_input("Search pattern ID", value="", key="fail_search")
    with filter_cols[1]:
        severity_filter = st.multiselect(
            "Severity",
            options=severities,
            default=severities,
            key="fail_severity",
        )
    with filter_cols[2]:
        lot_filter = st.multiselect(
            "Affected lot",
            options=all_lots,
            default=[],
            key="fail_lots",
            help="Empty = all lots",
        )
    with filter_cols[3]:
        min_failed = st.number_input(
            "Min failed logs",
            min_value=0,
            value=0,
            step=1,
            key="fail_min_logs",
        )
    with filter_cols[4]:
        show_all = st.checkbox("Show all", value=False, key="fail_show_all")

    filtered = df.copy()
    if search:
        filtered = filtered[
            filtered["pattern_id"].astype(str).str.contains(search, case=False, na=False)
        ]
    if severity_filter:
        filtered = filtered[filtered["severity"].astype(str).str.upper().isin(severity_filter)]
    if lot_filter:
        filtered = filtered[
            filtered["affected_lots"].apply(
                lambda lots: bool(set(lots or []) & set(lot_filter))
            )
        ]
    if min_failed > 0:
        filtered = filtered[filtered["failed_logs"].fillna(0) >= min_failed]

    filtered = filtered.sort_values("rank", ascending=True)
    default_n = 50
    visible = filtered if show_all else filtered.head(default_n)

    display = visible[
        [
            c
            for c in [
                "rank",
                "pattern_id",
                "failed_logs",
                "coverage_percent",
                "severity",
                "affected_lots",
                "failing_log_count",
            ]
            if c in visible.columns
        ]
    ].rename(
        columns={
            "rank": "Rank",
            "pattern_id": "Pattern ID",
            "failed_logs": "Failed Logs",
            "coverage_percent": "Coverage %",
            "severity": "Severity",
            "affected_lots": "Affected Lots",
            "failing_log_count": "Failing Log Count",
        }
    )
    if "Affected Lots" in display.columns:
        display["Affected Lots"] = display["Affected Lots"].apply(
            lambda lots: ", ".join(lots) if isinstance(lots, list) else lots
        )

    st.dataframe(display, use_container_width=True, hide_index=True)
    st.caption(
        f"Showing {len(visible)} of {len(filtered)} matching patterns"
        + (" (top 50)" if not show_all and len(filtered) > default_n else "")
    )

    csv_bytes = display.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Export visible failure rows (CSV)",
        data=csv_bytes,
        file_name="failure_aggregation.csv",
        mime="text/csv",
        key="fail_export",
    )

    with st.expander("Inspect failing log paths for a pattern"):
        options = visible["pattern_id"].astype(str).tolist() if "pattern_id" in visible.columns else []
        if not options:
            st.write("No patterns in the current view.")
            return
        selected = st.selectbox("Pattern", options=options, key="fail_inspect")
        match = visible[visible["pattern_id"].astype(str) == selected]
        if match.empty:
            return
        logs = match.iloc[0].get("failing_logs") or []
        if isinstance(logs, list) and logs:
            st.code("\n".join(str(path) for path in logs))
        else:
            st.write("No failing log paths recorded for this pattern.")
