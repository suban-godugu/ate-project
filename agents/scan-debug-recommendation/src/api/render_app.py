"""
Lean Scan Debug API for Render when full `src/data` + `src/models` are not in the repo.

Serves health + dashboard endpoints the Next.js UI expects, using built-in demo payloads.
Start: uvicorn src.api.render_app:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Scan Debug Recommendation Agent", version="1.1-render")

_origins = [
    o.strip()
    for o in (
        os.environ.get("CORS_ORIGINS")
        or "https://ate-project-ochre.vercel.app,http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _spark(seed: int) -> list[int]:
    return [max(2, round(seed + (i % 5) * 2 + (i % 3))) for i in range(12)]


def _dashboard() -> Dict[str, Any]:
    kpis = [
        {
            "id": "broken_chains",
            "section": "scan_chain_debug",
            "title": "Broken Chains Detected",
            "value": "7",
            "target": "0",
            "severity": "critical",
            "status": "at_risk",
            "trendPct": 12,
            "sparkline": _spark(7),
        },
        {
            "id": "debug_recommendations",
            "section": "scan_chain_debug",
            "title": "Debug Recommendations",
            "value": "18",
            "target": "—",
            "severity": "high",
            "status": "watch",
            "trendPct": 5,
            "sparkline": _spark(18),
        },
        {
            "id": "avg_ai_confidence",
            "section": "scan_chain_debug",
            "title": "Avg AI Confidence",
            "value": "88%",
            "target": "85%",
            "severity": "medium",
            "status": "healthy",
            "trendPct": 2,
            "sparkline": _spark(88),
        },
        {
            "id": "constraint_violations",
            "section": "atpg_constraint_review",
            "title": "Constraint Violations",
            "value": "23",
            "target": "0",
            "severity": "high",
            "status": "at_risk",
            "trendPct": 8,
            "sparkline": _spark(23),
        },
        {
            "id": "pending_review",
            "section": "atpg_constraint_review",
            "title": "Pending Review",
            "value": "14",
            "target": "<5",
            "severity": "medium",
            "status": "watch",
            "trendPct": -3,
            "sparkline": _spark(14),
        },
        {
            "id": "coverage_impact",
            "section": "atpg_constraint_review",
            "title": "Coverage Impact",
            "value": "+1.8%",
            "target": "+2.0%",
            "severity": "medium",
            "status": "watch",
            "trendPct": 4,
            "sparkline": _spark(18),
        },
        {
            "id": "timing_violations",
            "section": "timing_debug",
            "title": "Timing Violations",
            "value": "11",
            "target": "0",
            "severity": "high",
            "status": "at_risk",
            "trendPct": 6,
            "sparkline": _spark(11),
        },
        {
            "id": "timing_debug_recs",
            "section": "timing_debug",
            "title": "Timing Debug Recs",
            "value": "9",
            "target": "—",
            "severity": "high",
            "status": "watch",
            "trendPct": 1,
            "sparkline": _spark(9),
        },
        {
            "id": "worst_slack",
            "section": "timing_debug",
            "title": "Worst Slack",
            "value": "-42 ps",
            "target": ">0 ps",
            "severity": "critical",
            "status": "at_risk",
            "trendPct": -7,
            "sparkline": _spark(42),
        },
        {
            "id": "power_violations",
            "section": "power_related_debug",
            "title": "Power Violations",
            "value": "6",
            "target": "0",
            "severity": "high",
            "status": "at_risk",
            "trendPct": 3,
            "sparkline": _spark(6),
        },
        {
            "id": "power_debug_recs",
            "section": "power_related_debug",
            "title": "Power Debug Recs",
            "value": "9",
            "target": "—",
            "severity": "medium",
            "status": "watch",
            "trendPct": 2,
            "sparkline": _spark(9),
        },
        {
            "id": "peak_switching",
            "section": "power_related_debug",
            "title": "Peak Switching",
            "value": "1.34×",
            "target": "<1.10×",
            "severity": "high",
            "status": "at_risk",
            "trendPct": 9,
            "sparkline": _spark(34),
        },
        {
            "id": "defect_suspects",
            "section": "physical_defect_investigation",
            "title": "Defect Suspects",
            "value": "17",
            "target": "—",
            "severity": "high",
            "status": "watch",
            "trendPct": 4,
            "sparkline": _spark(17),
        },
        {
            "id": "investigation_recs",
            "section": "physical_defect_investigation",
            "title": "Investigation Recs",
            "value": "31",
            "target": "—",
            "severity": "medium",
            "status": "watch",
            "trendPct": 5,
            "sparkline": _spark(31),
        },
        {
            "id": "defect_localization",
            "section": "physical_defect_investigation",
            "title": "Defect Localization",
            "value": "12",
            "target": "—",
            "severity": "medium",
            "status": "healthy",
            "trendPct": 0,
            "sparkline": _spark(12),
        },
    ]

    return {
        "kpis": kpis,
        "rootCauseDistribution": [
            {"name": "Chain Break", value: 28, "fill": "#EF4444"},
            {"name": "Timing", value: 22, "fill": "#F59E0B"},
            {"name": "Power/IR", value: 18, "fill": "#7C3AED"},
            {"name": "ATPG Constraint", value: 16, "fill": "#38BDF8"},
            {"name": "Physical Defect", value: 16, "fill": "#34D399"},
        ],
        "recommendationPriority": [
            {"name": "Critical", "value": 10, "fill": "#EF4444"},
            {"name": "High", "value": 8, "fill": "#F59E0B"},
            {"name": "Medium", "value": 15, "fill": "#7C3AED"},
            {"name": "Low", "value": 9, "fill": "#64748B"},
        ],
        "recommendationTrend": [
            {"date": f"D-{29 - i}", "value": max(1, 8 + (i % 7))} for i in range(30)
        ],
        "aiConfidence": 0.87,
        "approvalTrend": [
            {
                "date": f"W{i + 1}",
                "value": 0,
                "approved": 6 + (i % 4),
                "rejected": 1 + (i % 3),
                "pending": 3 + (i % 2),
            }
            for i in range(12)
        ],
        "recommendations": [
            {
                "id": "DBG-REC-001",
                "category": "SCAN_CHAIN_DEBUG",
                "categoryLabel": "Broken Chain",
                "recommendation": "Inspect Scan Chain",
                "scanChain": "SC-004821",
                "rootCause": "Chain Breakpoint",
                "actionLabel": "Inspect Scan Chain 12",
                "priority": "P0",
                "priorityLabel": "Critical",
                "affectedScanChain": "LOT_1_Center",
                "expectedImpact": "Restore chain integrity",
                "expectedYieldGainPct": 1.8,
                "estimatedRuntimeReductionPct": 6.2,
                "confidence": 0.94,
            },
            {
                "id": "DBG-REC-002",
                "category": "TIMING_DEBUG",
                "categoryLabel": "Timing",
                "recommendation": "Review Capture Clock Timing",
                "scanChain": "SC-003158",
                "rootCause": "Hold Violation",
                "actionLabel": "Review Capture Clock Timing",
                "priority": "P1",
                "priorityLabel": "High",
                "affectedScanChain": "LOT_6_Near-Full",
                "expectedImpact": "42 ps slack recovery",
                "expectedYieldGainPct": 1.1,
                "estimatedRuntimeReductionPct": 3.4,
                "confidence": 0.88,
            },
        ],
        "executiveSummary": [
            {
                "id": "broken_chains",
                "label": "Broken Chains",
                "value": "7",
                "detail": "Chains requiring Inspect Scan Chain",
                "tone": "danger",
            },
            {
                "id": "timing_debug_recs",
                "label": "Timing Issues",
                "value": "11",
                "detail": "Review Capture Clock Timing recommendations",
                "tone": "warning",
            },
            {
                "id": "avg_ai_confidence",
                "label": "AI Confidence",
                "value": "88%",
                "detail": "Render demo policy confidence",
                "tone": "info",
            },
        ],
        "workflow": [
            {"id": "logs", "label": "Failure Logs", "status": "done"},
            {"id": "diag", "label": "Diagnosis Engine", "status": "done"},
            {"id": "rca", "label": "Root Cause Analysis", "status": "done"},
            {
                "id": "agent",
                "label": "Scan Debug Recommendation Agent",
                "status": "active",
            },
            {"id": "impl", "label": "Implementation", "status": "upcoming"},
            {"id": "val", "label": "Validation", "status": "upcoming"},
        ],
        "mode": "render-demo",
    }


def _workspace(kpi_id: str) -> Dict[str, Any]:
    dash = _dashboard()
    kpi = next((k for k in dash["kpis"] if k["id"] == kpi_id), None)
    title = (kpi or {}).get("title") or kpi_id
    return {
        "kpiId": kpi_id,
        "title": title,
        "decision": {
            "executiveSummary": f"{title} demo workspace (Render stub — full ML packages not in repo).",
            "rootCause": "Demo root cause pending full src/data restore.",
            "confidence": 0.84,
            "businessImpact": "Demo impact only.",
            "risk": "Low — demo payload",
            "recommendation": "Restore src/data + src/models for live engines.",
            "whatFailed": f"{title} demo breach.",
            "whyAiRecommended": "Stub ranking for embed smoke test.",
            "whatImproves": "Yield / debug cycle time (demo).",
            "shouldApprove": "Review — demo data.",
        },
        "summaryCards": [
            {"label": "Current", "value": str((kpi or {}).get("value", "—"))},
            {"label": "Target", "value": str((kpi or {}).get("target", "—"))},
            {"label": "Mode", "value": "render-demo"},
        ],
        "visualizationType": "topology",
        "vizSeries": [
            {"label": "SC_0142", "value": 94},
            {"label": "SC_0087", "value": 81},
            {"label": "SC_0211", "value": 76},
        ],
        "breakdown": [
            {"dimension": "Tester", "value": "ATE-07", "share": 28},
            {"dimension": "Lot", "value": "LOT_1", "share": 22},
        ],
        "impact": [
            {"label": "Yield opp.", "value": "+1.6%"},
            {"label": "Runtime", "value": "-4.6h / lot"},
        ],
        "diagnosisResults": [],
        "copilotStarters": [
            "Summarize this KPI for the DFT owner",
            "List top failing scan chains",
        ],
    }


@app.get("/health")
@app.get("/healthz")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "scan-debug-recommendation-agent",
        "env": os.environ.get("APP_ENV", "production"),
        "mode": "render-demo",
    }


@app.get("/ready")
@app.get("/readyz")
def ready() -> Dict[str, Any]:
    return {"status": "ready", "mode": "render-demo"}


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "scan-debug-recommendation-agent",
        "docs": "/docs",
        "health": "/health",
        "mode": "render-demo",
    }


@app.get("/status")
def status() -> Dict[str, Any]:
    return {
        "device": "cpu",
        "replay_buffer_size": 0,
        "epsilon": 0.05,
        "steps_done": 0,
        "model_weights_exist": False,
        "auto_train_on_startup": "false",
        "needs_training": False,
        "training_in_progress": False,
        "dataset_cases": 0,
        "auto_trained": False,
        "mode": "render-demo",
    }


@app.get("/api/v1/recommendation/dashboard")
def dashboard() -> Dict[str, Any]:
    return _dashboard()


@app.get("/api/v1/kpi/{kpi_id}/workspace")
def kpi_workspace(kpi_id: str) -> Dict[str, Any]:
    return _workspace(kpi_id)


@app.post("/train")
def train(episodes: int = 10, force: bool = False) -> Dict[str, Any]:
    return {
        "status": "skipped",
        "episodes_trained": 0,
        "average_episode_reward": 0,
        "average_loss": 0,
        "final_epsilon": 0.05,
        "weights_saved": False,
        "skipped": True,
        "source": "render-demo",
        "message": "Full DQN training requires src/models — not available in this deploy.",
    }
