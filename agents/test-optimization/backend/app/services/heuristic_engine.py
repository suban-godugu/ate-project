"""Deterministic heuristic engine — never invents missing metrics."""

from __future__ import annotations

from typing import Optional

from ..domain.models import OptimizationContext
from ..domain.schemas import (
    AdaptiveTestingBlock,
    MultiSiteBlock,
    OptimizationRecommendation,
    RecommendationItem,
    RiskBasedTestingBlock,
    TestStopBlock,
)


def detect_data_gaps(ctx: OptimizationContext) -> list[str]:
    gaps: list[str] = []
    mapping = {
        "pattern_recommendation": ctx.pattern_recommendation,
        "scan_debug_recommendation": ctx.scan_debug_recommendation,
        "yield_data": ctx.yield_data,
        "ate_logs": ctx.ate_logs,
        "coverage_report": ctx.coverage_report,
        "production_history": ctx.production_history,
        "wafer_analytics": ctx.wafer_analytics,
        "cost_metrics": ctx.cost_metrics,
        "historical_lots": ctx.historical_lots or None,
    }
    for name, value in mapping.items():
        if value is None or value == []:
            gaps.append(name)
    return gaps


def effective_coverage(ctx: OptimizationContext) -> Optional[float]:
    cov = ctx.coverage_report
    if cov is None:
        if ctx.pattern_recommendation and ctx.pattern_recommendation.coverage_after_optimization is not None:
            return ctx.pattern_recommendation.coverage_after_optimization
        return None
    if cov.coverage_pct is not None:
        return cov.coverage_pct
    parts = [v for v in (cov.stuck_at, cov.transition, cov.path_delay, cov.cell_aware) if v is not None]
    if parts:
        return min(parts)
    if ctx.pattern_recommendation and ctx.pattern_recommendation.coverage_after_optimization is not None:
        return ctx.pattern_recommendation.coverage_after_optimization
    return None


def run_heuristic(ctx: OptimizationContext) -> OptimizationRecommendation:
    gaps = detect_data_gaps(ctx)
    assumptions = list(ctx.assumptions)
    for g in gaps:
        assumptions.append(f"Missing input '{g}' — using only available signals.")

    yd = ctx.yield_data
    current_yield = yd.current_yield if yd else None
    hist_yield = yd.historical_yield if yd else None
    loss = yd.yield_loss if yd and yd.yield_loss is not None else (
        (hist_yield - current_yield) if hist_yield is not None and current_yield is not None else None
    )
    cov = effective_coverage(ctx)
    stop_threshold = ctx.policy.coverage_stop_threshold_pct
    ate = ctx.ate_logs
    pattern = ctx.pattern_recommendation
    debug = ctx.scan_debug_recommendation
    prod = ctx.production_history
    cost = ctx.cost_metrics
    wafer = ctx.wafer_analytics

    risk_score = 0.0
    reasons: list[str] = []

    if current_yield is not None and current_yield < 90:
        risk_score += 35
        reasons.append(f"current yield {current_yield:.1f}% < 90%")
    elif current_yield is not None and current_yield < ctx.policy.min_yield_for_reduced_flow_pct:
        risk_score += 12
        reasons.append(f"yield {current_yield:.1f}% below reduced-flow threshold")

    if loss is not None and loss > 2:
        risk_score += 20
        reasons.append(f"yield loss {loss:.1f} pts")

    if ate and ate.abort_rate is not None and ate.abort_rate > ctx.policy.max_abort_rate:
        risk_score += 15
        reasons.append(f"abort rate {ate.abort_rate:.2%}")

    if prod and prod.escape_rate_ppm is not None and prod.escape_rate_ppm > ctx.policy.max_escape_rate_ppm:
        risk_score += 15
        reasons.append(f"escape {prod.escape_rate_ppm:.1f} ppm")

    if prod and context_lot_high_risk(ctx):
        risk_score += 15
        reasons.append(f"lot {ctx.lot_id} flagged high-failure")

    if debug and debug.confidence is not None and debug.confidence >= 0.85:
        risk_score += 18
        reasons.append(f"scan-debug confidence {debug.confidence:.0%}")

    if wafer and wafer.systematic_signature:
        risk_score += 10
        reasons.append(f"systematic: {wafer.systematic_signature}")

    risk_score = min(100.0, risk_score)
    if risk_score >= 50:
        risk_level = "High"
    elif risk_score >= 20:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # Adaptive
    if risk_level == "High" or (current_yield is not None and current_yield < 90):
        adaptive = AdaptiveTestingBlock(
            recommendation=f"Enable Extended Testing for Lot {ctx.lot_id}",
            flow_mode="extended",
            applicable_to=f"high-risk lot {ctx.lot_id}",
            rationale="; ".join(reasons) or "Yield excursion requires extended content.",
            trade_offs="Higher tester time/cost vs lower escape risk and better diagnosis.",
            business_impact="Protects quality and customer returns at expense of cycle time.",
            confidence=0.91,
        )
    elif (
        risk_level == "Low"
        and current_yield is not None
        and current_yield >= ctx.policy.min_yield_for_reduced_flow_pct
        and not (debug and debug.confidence and debug.confidence >= 0.85)
    ):
        adaptive = AdaptiveTestingBlock(
            recommendation="Run reduced pattern set for low-risk devices",
            flow_mode="reduced",
            applicable_to=f"low-risk lots of {ctx.device}",
            rationale=f"Yield {current_yield:.1f}% supports reduced content.",
            trade_offs="Lower cost/time; residual risk if process drifts.",
            business_impact="Reduces cost-of-test and frees tester capacity.",
            confidence=0.86,
        )
    else:
        adaptive = AdaptiveTestingBlock(
            recommendation="Maintain Full Test Flow",
            flow_mode="full",
            applicable_to=ctx.device,
            rationale="Mixed signals — preserve full coverage.",
            trade_offs="No immediate COT savings; maximum coverage retained.",
            business_impact="Stable production quality baseline.",
            confidence=0.76,
        )

    # Test stop
    if cov is not None and cov >= stop_threshold and adaptive.flow_mode != "extended":
        test_stop = TestStopBlock(
            recommendation=f"Stop testing after {stop_threshold:.1f}% effective coverage",
            stop_coverage_pct=stop_threshold,
            early_stop=True,
            rationale=f"Effective coverage {cov:.1f}% meets stop threshold.",
            trade_offs="Saves pattern time; forgoes marginal coverage.",
            business_impact="Direct reduction in test seconds per device.",
            confidence=0.88,
        )
    elif cov is not None:
        test_stop = TestStopBlock(
            recommendation="Continue testing until coverage target",
            stop_coverage_pct=None,
            early_stop=False,
            rationale=f"Coverage {cov:.1f}% below {stop_threshold:.1f}% stop gate.",
            trade_offs="More tester time to protect coverage floor.",
            business_impact="Avoids under-test escapes.",
            confidence=0.84,
        )
    else:
        assumptions.append("Coverage metrics unavailable — cannot recommend early stop.")
        test_stop = TestStopBlock(
            recommendation="Coverage data missing — do not early-stop",
            early_stop=False,
            rationale="No coverage values provided.",
            trade_offs="Conservative stance when metrics unknown.",
            business_impact="Prevents unsafe early-stop decisions.",
            confidence=0.55,
        )

    high_risk_lots = list(prod.high_failure_lots) if prod else []
    high_risk_lots += [h.lot_id for h in ctx.historical_lots if h.high_risk]
    if ctx.lot_id not in high_risk_lots and risk_level == "High":
        high_risk_lots.append(ctx.lot_id)
    high_risk_lots = sorted(set(high_risk_lots))

    risk_based = RiskBasedTestingBlock(
        recommendation=(
            "Enable extended testing only for high-risk lots"
            if risk_level != "Low"
            else "Standard flow sufficient; reserve extended testing for flagged lots"
        ),
        high_risk_lots=high_risk_lots,
        action_for_high_risk="Extended patterns + execute scan-debug actions before release",
        action_for_low_risk="Reduced/adaptive flow with coverage stop gate",
        rationale="; ".join(reasons) if reasons else "No strong risk markers.",
        trade_offs="Concentrates cost on risky material.",
        business_impact="Improves COT efficiency without blanket over-test.",
        confidence=0.82 if reasons else 0.65,
    )

    yield_recs: list[RecommendationItem] = []
    expected_yield = "N/A"
    if loss is not None and loss > 1:
        yield_recs.append(
            RecommendationItem(
                action="Trigger Yield Excursion Review",
                rationale=f"Yield loss {loss:.1f} pts vs historical baseline.",
                trade_offs="Engineering time vs shipping systematic fails.",
                business_impact="Contains excursion before customer impact.",
                confidence=0.9,
                estimated_impact={"yield_gap_pct": loss},
            )
        )
        expected_yield = f"Recover up to ~{min(loss, 3.0):.1f} pts if root cause closed"
    if debug and debug.debug_actions:
        yield_recs.append(
            RecommendationItem(
                action=f"Execute scan-debug on {debug.scan_chain or 'reported chain'}",
                rationale=f"Root cause={debug.suspected_root_cause or 'n/a'}; conf={debug.confidence}",
                trade_offs="Debug cycle time vs unresolved yield loss.",
                business_impact="Targets systematic fails driving yield loss.",
                confidence=float(debug.confidence or 0.7),
                estimated_impact={"debug_actions": debug.debug_actions},
            )
        )
    if wafer and (wafer.hotspots or wafer.defect_clustering or wafer.spatial_fail_clusters):
        clusters = wafer.hotspots or wafer.defect_clustering or wafer.spatial_fail_clusters
        yield_recs.append(
            RecommendationItem(
                action="Investigate wafer hotspots / defect clustering",
                rationale=f"Reported: {', '.join(clusters[:5])}",
                trade_offs="Fab feedback latency vs continued yield drag.",
                business_impact="Addresses spatial systematic yield loss.",
                confidence=0.76,
            )
        )
    if not yield_recs:
        yield_recs.append(
            RecommendationItem(
                action="Continue standard yield monitoring",
                rationale="No excursion signal in available inputs.",
                trade_offs="No extra screens.",
                business_impact="Maintains baseline yield controls.",
                confidence=0.7,
            )
        )

    cost_recs: list[RecommendationItem] = []
    time_saved = 0.0
    if pattern and pattern.estimated_test_time_saved and pattern.estimated_test_time_saved > 0:
        time_saved += pattern.estimated_test_time_saved
        cost_recs.append(
            RecommendationItem(
                action="Apply upstream pattern removals/reorders",
                rationale=(
                    f"Pattern agent estimates {pattern.estimated_test_time_saved:.1f}s saved; "
                    f"removed={pattern.patterns_removed}"
                ),
                trade_offs="Must hold coverage_after_optimization.",
                business_impact="Immediate COT reduction from upstream pattern agent.",
                confidence=0.82,
                estimated_impact={
                    "time_saved_s": pattern.estimated_test_time_saved,
                    "coverage_after_optimization": pattern.coverage_after_optimization,
                },
            )
        )
    if adaptive.flow_mode == "reduced" and ate and ate.execution_time_s:
        est = ate.execution_time_s * 0.2
        time_saved += est
        cost_recs.append(
            RecommendationItem(
                action="Reduce unnecessary patterns via reduced flow",
                rationale=f"~20% content cut on {ate.execution_time_s:.1f}s baseline.",
                trade_offs="Cost down vs small escape risk.",
                business_impact="Frees tester capacity for other products.",
                confidence=0.78,
                estimated_impact={"time_saved_s": est},
            )
        )
    elif adaptive.flow_mode == "extended":
        cost_recs.append(
            RecommendationItem(
                action="Defer cost reduction until yield/risk stabilizes",
                rationale="High-risk signals override COT cuts this lot.",
                trade_offs="Higher short-term cost; protects quality.",
                business_impact="Avoids false savings that inflate escapes.",
                confidence=0.88,
            )
        )
    if ate and ate.retest_count and ate.total_devices:
        rate = ate.retest_count / max(ate.total_devices, 1)
        if rate > 0.03:
            cost_recs.append(
                RecommendationItem(
                    action="Reduce retest via contact integrity and first-pass yield",
                    rationale=f"Retest rate {rate:.1%} ({ate.retest_count}/{ate.total_devices}).",
                    trade_offs="Setup effort vs recurring retest cost.",
                    business_impact="Lowers retest cost and cycle time.",
                    confidence=0.74,
                    estimated_impact={"retest_rate": rate},
                )
            )
    if not cost_recs:
        cost_recs.append(
            RecommendationItem(
                action="No strong cost lever from available data",
                rationale="Insufficient cost/timing inputs.",
                trade_offs="N/A",
                business_impact="Await richer cost telemetry.",
                confidence=0.6,
            )
        )

    coverage_recs: list[RecommendationItem] = []
    if cov is not None and ctx.coverage_report:
        cr = ctx.coverage_report
        coverage_recs.append(
            RecommendationItem(
                action="Maintain coverage floor with minimum pattern set",
                rationale=(
                    f"Effective {cov:.1f}% "
                    f"(SA={cr.stuck_at}, Tran={cr.transition}, PD={cr.path_delay}, CA={cr.cell_aware})"
                ),
                trade_offs="Do not remove patterns that breach floor.",
                business_impact="Preserves quality while enabling COT cuts above floor.",
                confidence=0.83,
            )
        )
        if pattern and pattern.patterns_added:
            coverage_recs.append(
                RecommendationItem(
                    action="Accept upstream transition/coverage pattern additions",
                    rationale=f"Added patterns: {pattern.patterns_added}",
                    trade_offs="Slight time increase for coverage recovery.",
                    business_impact="Closes known coverage gaps.",
                    confidence=0.8,
                )
            )
    else:
        coverage_recs.append(
            RecommendationItem(
                action="Coverage report missing — hold pattern reductions",
                rationale="Cannot verify fault coverage without report.",
                trade_offs="Conservative over-test risk.",
                business_impact="Avoids silent coverage loss.",
                confidence=0.6,
            )
        )

    production_recs: list[RecommendationItem] = []
    if prod and prod.historical_failures:
        production_recs.append(
            RecommendationItem(
                action="Monitor known historical failure modes",
                rationale=f"Modes: {', '.join(prod.historical_failures[:5])}",
                trade_offs="Slight monitoring overhead.",
                business_impact="Early detection of recurring issues.",
                confidence=0.72,
            )
        )
    if prod and prod.customer_returns:
        production_recs.append(
            RecommendationItem(
                action="Align screens with customer-return signatures",
                rationale=f"Returns: {', '.join(prod.customer_returns[:5])}",
                trade_offs="May add targeted tests.",
                business_impact="Reduces field returns and warranty cost.",
                confidence=0.78,
            )
        )
    if debug and debug.suspected_root_cause:
        production_recs.append(
            RecommendationItem(
                action="Hold lot disposition until scan-debug root cause cleared",
                rationale=debug.suspected_root_cause,
                trade_offs="Schedule delay vs escape risk.",
                business_impact="Prevents shipping systematic fails.",
                confidence=float(debug.confidence or 0.75),
            )
        )
    if not production_recs:
        production_recs.append(
            RecommendationItem(
                action="Proceed with adaptive strategy under standard production controls",
                rationale="No additional production blockers.",
                trade_offs="N/A",
                business_impact="Keeps factory flow moving.",
                confidence=0.7,
            )
        )

    multi_site: Optional[MultiSiteBlock] = None
    if ate and ate.site_utilization:
        vals = list(ate.site_utilization.values())
        avg = sum(vals) / len(vals)
        imbalance = max(vals) - min(vals)
        actions: list[str] = []
        if avg < 0.7:
            actions.append("Rebalance load / enable idle sites")
        if imbalance > 0.25:
            weak = min(ate.site_utilization, key=ate.site_utilization.get)  # type: ignore[arg-type]
            actions.append(f"Diagnose under-utilized site {weak}")
        multi_site = MultiSiteBlock(
            recommendation=(
                "Optimize multi-site parallelism and site health"
                if actions
                else "Multi-site configuration adequate"
            ),
            site_actions=actions or ["Maintain current site mapping"],
            rationale=f"Avg utilization {avg:.0%}, imbalance {imbalance:.0%}.",
            trade_offs="Engineering time vs throughput.",
            business_impact="Higher UPH and lower idle tester cost.",
            confidence=0.8,
        )
    elif ate and ate.site_count == 1 and ate.total_devices and ate.total_devices > 500:
        multi_site = MultiSiteBlock(
            recommendation="Evaluate multi-site enablement for high volume",
            site_actions=["Assess contactor/board readiness for multi-site"],
            rationale=f"Single-site with {ate.total_devices} devices.",
            trade_offs="CapEx vs throughput.",
            business_impact="Potential step-function capacity gain.",
            confidence=0.7,
        )

    # Aggregates from known numbers only
    if adaptive.flow_mode == "extended":
        est_time = "Net time increase expected (extended testing)"
        est_cost = "Cost reduction deferred due to high risk"
    elif time_saved > 0:
        est_time = f"~{time_saved:.1f}s per device from quantified levers"
        if cost and cost.cost_per_second_usd is not None:
            est_cost = f"~${time_saved * cost.cost_per_second_usd:.4f} per device"
        elif cost and cost.tester_hour_cost_usd is not None:
            est_cost = f"~${cost.tester_hour_cost_usd * (time_saved / 3600):.4f} tester-time per device"
        else:
            est_cost = "Time savings quantified; dollar savings need cost_per_second_usd"
    else:
        est_time = "Not quantified — insufficient timing inputs"
        est_cost = "Not quantified — insufficient cost inputs"

    strategy = (
        f"{adaptive.flow_mode.upper()} flow for {ctx.device} lot {ctx.lot_id}; "
        f"risk={risk_level}; "
        + (
            f"early-stop at {test_stop.stop_coverage_pct:.1f}%"
            if test_stop.early_stop and test_stop.stop_coverage_pct is not None
            else "no early-stop"
        )
    )
    business = (
        f"Strategy balances yield protection and COT for {ctx.device}. "
        f"Risk={risk_level} (score {risk_score:.0f}/100). "
        f"Time: {est_time}. Cost: {est_cost}. Yield: {expected_yield}."
    )
    overall = max(
        0.0,
        min(
            1.0,
            (adaptive.confidence + test_stop.confidence + risk_based.confidence) / 3 - 0.03 * len(gaps),
        ),
    )

    return OptimizationRecommendation(
        device=ctx.device,
        lot_id=ctx.lot_id,
        summary=(
            f"Adaptive strategy for lot {ctx.lot_id} ({ctx.device}): "
            f"{adaptive.recommendation}. Risk level {risk_level}."
        ),
        recommended_strategy=strategy,
        risk_level=risk_level,  # type: ignore[arg-type]
        confidence=round(overall, 3),
        risk_score=risk_score,
        adaptive_testing=adaptive,
        test_stop=test_stop,
        risk_based_testing=risk_based,
        yield_recommendations=yield_recs,
        cost_recommendations=cost_recs,
        coverage_recommendations=coverage_recs,
        production_recommendations=production_recs,
        multi_site_optimization=multi_site,
        estimated_time_reduction=est_time,
        estimated_cost_reduction=est_cost,
        expected_yield_improvement=expected_yield,
        business_impact=business,
        assumptions=assumptions,
        data_gaps=gaps,
        engine="heuristic",
    )


def context_lot_high_risk(ctx: OptimizationContext) -> bool:
    if ctx.production_history and ctx.lot_id in ctx.production_history.high_failure_lots:
        return True
    return any(h.lot_id == ctx.lot_id and h.high_risk for h in ctx.historical_lots)
