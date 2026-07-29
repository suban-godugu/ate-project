"""
Pattern Recommendation Dashboard

Streamlit UI over the FastAPI backend:
  KPI cards → Failure Aggregation → Recommendation Workbench
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Allow `streamlit run dashboard/app.py` from project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dashboard.api_client import ApiError, BackendClient
from dashboard.components.failure_section import render_failure_section
from dashboard.components.kpi_cards import (
    SECTION_DATASETS,
    SECTION_FAILURE,
    SECTION_PATTERNS,
    render_kpi_rows,
)
from dashboard.components.rec_tabs import render_recommendation_tabs

PAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap');

html, body, [class*="css"] {
  font-family: "IBM Plex Sans", sans-serif;
}

.stApp {
  background:
    radial-gradient(1200px 500px at 10% -10%, #d7f0ea 0%, transparent 55%),
    radial-gradient(900px 400px at 100% 0%, #e8eef5 0%, transparent 50%),
    linear-gradient(180deg, #f4f7fa 0%, #eef2f6 100%);
}

.block-container {
  padding-top: 1.2rem;
  max-width: 1280px;
}

.brand-lockup {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  margin-bottom: 0.4rem;
}
.brand-name {
  font-size: 1.85rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #0f2f3a;
  margin: 0;
}
.brand-tag {
  color: #4a6570;
  font-size: 0.95rem;
  margin: 0;
}

.kpi-tile {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid #d5e0e6;
  border-radius: 10px;
  padding: 0.85rem 0.9rem 0.7rem;
  min-height: 96px;
  margin-bottom: 0.35rem;
}
.kpi-label {
  font-size: 0.78rem;
  color: #5a717c;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.kpi-value {
  font-family: "IBM Plex Mono", monospace;
  font-size: 1.25rem;
  font-weight: 500;
  color: #0c3d4a;
  margin-top: 0.25rem;
  line-height: 1.25;
  word-break: break-word;
}
.kpi-sub {
  font-size: 0.72rem;
  color: #7a9099;
  margin-top: 0.2rem;
}

div[data-testid="stMetricValue"] {
  font-family: "IBM Plex Mono", monospace;
}
</style>
"""


def _init_state() -> None:
    defaults = {
        "active_section": SECTION_FAILURE,
        "active_tab": "removal",
        "load_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_data(ttl=30, show_spinner=False)
def _load_bundle(base_url: str) -> dict:
    client = BackendClient(base_url=base_url)
    errors: list[str] = []

    health_ok = False
    try:
        health = client.get_health()
        health_ok = str(health.get("status", "")).lower() in {
            "healthy",
            "ok",
            "operational",
        }
    except ApiError as exc:
        errors.append(f"health: {exc.message}")
        raise

    datasets: dict = {}
    try:
        datasets = client.get_datasets_status()
    except ApiError as exc:
        errors.append(f"datasets: {exc.message}")

    failure: dict | None = None
    try:
        failure = client.get_failure_summary()
    except ApiError as exc:
        errors.append(f"failures: {exc.message}")

    pattern_stats: dict = {}
    try:
        pattern_stats = client.get_patterns_statistics()
    except ApiError as exc:
        errors.append(f"patterns: {exc.message}")

    dashboard: dict = {}
    try:
        dashboard = client.get_dashboard()
    except ApiError as exc:
        errors.append(f"dashboard: {exc.message}")

    summary = (dashboard or {}).get("summary") or {}
    if not summary:
        try:
            summary = client.get_unified_summary()
        except ApiError as exc:
            errors.append(f"summary: {exc.message}")

    return {
        "health_ok": health_ok,
        "datasets": datasets,
        "failure": failure,
        "pattern_stats": pattern_stats,
        "dashboard": dashboard,
        "summary": summary,
        "built_at": (dashboard or {}).get("built_at"),
        "errors": errors,
    }


def main() -> None:
    st.set_page_config(
        page_title="Pattern Recommendation",
        page_icon="◇",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(PAGE_CSS, unsafe_allow_html=True)
    _init_state()

    client = BackendClient()
    base_url = client.base_url

    header_l, header_r = st.columns([3, 1])
    with header_l:
        st.markdown(
            """
            <div class="brand-lockup">
              <p class="brand-name">Pattern Recommendation</p>
              <p class="brand-tag">Failure aggregation and pattern analytics console</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with header_r:
        st.caption(f"API · `{base_url}`")
        if st.button("Refresh All", type="primary", use_container_width=True):
            with st.spinner("Refreshing recommendations and failure summary…"):
                try:
                    client.refresh_failures()
                    client.refresh_recommendations()
                    _load_bundle.clear()
                    st.session_state["load_error"] = None
                    st.success("Refresh completed")
                except ApiError as exc:
                    st.session_state["load_error"] = exc.message
                    st.error(exc.message)
            st.rerun()

    try:
        data = _load_bundle(base_url)
    except ApiError as exc:
        st.error(f"Backend unavailable: {exc.message}")
        st.info(
            "Start the API with `python -m backend.app`, then reload this page. "
            "Optional: set `DASHBOARD_API_URL` if the API is not on 127.0.0.1:8000."
        )
        return

    if st.session_state.get("load_error"):
        st.warning(st.session_state["load_error"])

    for err in data.get("errors") or []:
        st.warning(err)

    render_kpi_rows(
        failure=data.get("failure"),
        pattern_stats=data.get("pattern_stats"),
        summary=data.get("summary"),
        datasets=data.get("datasets"),
        health_ok=bool(data.get("health_ok")),
        built_at=data.get("built_at"),
    )

    active = st.session_state.get("active_section", SECTION_FAILURE)

    # Failure aggregation (always below KPIs; highlighted when KPI deep-links here)
    if active in {SECTION_FAILURE, SECTION_PATTERNS, SECTION_DATASETS}:
        render_failure_section(data.get("failure"))
        if active == SECTION_DATASETS:
            st.markdown("#### Dataset status")
            st.json(data.get("datasets") or {})
        if active == SECTION_PATTERNS:
            st.markdown("#### Pattern statistics")
            st.json(data.get("pattern_stats") or {})
    else:
        render_failure_section(data.get("failure"))

    render_recommendation_tabs(data.get("dashboard"), top_n=100)


if __name__ == "__main__":
    main()
