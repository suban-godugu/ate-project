"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { RecommendationCenterContent } from "@/components/recommendation/RecommendationCenterContent";

export default function RecommendationAnalysisPage() {
  return (
    <DashboardLayout
      title="Recommendation Analysis"
      subtitle="AI-powered recommendation engine for Pattern Optimization, Scan Debug and Test Optimization"
      searchPlaceholder="Search recommendations, patterns, scan chains, lots..."
      primaryActionLabel="Generate AI Recommendations"
      pageId="recommendation-analysis"
    >
      <RecommendationCenterContent />
    </DashboardLayout>
  );
}
