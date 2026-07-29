import { recentAlerts } from "@/lib/alertsData";
import { executiveKPIs, patternAnalysisData } from "@/lib/dummyData";
import { recentFailures as lbistRecentFailures } from "@/lib/lbistData";
import { recentFailures as mbistRecentFailures } from "@/lib/mbistData";
import {
  scanChainRecommendations,
  unifiedRecommendations,
} from "@/lib/recommendationData";
import { failingChainsData, failureRecords } from "@/lib/scanChainData";
import type { SearchResultItem } from "@/types/platform";

function pushResult(
  results: SearchResultItem[],
  item: Omit<SearchResultItem, "matchedField"> & { fields: string[] },
  query: string
) {
  const q = query.toLowerCase();
  const matched = item.fields.find((f) => f.toLowerCase().includes(q));
  if (matched) {
    results.push({ ...item, matchedField: matched });
  }
}

export function searchPlatform(query: string): SearchResultItem[] {
  if (!query.trim()) return [];
  const results: SearchResultItem[] = [];

  executiveKPIs.forEach((kpi) => {
    pushResult(
      results,
      {
        id: kpi.id,
        title: kpi.title,
        subtitle: kpi.value,
        category: "Dashboard",
        route: "/dashboard",
        fields: [kpi.id, kpi.title, kpi.value],
      },
      query
    );
  });

  patternAnalysisData.forEach((row) => {
    pushResult(
      results,
      {
        id: row.id,
        title: `Pattern ${row.id}`,
        subtitle: `ROI ${row.roiScore} · ${row.recommendation}`,
        category: "Dashboard",
        route: "/dashboard",
        fields: [row.id, String(row.roiScore), row.recommendation],
      },
      query
    );
  });

  failingChainsData.forEach((row) => {
    pushResult(
      results,
      {
        id: row.chainId,
        title: row.chainId,
        subtitle: `${row.patternId} · ${row.failType}`,
        category: "Scan Chain",
        route: "/dashboard/scan-chain",
        fields: [row.chainId, row.patternId, row.chip, row.failType, row.rootCause],
      },
      query
    );
  });

  failureRecords.forEach((row) => {
    pushResult(
      results,
      {
        id: row.failureId,
        title: row.failureId,
        subtitle: `${row.chainId} · ${row.failType}`,
        category: "Scan Chain",
        route: "/dashboard/scan-chain",
        fields: [row.failureId, row.chainId, row.failType, row.severity],
      },
      query
    );
  });

  mbistRecentFailures.forEach((row) => {
    pushResult(
      results,
      {
        id: row.memoryId,
        title: row.memoryId,
        subtitle: `${row.bank} · ${row.status}`,
        category: "MBIST",
        route: "/dashboard/mbist",
        fields: [row.memoryId, row.memoryType, row.bank, row.status, row.failureType],
      },
      query
    );
  });

  lbistRecentFailures.forEach((row) => {
    pushResult(
      results,
      {
        id: row.sessionId,
        title: row.logicBlock,
        subtitle: `${row.controller} · ${row.status}`,
        category: "LBIST",
        route: "/dashboard/lbist",
        fields: [row.sessionId, row.logicBlock, row.controller, row.misrSignature],
      },
      query
    );
  });

  unifiedRecommendations.forEach((row) => {
    pushResult(
      results,
      {
        id: row.id,
        title: row.id,
        subtitle: `${row.sourceModule} · ${row.category}`,
        category: "Recommendation Analysis",
        route: "/dashboard/recommendation-analysis",
        fields: [row.id, row.sourceModule, row.category, row.assignedEngineer],
      },
      query
    );
  });

  scanChainRecommendations.forEach((row) => {
    pushResult(
      results,
      {
        id: row.id,
        title: row.id,
        subtitle: `${row.scanChain} · ${row.recommendation}`,
        category: "Recommendation Analysis",
        route: "/dashboard/recommendation-analysis",
        fields: [row.id, row.scanChain, row.pattern, row.recommendation],
      },
      query
    );
  });

  recentAlerts.forEach((row) => {
    pushResult(
      results,
      {
        id: row.id,
        title: row.id,
        subtitle: `${row.sourceModule} · ${row.severity}`,
        category: "Alerts",
        route: "/dashboard/alerts",
        fields: [row.id, row.description, row.sourceModule, row.severity, row.lotId, row.waferId],
      },
      query
    );
  });

  return results.slice(0, 12);
}
