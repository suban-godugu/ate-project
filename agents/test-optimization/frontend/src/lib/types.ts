export type RiskLevel = "Low" | "Medium" | "High";
export type FlowMode = "full" | "reduced" | "extended" | "skip";
export type Engine = "llm" | "heuristic";

export interface AdaptiveTestingBlock {
  recommendation: string;
  flow_mode: FlowMode;
  applicable_to: string | null;
  rationale: string;
  trade_offs: string;
  business_impact: string;
  confidence: number;
}

export interface TestStopBlock {
  recommendation: string;
  stop_coverage_pct: number | null;
  early_stop: boolean;
  rationale: string;
  trade_offs: string;
  business_impact: string;
  confidence: number;
}

export interface RiskBasedTestingBlock {
  recommendation: string;
  high_risk_lots: string[];
  action_for_high_risk: string;
  action_for_low_risk: string;
  rationale: string;
  trade_offs: string;
  business_impact: string;
  confidence: number;
}

export interface MultiSiteBlock {
  recommendation: string;
  site_actions: string[];
  rationale: string;
  trade_offs: string;
  business_impact: string;
  confidence: number;
}

export interface RecommendationItem {
  action: string;
  rationale: string;
  trade_offs: string;
  business_impact: string;
  confidence: number;
  estimated_impact: Record<string, unknown>;
}

export interface OptimizationRecommendation {
  id: string;
  created_at: string;
  device: string;
  lot_id: string;
  summary: string;
  recommended_strategy: string;
  risk_level: RiskLevel;
  confidence: number;
  risk_score: number;
  adaptive_testing: AdaptiveTestingBlock;
  test_stop: TestStopBlock;
  risk_based_testing: RiskBasedTestingBlock;
  yield_recommendations: RecommendationItem[];
  cost_recommendations: RecommendationItem[];
  coverage_recommendations: RecommendationItem[];
  production_recommendations: RecommendationItem[];
  multi_site_optimization: MultiSiteBlock | null;
  estimated_time_reduction: string;
  estimated_cost_reduction: string;
  expected_yield_improvement: string;
  business_impact: string;
  assumptions: string[];
  data_gaps: string[];
  engine: Engine;
}

export interface HealthResponse {
  status: string;
  agent: string;
  version: string;
  llm_enabled: boolean;
  model: string | null;
  environment: string;
}

export interface RecommendationListResponse {
  items: OptimizationRecommendation[];
  total: number;
}

export interface AnalyticsSummary {
  total_recommendations: number;
  avg_confidence: number;
  risk_distribution: Record<string, number>;
  avg_yield: number | null;
  recent: OptimizationRecommendation[];
}

export interface SamplesResponse {
  samples: string[];
}
