# VERILUMEN / COMPTY — Complete Prompt Archive

**Generated:** 2026-07-07 · **Updated:** 2026-07-10

**Repositories:**
- Frontend (dev): `c1-com/ate-dashboard`
- Frontend (sync): `bd-1/dashboard`
- Backend: `bd-1/backend`

---

# Part A — STEP Prompt Archive (prompts.csv)

Total entries: **54**

## STEP 1 — Project Setup

**Date:** 2026-06-29

### Prompt

```text
Create Next.js app with TypeScript Tailwind ESLint App Router src directory. Install recharts framer-motion react-icons lucide-react react-query clsx tailwind-merge. Init shadcn and add button card table dropdown-menu input select slider avatar badge.
```

**Files:** package.json; components.json; src/app/layout.tsx; src/app/globals.css; src/lib/utils.ts; src/components/ui/*.tsx

**Components:** shadcn UI primitives (Button Card Table DropdownMenu Input Select Slider Avatar Badge)

---

## STEP 2 — Folder Structure

**Date:** 2026-06-29

### Prompt

```text
Define src folder structure for dashboard components layout cards charts tables filters optimization results lib types hooks styles.
```

**Files:** src/types/dashboard.ts; src/lib/dummyData.ts; src/styles/globals.css

**Components:** Project scaffolding folders

---

## STEP 3 — Layout (Cursor Prompt 1)

**Date:** 2026-06-29

### Prompt

```text
Premium enterprise dashboard layout: 280px sidebar 72px navbar 24px padding/gap CSS Grid glassmorphism purple accent dark theme responsive. Background #090B12 Cards #111827 Border #2D3748 Accent #7C3AED Rounded 20px.
```

**Files:** src/components/layout/DashboardLayout.tsx; src/components/layout/Sidebar.tsx; src/components/layout/TopNavbar.tsx; src/styles/globals.css; src/app/globals.css

**Components:** DashboardLayout Sidebar TopNavbar

---

## STEP 4 — Sidebar (Cursor Prompt 2)

**Date:** 2026-06-29

### Prompt

```text
280px sidebar #0A1020 background. Header ATE Intelligence Enterprise Platform. Navigation: Dashboard Scan Chain Analysis MBIST LBIST Wafer Analysis Cost Intelligence Alerts Settings. Active menu purple gradient rounded-xl glow. Icons for every menu. Quick Filters: Date Range Fab Tester Product Reset Filters. Alerts badge 5. Sidebar fixed.
```

**Files:** src/components/layout/Sidebar.tsx

**Components:** Sidebar with navigation and Quick Filters

---

## STEP 5 — Top Navbar (Cursor Prompt 3)

**Date:** 2026-06-29

### Prompt

```text
72px sticky navbar. Left page title Executive Dashboard. Center large search bar. Right Calendar Notifications Profile Export Report AI Optimize. User Alex Johnson Admin. Notification badge 12. Glass backdrop blur.
```

**Files:** src/components/layout/TopNavbar.tsx

**Components:** TopNavbar

---

## STEP 6 — Executive KPI Cards (Cursor Prompt 4)

**Date:** 2026-06-29

### Prompt

```text
Six KPI cards in 6-column grid. Each card: icon title large value weekly trend sparkline hover animation. Metrics: Total Test Cost Cost per Wafer Cost per Die Test Time Yield ROI Improvement. Recharts AreaChart sparklines Framer Motion entrance. Glass card gradient border.
```

**Files:** src/components/cards/ExecutiveCard.tsx; src/lib/dummyData.ts (executiveKPIs); src/types/dashboard.ts (ExecutiveKPI)

**Components:** ExecutiveCard ExecutiveKPIGrid

---

## STEP 7 — Wafer Heatmap (Cursor Prompt 5)

**Date:** 2026-06-29

### Prompt

```text
Wafer Cost Heatmap canvas 40x40 circular wafer grid. Pan zoom reset fullscreen. Overlay dropdown fail density yield cost. Color legend green yellow orange red. Tooltip on hover. Spatial AI analysis.
```

**Files:** src/components/charts/WaferHeatmap.tsx; src/lib/dummyData.ts (generateWaferHeatData); src/types/dashboard.ts (HeatmapOverlay)

**Components:** WaferHeatmap

---

## STEP 8 — Pattern Analysis Table (Cursor Prompt 6)

**Date:** 2026-06-29

### Prompt

```text
Enterprise table columns: Pattern ID Test Time Cost Fail Rate Detect Power ROI Score Recommendation. Badges Keep Review Remove. Sticky header pagination search sorting hover row highlight.
```

**Files:** src/components/tables/PatternTable.tsx; src/lib/dummyData.ts (patternAnalysisData); src/types/dashboard.ts (PatternRow Recommendation)

**Components:** PatternTable

---

## STEP 9 — Cost Trend Chart (Cursor Prompt 7)

**Date:** 2026-06-29

### Prompt

```text
Recharts line chart Total Cost and Cost per Wafer over 7 days Mon-Sun. Smooth animated lines dark theme legend. Glass card wrapper.
```

**Files:** src/components/charts/CostTrendChart.tsx; src/lib/dummyData.ts (costTrendData); src/types/dashboard.ts (CostTrendPoint)

**Components:** CostTrendChart

---

## STEP 10 — Optimization Engine (Cursor Prompt 8)

**Date:** 2026-06-29

### Prompt

```text
Three sliders Maximum Cost Yield Target Maximum Test Time with live values. Run AI Optimization purple button with sparkle icon animated loading state.
```

**Files:** src/components/optimization/OptimizationEngine.tsx; src/types/dashboard.ts (OptimizationParams)

**Components:** OptimizationEngine

---

## STEP 11 — Optimization Results (Cursor Prompt 9)

**Date:** 2026-06-29

### Prompt

```text
Result card after optimization: cost reduction time savings projected yield patterns reduced total savings. Green positive values. View Optimized Pattern Set button hover animation.
```

**Files:** src/components/results/OptimizationResult.tsx; src/lib/dummyData.ts (defaultOptimizationResults); src/types/dashboard.ts (OptimizationResults)

**Components:** OptimizationResult

---

## STEP 12 — Final Polish (Cursor Prompt 10)

**Date:** 2026-06-29

### Prompt

```text
Inter font glassmorphism gradient borders hover lift responsive desktop tablet mobile. Integrate all components dummy JSON production ready enterprise SaaS quality comparable to Synopsys Siemens NVIDIA Intel dashboards.
```

**Files:** src/app/dashboard/page.tsx; src/app/layout.tsx; src/app/globals.css; src/styles/globals.css; src/contexts/ThemeContext.tsx

**Components:** Full dashboard integration and polish

---

## SETTINGS — Settings Page

**Date:** 2026-06-29

### Prompt

```text
Theme Settings: appearance accent sidebar card font compact animations reset. Account Presets: profile role department dashboard language timezone notifications save. Persist to localStorage. Live theme preview.
```

**Files:** src/app/settings/page.tsx; src/types/theme.ts; src/contexts/ThemeContext.tsx; src/components/ui/switch.tsx; src/components/ui/radio-group.tsx; src/components/ui/label.tsx; src/components/settings/*.tsx

**Components:** Settings page ThemeProvider ThemeSettingsPanel AccountPresetsPanel

---

## INTEGRATION — Dashboard Page Integration

**Date:** 2026-06-29

### Prompt

```text
Wire all components into main dashboard page with shared dummy data and responsive grid layout. Redirect root / to /dashboard.
```

**Files:** src/app/dashboard/page.tsx; src/app/page.tsx

**Components:** DashboardPage

---

## STEP 13 — Scan Chain Analysis Dashboard

**Date:** 2026-06-29

### Prompt

```text
Cursor AI Prompt – Scan Chain Analysis Dashboard. Create premium enterprise Scan Chain Analysis dashboard for ATE Intelligence Enterprise Platform. Stack: Next.js 15 TypeScript TailwindCSS shadcn/ui Framer Motion Recharts Lucide. Theme: Background #090B12 Cards #111827 Border #2D3748 Accent #7C3AED Rounded 20px Glass Effect smooth animations responsive. LEFT SIDEBAR: ATE Intelligence Enterprise Platform nav Dashboard Scan Chain Analysis (Active) MBIST LBIST Wafer Cost Intelligence Alerts Settings purple gradient active glow fixed. TOP NAV: Scan Chain Analysis title search placeholder Search scan chains patterns chips flops Calendar Notifications Profile Export Report AI Diagnose sticky. SECONDARY NAV tabs below title: Overview Pattern Analysis Failure Analysis Scan Diagnosis Overview active purple underline bold smooth tab switch content. OVERVIEW TAB: 6 KPI cards Total Scan Chains Failing Scan Chains Failing Flops Scan Coverage Average Test Time Pattern Count icon title value trend sparkline hover. Row 2: Scan Chain Health Summary donut Healthy Warning Failing Unknown center Total Chains; Top Failing Chips horizontal bar top 10; Scan Chain Heatmap grid green yellow orange red legend. Row 3: Recent Failing Scan Chains table Chain ID Pattern ID Chip Fail Cycle Fail Type Suspected Root Cause Diagnosis Status Action search pagination sorting; Failure Distribution pie Stuck At Transition Bridging Timing Unknown; AI Diagnosis Summary card root cause critical chains debug area repair success confidence Run AI Diagnosis button. PATTERN ANALYSIS TAB: KPIs Total Patterns Active Patterns Pattern Coverage Pattern Efficiency Pattern Runtime Compressed Patterns; charts Pattern Execution Trend Pattern Cost Pattern Coverage Pattern Density; tables Pattern Summary Pattern Recommendations. FAILURE ANALYSIS TAB: KPIs Total Failures Critical Warning Recovered Root Causes Repair Rate; charts Failure Trend Failure Type Distribution Failing Regions Failure Density; tables Failure Records Root Cause Analysis AI Recommendation. SCAN DIAGNOSIS TAB: KPIs Diagnosed Unknown Repair Suggestions Diagnosis Accuracy Coverage Confidence; charts Diagnosis Timeline Chain Connectivity Graph Failure Propagation AI Confidence; tables Diagnosis Report Suspected Scan Cells Recommended Debug Points Repair Priority. COMMON: glass cards border hover lift shadow rounded 20px 24px spacing grid 2xl desktop 2 col tablet 1 col mobile. Animations fade slide scale hover glow sparkline. Typography Inter bold white headers gray subtitles large colored values. Reusable components dummy JSON separate components clean folder structure responsive production ready enterprise SaaS Synopsys Siemens NVIDIA Intel quality.
```

**Files:** src/app/scan-chain/page.tsx; src/types/scanChain.ts; src/lib/scanChainData.ts; src/components/scan-chain/KPICard.tsx; src/components/scan-chain/ScanChainTabs.tsx; src/components/scan-chain/ChartCard.tsx; src/components/scan-chain/DataTable.tsx; src/components/scan-chain/ScanChainHeatmap.tsx; src/components/scan-chain/AIDiagnosisCard.tsx; src/components/scan-chain/ConnectivityGraph.tsx; src/components/scan-chain/charts/PieCharts.tsx; src/components/scan-chain/charts/BarCharts.tsx; src/components/scan-chain/charts/LineCharts.tsx; src/components/scan-chain/tabs/OverviewTab.tsx; src/components/scan-chain/tabs/PatternAnalysisTab.tsx; src/components/scan-chain/tabs/FailureAnalysisTab.tsx; src/components/scan-chain/tabs/ScanDiagnosisTab.tsx; src/components/layout/Sidebar.tsx; src/components/layout/TopNavbar.tsx; src/components/layout/DashboardLayout.tsx

**Components:** KPICard KPIGrid ScanChainTabs ChartCard DataTable ScanChainHeatmap AIDiagnosisCard ConnectivityGraph DonutChart DistributionPie HorizontalBarChart VerticalBarChart TrendLineChart TrendAreaChart OverviewTab PatternAnalysisTab FailureAnalysisTab ScanDiagnosisTab

---

## STEP 14 — Record All Prompts

**Date:** 2026-06-29

### Prompt

```text
Record the all prompt in csv and readme file.
```

**Files:** prompts.csv; README.md

**Components:** Prompt documentation archive

---

## STEP 15 — Automatic Prompt Recording

**Date:** 2026-06-29

### Prompt

```text
make the automatic record the prompt in csv and readme file.
```

**Files:** .cursor/hooks.json; .cursor/hooks/prompt-recorder.mjs; .cursor/hooks/record-prompt-start.mjs; .cursor/hooks/record-prompt-stop.mjs; .cursor/hooks/track-file-edit.mjs; scripts/record-prompt.mjs; package.json; .gitignore

**Components:** prompt-recorder record-prompt-start record-prompt-stop track-file-edit

---

## STEP 16 — Recommendation Analysis Sidebar

**Date:** 2026-06-29

### Prompt

```text
Add Recommendation Analysis to sidebar between Cost Intelligence and Alerts. Sparkles icon route /dashboard/recommendation-analysis. Purple gradient active state hover scale accessibility. Do not redesign sidebar.
```

**Files:** src/components/layout/Sidebar.tsx; src/app/dashboard/recommendation-analysis/page.tsx

**Components:** Sidebar RecommendationAnalysisPage

---

## STEP 17 — MBIST Analysis Dashboard

**Date:** 2026-06-29

### Prompt

```text
Create premium enterprise MBIST Analysis dashboard. Stack Next.js TypeScript Tailwind shadcn Framer Motion Recharts Lucide. Theme dark enterprise glassmorphism. Sidebar MBIST Analysis active. Header MBIST Analysis subtitle Memory Built-In Self-Test Analytics. Tabs Overview Memory Health Failure Analysis Diagnosis AI Recommendation. Overview 6 KPIs memory health donut failure by bank heatmap failures table failure pie AI diagnosis. Memory Health KPIs utilization temperature access density charts. Failure Analysis KPIs trend type bank heatmap records table. Diagnosis KPIs timeline correlation connectivity root cause graphs diagnosis fail address repair tables. AI Recommendation risk cards recommendations table. Route /mbist.
```

**Files:** src/app/mbist/page.tsx; src/types/mbist.ts; src/lib/mbistData.ts; src/components/mbist/KPICard.tsx; src/components/mbist/MBISTTabs.tsx; src/components/mbist/MBISTHeatmap.tsx; src/components/mbist/MBISTAIDiagnosisCard.tsx; src/components/mbist/MemoryGraphs.tsx; src/components/mbist/tabs/OverviewTab.tsx; src/components/mbist/tabs/MemoryHealthTab.tsx; src/components/mbist/tabs/FailureAnalysisTab.tsx; src/components/mbist/tabs/DiagnosisTab.tsx; src/components/mbist/tabs/AIRecommendationTab.tsx; src/components/layout/Sidebar.tsx; src/components/layout/TopNavbar.tsx; src/components/layout/DashboardLayout.tsx

**Components:** MBISTTabs KPIGrid MBISTHeatmap MBISTAIDiagnosisCard MemoryConnectivityGraph RootCauseGraph OverviewTab MemoryHealthTab FailureAnalysisTab DiagnosisTab AIRecommendationTab

---

## STEP 18 — LBIST Analysis Dashboard

**Date:** 2026-06-29

### Prompt

```text
Create premium enterprise LBIST Analysis dashboard. Subtitle Logic Built-In Self-Test Analytics Coverage and Diagnosis. Tabs Overview Coverage Analysis Failure Analysis Diagnosis AI Recommendation. Overview 6 KPIs coverage donut failure by module heatmap failures table failure pie AI diagnosis. Coverage Analysis KPIs trend block efficiency detection heatmap. Failure Analysis KPIs trend distribution density records tables. Diagnosis timeline correlation connectivity coverage correlation tables AI diagnosis. AI Recommendation 7 risk cards recommendations table. Route /lbist. Same design as Executive Scan Chain MBIST dashboards.
```

**Files:** src/app/lbist/page.tsx; src/types/lbist.ts; src/lib/lbistData.ts; src/components/lbist/KPICard.tsx; src/components/lbist/LBISTTabs.tsx; src/components/lbist/LBISTHeatmap.tsx; src/components/lbist/LBISTAIDiagnosisCard.tsx; src/components/lbist/LogicGraphs.tsx; src/components/lbist/tabs/OverviewTab.tsx; src/components/lbist/tabs/CoverageAnalysisTab.tsx; src/components/lbist/tabs/FailureAnalysisTab.tsx; src/components/lbist/tabs/DiagnosisTab.tsx; src/components/lbist/tabs/AIRecommendationTab.tsx; src/components/layout/Sidebar.tsx

**Components:** LBISTTabs KPIGrid LBISTHeatmap LBISTAIDiagnosisCard LogicConnectivityGraph OverviewTab CoverageAnalysisTab FailureAnalysisTab DiagnosisTab AIRecommendationTab

---

## STEP 19 — Recommendation Analysis Dashboard

**Date:** 2026-06-29

### Prompt

```text
Create premium enterprise Recommendation Analysis dashboard centralized AI recommendation module consolidating Scan Chain MBIST LBIST and Wafer Analysis. Route /recommendation-analysis. Header subtitle AI-powered unified recommendations. Primary action Generate AI Recommendations. Tabs Overview Scan Chain MBIST LBIST Wafer Analysis. Overview 6 KPIs source donut priority bar trend line unified table AI executive summary recommendation engine workflow bottom AI summary. Module tabs domain KPIs charts tables. Priority badges Critical High Medium Low. Dark enterprise glassmorphism theme.
```

**Files:** src/app/recommendation-analysis/page.tsx; src/types/recommendation.ts; src/lib/recommendationData.ts; src/components/recommendation/KPICard.tsx; src/components/recommendation/RecommendationTabs.tsx; src/components/recommendation/Badges.tsx; src/components/recommendation/AIExecutiveSummaryCard.tsx; src/components/recommendation/EnginePanels.tsx; src/components/recommendation/WaferRecHeatmap.tsx; src/components/recommendation/tabs/OverviewTab.tsx; src/components/recommendation/tabs/ScanChainTab.tsx; src/components/recommendation/tabs/MbistTab.tsx; src/components/recommendation/tabs/LbistTab.tsx; src/components/recommendation/tabs/WaferTab.tsx; src/components/layout/Sidebar.tsx; src/app/dashboard/recommendation-analysis/page.tsx

**Components:** RecommendationTabs KPIGrid PriorityBadge ModuleBadge StatusBadge AIExecutiveSummaryCard RecommendationEnginePanel WorkflowPanel BottomAISummaryPanel OverviewTab ScanChainTab MbistTab LbistTab WaferTab WaferRecHeatmap

---

## STEP 20 — Cost Intelligence Dashboard

**Date:** 2026-06-29

### Prompt

```text
Create premium enterprise Cost Intelligence dashboard. Route /cost-intelligence. Subtitle analyze and optimize semiconductor test costs across Scan Chain MBIST LBIST and Wafer Analysis. Primary action Generate Cost Optimization. Tabs Overview Scan Chain Cost MBIST Cost LBIST Cost Wafer Cost AI Cost Optimization. Overview 6 KPIs cost contribution donut cost breakdown bar monthly trend stacked distribution product cost table AI cost summary enterprise summary. Module tabs KPIs charts tables. AI optimization recommendation table engine categories enterprise cost summary.
```

**Files:** src/app/cost-intelligence/page.tsx; src/types/costIntelligence.ts; src/lib/costIntelligenceData.ts; src/components/cost-intelligence/KPICard.tsx; src/components/cost-intelligence/CostTabs.tsx; src/components/cost-intelligence/CostCharts.tsx; src/components/cost-intelligence/CostPanels.tsx; src/components/cost-intelligence/WaferCostHeatmap.tsx; src/components/cost-intelligence/tabs/OverviewTab.tsx; src/components/cost-intelligence/tabs/ScanChainCostTab.tsx; src/components/cost-intelligence/tabs/MbistCostTab.tsx; src/components/cost-intelligence/tabs/LbistCostTab.tsx; src/components/cost-intelligence/tabs/WaferCostTab.tsx; src/components/cost-intelligence/tabs/AICostOptimizationTab.tsx; src/components/layout/Sidebar.tsx

**Components:** CostTabs KPIGrid ModuleHorizontalBarChart StackedCostBarChart AICostSummaryCard CostOptimizationEnginePanel EnterpriseCostSummaryPanel OverviewTab ScanChainCostTab MbistCostTab LbistCostTab WaferCostTab AICostOptimizationTab WaferCostHeatmap

---

## STEP 21 — Alerts Dashboard

**Date:** 2026-06-29

### Prompt

```text
Create premium enterprise Alerts dashboard real-time monitoring and notification center consolidating Scan Chain MBIST LBIST Wafer Cost Intelligence and AI Recommendation alerts. Route /alerts. Subtitle monitor and manage real-time alerts. Primary action Mark All as Read. Tabs Overview Scan Chain Alerts MBIST Alerts LBIST Alerts Wafer Alerts Cost Alerts AI Recommendation Alerts. Overview 6 KPIs alert distribution donut severity bar trend line recent alerts table critical alert summary workflow executive summary. Module tabs KPIs charts tables. Severity badges Critical High Medium Low. Alert workflow animated steps.
```

**Files:** src/app/alerts/page.tsx; src/types/alerts.ts; src/lib/alertsData.ts; src/components/alerts/KPICard.tsx; src/components/alerts/AlertTabs.tsx; src/components/alerts/Badges.tsx; src/components/alerts/AlertPanels.tsx; src/components/alerts/WaferAlertHeatmap.tsx; src/components/alerts/tabs/OverviewTab.tsx; src/components/alerts/tabs/ScanChainAlertsTab.tsx; src/components/alerts/tabs/MbistAlertsTab.tsx; src/components/alerts/tabs/LbistAlertsTab.tsx; src/components/alerts/tabs/WaferAlertsTab.tsx; src/components/alerts/tabs/CostAlertsTab.tsx; src/components/alerts/tabs/AIRecommendationAlertsTab.tsx; src/components/layout/Sidebar.tsx

**Components:** AlertTabs KPIGrid SeverityBadge AlertStatusBadge ModuleBadge CriticalAlertSummaryCard AlertWorkflowPanel ExecutiveAlertSummaryPanel OverviewTab ScanChainAlertsTab MbistAlertsTab LbistAlertsTab WaferAlertsTab CostAlertsTab AIRecommendationAlertsTab WaferAlertHeatmap

---

## STEP 22 — Upload Test Data

**Date:** 2026-06-29

### Prompt

```text
Add enterprise Upload Test Data feature top navbar UploadCloud button purple gradient modal drag-drop react-dropzone dataset category metadata progress upload history. Supported STDF STIL WGL CSV XLSX JSON ZIP XML max 10GB. Frontend UI UX only no backend simulated progress toast client-side history.
```

**Files:** src/components/upload/UploadDataModal.tsx; src/components/upload/UploadDropzone.tsx; src/components/upload/UploadProgressPanel.tsx; src/components/upload/UploadHistoryTable.tsx; src/components/upload/UploadToastStack.tsx; src/contexts/UploadContext.tsx; src/types/upload.ts; src/lib/uploadData.ts; src/components/ui/dialog.tsx; src/components/ui/progress.tsx; src/components/layout/TopNavbar.tsx; src/app/layout.tsx

**Components:** UploadDataModal UploadDropzone UploadProgressPanel DataUploadHistoryTable UploadProvider UploadToastStack

---

## STEP 23 — Upload Log File

**Date:** 2026-06-29

### Prompt

```text
Add enterprise Upload Log File button beside Upload Data FileText dark glass purple border modal ATE log upload log source tester metadata validation progress 5-step pipeline AI log summary upload history actions. Supported STDF STIL WGL LOG TXT CSV JSON XML ZIP GZ max 5GB. Frontend UI UX only no backend toast notifications.
```

**Files:** src/components/upload/UploadLogFileModal.tsx; src/components/upload/UploadDataModal.tsx; src/components/upload/UploadDropzone.tsx; src/components/upload/UploadProgressPanel.tsx; src/components/upload/UploadHistoryTable.tsx; src/contexts/UploadContext.tsx; src/types/upload.ts; src/lib/uploadData.ts; src/components/layout/TopNavbar.tsx

**Components:** UploadLogFileModal LogUploadHistoryTable ValidationResult PipelineStep AILogSummary

---

## STEP 24 — Complete Remaining Platform Functionality

**Date:** 2026-06-29

### Prompt

```text
Complete remaining frontend functionality for ATE Intelligence Enterprise Platform. Zustand stores filters user uploads notifications settings. Route migration to /dashboard/* with redirects and wafer-analysis page. Global search calendar notifications export responsive nav sidebar. Filter engine primary actions AI diagnosis apply recommendation. Upload persistence profile loading empty error states accessibility. Do not redesign page shell.
```

**Files:** src/stores/*.ts; src/app/dashboard/wafer-analysis/page.tsx; src/components/filters/*; src/components/search/*; src/components/notifications/*; src/components/export/*; src/components/ai/*; src/components/states/*

**Components:** FilterStore UserStore UploadStore NotificationStore SettingsStore GlobalSearch ExportPanel AIDiagnosisPanel ApplyRecommendationButton

---

## STEP 25 — Pattern Analysis KPI Dashboard

**Date:** 2026-06-29

### Prompt

```text
Scan Chain Pattern Analysis tab enterprise KPI dashboard. 11 KPIs PA-001 to PA-011: Total Patterns Active Patterns Pattern Coverage Pattern Efficiency Pattern Runtime Compressed Patterns Pattern Import Rate Pattern Redundancy Pattern Similarity Pattern Cluster Count Pattern Optimization Score. Charts: Pattern Import Trend Pattern Coverage Trend Pattern Cluster Distribution donut Pattern Similarity Scatter. Table: Pattern ID Category Coverage Efficiency Runtime Redundancy Similarity Cluster Recommendation Priority Status. Dark enterprise glass theme Recharts Framer Motion.
```

**Files:** src/components/scan-chain/tabs/PatternAnalysisTab.tsx; src/components/scan-chain/pattern/PatternKPIGrid.tsx; src/components/scan-chain/pattern/PatternImportTrendChart.tsx; src/components/scan-chain/pattern/PatternCoverageTrendChart.tsx; src/components/scan-chain/pattern/PatternClusterPieChart.tsx; src/components/scan-chain/pattern/PatternSimilarityScatter.tsx; src/components/scan-chain/pattern/PatternAnalysisTable.tsx; src/types/scanChain.ts; src/lib/scanChainData.ts; src/styles/globals.css (.pattern-kpi-grid)

**Components:** PatternKPIGrid PatternImportTrendChart PatternCoverageTrendChart PatternClusterPieChart PatternSimilarityScatter PatternAnalysisTable

---

## STEP 26 — Pattern Analysis Tab Refinement

**Date:** 2026-06-29

### Prompt

```text
Remove from Scan Chain Pattern Analysis tab: header action box Upload Export Generate AI buttons AI Recommendation Summary section Redundancy Heatmap Similarity Matrix. Keep 11 KPIs import/coverage trend charts cluster pie scatter chart pattern table.
```

**Files:** src/components/scan-chain/tabs/PatternAnalysisTab.tsx

**Components:** PatternAnalysisTab (simplified layout)

---

## STEP 27 — Failure Analysis KPI Dashboard

**Date:** 2026-06-29

### Prompt

```text
Scan Chain Failure Analysis tab enterprise KPI dashboard. 12 KPIs FA-FR-001 to FA-FR-012: Total Failures Critical Failures Warning Failures Recovered Failures Failure Rate Root Cause Count Repair Rate Mean Time to Repair Failure Density Failure Trend Score Failure Impact Score Failure Recovery Score. Charts: Failure Trend Failure Type Distribution Failure by Lot Failure Density. Table: Failure ID Pattern ID Chip Fail Type Root Cause Severity Status Repair Action Priority. Dark enterprise glass theme.
```

**Files:** src/components/scan-chain/tabs/FailureAnalysisTab.tsx; src/components/scan-chain/failure/FailureKPIGrid.tsx; src/components/scan-chain/failure/FailureTrendChart.tsx; src/components/scan-chain/failure/FailureTypeDistributionChart.tsx; src/components/scan-chain/failure/FailureByLotChart.tsx; src/components/scan-chain/failure/FailureAnalysisTable.tsx; src/types/scanChain.ts; src/lib/scanChainData.ts

**Components:** FailureKPIGrid FailureTrendChart FailureTypeDistributionChart FailureByLotChart FailureAnalysisTable

---

## STEP 28 — Failure Analysis Tab Refinement

**Date:** 2026-06-29

### Prompt

```text
Remove from Scan Chain Failure Analysis tab: header action box Upload Export Generate AI buttons AI Recommendation Summary Wafer Die heatmaps Correlation Matrix Root Cause Analysis section. Keep 12 KPIs failure trend charts distribution by-lot charts failure table.
```

**Files:** src/components/scan-chain/tabs/FailureAnalysisTab.tsx

**Components:** FailureAnalysisTab (simplified layout)

---

## STEP 29 — Recommendation Analysis AI Agent Center

**Date:** 2026-06-29

### Prompt

```text
Redesign Recommendation Analysis page as single AI Recommendation Center without module tabs Overview Scan Chain MBIST LBIST Wafer. Three agent sections on one page: Pattern Recommendation Agent Scan Debug Recommendation Agent Test Optimization Recommendation Agent. Each section KPIs charts tables AI summary workflow. Do not redesign sidebar or top nav.
```

**Files:** src/app/dashboard/recommendation-analysis/page.tsx; src/components/recommendation/RecommendationCenterContent.tsx; src/components/recommendation/CenterKPIGrid.tsx; src/components/recommendation/AgentSummaryCard.tsx; src/components/recommendation/AgentWorkflowDiagram.tsx; src/types/recommendation.ts; src/lib/recommendationData.ts

**Components:** RecommendationCenterContent CenterKPIGrid AgentSummaryCard AgentWorkflowDiagram

---

## STEP 30 — Recommendation Analysis AI Agent Tabs

**Date:** 2026-06-29

### Prompt

```text
Redesign Recommendation Analysis with 3 AI Agent tabs persisted in uiStore: Pattern Recommendation Agent Scan Debug Recommendation Agent Test Optimization Recommendation Agent. Animated tab switching Framer Motion. Remove old 5 module tabs. Route /dashboard/recommendation-analysis.
```

**Files:** src/components/recommendation/RecommendationCenterContent.tsx; src/components/recommendation/AgentTabs.tsx; src/components/recommendation/tabs/PatternAgentTab.tsx; src/components/recommendation/tabs/ScanDebugAgentTab.tsx; src/components/recommendation/tabs/TestOptAgentTab.tsx; src/stores/uiStore.ts; src/types/recommendation.ts

**Components:** AgentTabs PatternAgentTab ScanDebugAgentTab TestOptAgentTab RecommendationCenterContent

---

## STEP 31 — Scan Debug Recommendation Agent Tab

**Date:** 2026-06-29

### Prompt

```text
Scan Debug Recommendation Agent tab full enterprise dashboard. 15 KPIs in 5 sections ai-rec-kpi-grid 5 cols desktop: Debug Queue Open Issues Critical Debug Items Root Cause Identified Repair Success Rate Diagnosis Coverage Debug Cycle Time Pattern Failures Scan Chain Failures Suspected Cells Debug Priority Score AI Confidence Debug Cost Impact Expected Yield Gain. Charts: root cause donut priority bar 30-day trend. Table: Recommendation ID Category Priority Expected Impact Action Status. AI Debug Executive Summary 9 cards. Debug workflow diagram action bar.
```

**Files:** src/components/recommendation/tabs/ScanDebugAgentTab.tsx; src/components/recommendation/SectionedKPIGrid.tsx; src/components/recommendation/AgentTabHeader.tsx; src/components/recommendation/AgentActionBar.tsx; src/lib/recommendationData.ts (scanDebugAgent*); src/styles/globals.css (.ai-rec-kpi-grid)

**Components:** ScanDebugAgentTab SectionedKPIGrid AgentTabHeader AgentActionBar

---

## STEP 32 — Test Optimization Recommendation Agent Tab

**Date:** 2026-06-29

### Prompt

```text
Test Optimization Recommendation Agent tab full enterprise dashboard. 19 KPIs in 7 sections test-opt-kpi-grid 3 cols desktop: Total Recommendations Active Optimizations Cost Savings Potential Time Savings Potential Yield Improvement Potential Test Time Reduction Pattern Count Reduction Site Utilization Score Tester Efficiency Score ROI Score Optimization Confidence Priority Score Assigned Engineers Pending Actions Completed Actions Expected Cost Impact Expected Yield Gain Optimization Score. Charts: priority donut priority bar 30-day trend yield line cost area site utilization heatmap 16 sites. Table: Recommendation ID Category Priority Confidence Assigned Engineer Expected Impact Action Status. Executive AI Summary 8 cards. Optimization workflow action bar.
```

**Files:** src/components/recommendation/tabs/TestOptAgentTab.tsx; src/components/recommendation/SiteUtilizationHeatmap.tsx; src/lib/recommendationData.ts (testOptAgent*); src/styles/globals.css (.test-opt-kpi-grid)

**Components:** TestOptAgentTab SiteUtilizationHeatmap SectionedKPIGrid AgentTabHeader AgentActionBar

---

## STEP 33 — Record All Prompts (Session Update)

**Date:** 2026-06-29

### Prompt

```text
have upload all promt to csv and readme fie
```

**Files:** prompts.csv; README.md

**Components:** Prompt documentation archive (STEP 24-33)

---

## STEP 34 — Wafer Analysis Module (All Tabs)

**Date:** 2026-06-29

### Prompt

```text
Create premium enterprise Wafer Analysis module for ATE Intelligence Enterprise Platform. Route /dashboard/wafer-analysis redirect /wafer-analysis. Stack Next.js TypeScript Tailwind shadcn Recharts Framer Motion Zustand HTML5 Canvas. Theme dark enterprise #090B12 #111827 #2D3748 #7C3AED glass 20px. Keep sidebar top nav search upload export filters. Header Wafer Analysis subtitle AI-powered wafer defect classification yield analysis hotspot detection spatial intelligence. Primary action Generate Yield Analysis. 10 tabs TabPanelHost keep-alive: Overview Centre Donut Edge-Ring Scratch Near-Full Normal Edge-Loc Local Random. Overview: Input Die Statistics 5 KPIs Defect Classification 9 clickable KPIs Yield Analysis positive negative donut Gallery 9 cards Upload Workflow 8 steps Bottom Summary 7 KPIs. Defect tabs shared DefectClassTab: header 8 KPIs Upload History list Overlay Analytics canvas Fail Density canvas Info Panel workflow. Data waferData.ts wafer.ts buildWaferImages getDefectBundle defectClassMeta galleryCards. Components WaferTabs WaferNavigationContext KPICard DefectClassKPIGrid WaferGalleryGrid BottomSummaryBar UploadHistoryPanel WaferAnalysisViews WaferInfoPanel OverviewTab DefectClassTab. Match Scan Chain MBIST enterprise quality.
```

**Files:** src/app/dashboard/wafer-analysis/page.tsx; src/app/wafer-analysis/page.tsx; src/types/wafer.ts; src/lib/waferData.ts; src/components/wafer/WaferTabs.tsx; src/components/wafer/WaferNavigationContext.tsx; src/components/wafer/KPICard.tsx; src/components/wafer/DefectClassKPIGrid.tsx; src/components/wafer/WaferGalleryGrid.tsx; src/components/wafer/BottomSummaryBar.tsx; src/components/wafer/UploadHistoryPanel.tsx; src/components/wafer/WaferAnalysisViews.tsx; src/components/wafer/WaferInfoPanel.tsx; src/components/wafer/tabs/OverviewTab.tsx; src/components/wafer/tabs/DefectClassTab.tsx

**Components:** WaferTabs WaferNavigationProvider TabPanelHost OverviewTab DefectClassTab KPIGrid DefectClassKPIGrid WaferGalleryGrid BottomSummaryBar UploadHistoryPanel WaferAnalysisViews WaferInfoPanel

---

## STEP 35 — Wafer Analysis Images in Data

**Date:** 2026-06-29

### Prompt

```text
Update wafer data to include wafer images in waferData.ts not separate asset system. WaferImages interface wafer overlay density SVG data URIs via buildWaferImages buildWaferImageUri. Attach images to defectClassMeta galleryCards topDefectWafers allUploads analysisRows. Components use img src from data. Remove separate WaferDieMap canvas generator.
```

**Files:** src/types/wafer.ts; src/lib/waferData.ts; src/components/wafer/WaferGalleryGrid.tsx; src/components/wafer/UploadHistoryPanel.tsx; src/components/wafer/WaferAnalysisViews.tsx

**Components:** WaferImages buildWaferImages buildWaferImageUri

---

## STEP 36 — Wafer Analysis UI Refinement

**Date:** 2026-06-29

### Prompt

```text
Overview remove: Yield Trend Yield Distribution Defect Class Breakdown Recent Wafer Yield Top Defect Wafers table. Keep Input Die Statistics Defect Classification positive negative donut Gallery Workflow Summary. Defect tabs remove Class Probability Distribution AI Insights separate Recent History. Upload History single selectable list allUploads 10 items drives canvas maps. Overlay Analytics canvas teal good gold fail cyan cluster boxes. Fail Density canvas smooth heatmap blue cyan yellow purple crosshair X Y tooltip. Info panel updates from selected upload.
```

**Files:** src/components/wafer/tabs/OverviewTab.tsx; src/components/wafer/tabs/DefectClassTab.tsx; src/components/wafer/UploadHistoryPanel.tsx; src/components/wafer/WaferAnalysisViews.tsx; src/lib/waferData.ts; src/types/wafer.ts

**Components:** UploadHistoryPanel WaferAnalysisViews OverlayAnalyticsCanvas FailDensityCanvas

---

## STEP 37 — Wafer Analysis Records Removal

**Date:** 2026-06-29

### Prompt

```text
Remove Wafer Analysis Records table from all defect class tabs. Remove analysisRows from defect bundle and buildAnalysisRows from waferData.
```

**Files:** src/components/wafer/tabs/DefectClassTab.tsx; src/lib/waferData.ts; src/types/wafer.ts

**Components:** DefectClassTab (simplified)

---

## STEP 38 — Platform Tab Performance Optimization

**Date:** 2026-06-29

### Prompt

```text
Improve tab and section response time without UI visual changes. TabPanelHost lazy mount keep-alive hidden inactive tabs. Remove artificial setTimeout delays in usePlatformData. Executive dashboard useMemo not skeleton gate. React Query cache defaults refetchOnWindowFocus false staleTime 60s. Wafer heatmap pan functional setState. Apply TabPanelHost to scan-chain mbist lbist wafer-analysis cost-intelligence alerts recommendation-analysis.
```

**Files:** src/components/platform/TabPanelHost.tsx; src/hooks/usePlatformData.ts; src/app/dashboard/page.tsx; src/components/providers/QueryProvider.tsx; src/app/dashboard/scan-chain/page.tsx; src/app/dashboard/mbist/page.tsx; src/app/dashboard/lbist/page.tsx; src/app/dashboard/wafer-analysis/page.tsx; src/app/dashboard/cost-intelligence/page.tsx; src/app/dashboard/alerts/page.tsx; src/components/recommendation/RecommendationCenterContent.tsx; src/components/charts/WaferHeatmap.tsx

**Components:** TabPanelHost useFilteredExecutiveData QueryProvider

---

## STEP 39 — Record All Prompts (Full Platform Update)

**Date:** 2026-06-29

### Prompt

```text
Update all prompts to prompts.csv and README.md including Wafer Analysis module all tabs data images UI refinements performance optimization and current platform state.
```

**Files:** prompts.csv; README.md

**Components:** Prompt documentation archive (STEP 1-39)

---

## BACKEND — VERILUMEN Backend Implementation

**Date:** 2026-07-06

### Prompt

```text
VERILUMEN Backend Implementation Prompt FastAPI SQLAlchemy Postgres Redis MinIO ARQ. Phases 1-9 infra MinIO Redis auth uploads dashboard notifications. Separate verilumen-api repo. See README VERILUMEN Backend Implementation.
```

**Files:** (separate verilumen-api repo)

**Components:** FastAPI MinIO Redis ARQ routers workers

---

## DATABASE — VERILUMEN Database Schema

**Date:** 2026-07-06

### Prompt

```text
VERILUMEN Database Schema Alembic Phase 2 reconcile 39-table Postgres. Dims auth upload pipeline analytics recommendation_feedback indexes. See README VERILUMEN Database Schema.
```

**Files:** (separate verilumen-api repo) alembic/versions/*.py

**Components:** Alembic migrations SQLAlchemy models

---

## STEP 40 — Frontend API Client Foundation

**Date:** 2026-07-06

### Prompt

```text
STEP 40 Environment and typed API client. env.local.example NEXT_PUBLIC_API_URL NEXT_PUBLIC_API_MODE mock. src/lib/api client config auth dashboard uploads notifications. Thin fetch wrapper auth injection typed errors maps backend /api/v1. Default mock nothing breaks.
```

**Files:** env.local.example; src/lib/api/*.ts

**Components:** api client authApi dashboardApi uploadsApi notificationsApi

---

## STEP 41 — Frontend Auth

**Date:** 2026-07-06

### Prompt

```text
STEP 41 Auth. Extend userStore session tokens setSession clearSession. login page AuthGuard on dashboard layout. Replace hardcoded Alex Johnson uploadedBy with getSessionDisplayName. Live mode redirects to login.
```

**Files:** src/stores/userStore.ts; src/app/login/page.tsx; src/components/auth/AuthGuard.tsx; src/components/layout/DashboardLayout.tsx; src/components/upload/UploadDataModal.tsx; src/components/upload/UploadLogFileModal.tsx

**Components:** LoginPage AuthGuard session tokens

---

## STEP 42 — Frontend Module Data Hooks

**Date:** 2026-07-06

### Prompt

```text
STEP 42 Consolidate data access behind hooks. useFiltered Module Data per module recommendation alerts mbist lbist cost scan-chain wafer. Repoint 50 direct mock imports. useFilterStore returns kpis rows isLoading. Order: recommendation 10 alerts 8 mbist lbist 7 cost 7 scan-chain 6 wafer 4.
```

**Files:** (planned) src/hooks/use*ModuleData.ts

**Components:** useFilteredModuleData hooks

---

## STEP 43 — Frontend Live Dashboard Wiring

**Date:** 2026-07-06

### Prompt

```text
STEP 43 Live-wire dashboards. NEXT_PUBLIC_API_MODE live uses useQuery queryKey module tab filters queryFn dashboardApi. Flip flag per module as backend lands. Mock keeps useMemo path.
```

**Files:** (planned) src/hooks/usePlatformData.ts

**Components:** useQuery live dashboard

---

## STEP 44 — Frontend Filters and Search

**Date:** 2026-07-06

### Prompt

```text
STEP 44 Wire filters and search. Side effect of STEP 42 hooks reading useFilterStore. searchPlatform points at GET /search?q= when live keeping useGlobalSearch interface.
```

**Files:** (planned) src/lib/searchIndex.ts

**Components:** GlobalSearch live search

---

## STEP 45 — Frontend Real Upload Flow

**Date:** 2026-07-06

### Prompt

```text
STEP 45 Real upload flow. Replace simulateUpload with presign PUT MinIO complete SSE. Drop fileCache from uploadStore. dataHistory logHistory from GET /uploads/data /uploads/log useQuery.
```

**Files:** (planned) src/components/upload/*.tsx; src/stores/uploadStore.ts

**Components:** presigned upload SSE

---

## STEP 46 — Frontend Notifications API

**Date:** 2026-07-06

### Prompt

```text
STEP 46 Notifications. notificationStore seed replaced with useQuery GET /notifications useMutation markRead markAllRead Redis cached unread.
```

**Files:** (planned) src/stores/notificationStore.ts; src/components/platform/NotificationCenter.tsx

**Components:** notifications useQuery

---

## STEP 47 — Frontend Recommendation RL Feedback

**Date:** 2026-07-06

### Prompt

```text
STEP 47 Recommendation feedback RL signal. pattern-agent scan-debug-agent test-optimization-agent apply reject calls POST /recommendations/feedback tied to recommendation_feedback table.
```

**Files:** (planned) src/components/platform/RecommendationActionButtons.tsx

**Components:** recommendation feedback API

---

## STEP 48 — Frontend Export Report API

**Date:** 2026-07-06

### Prompt

```text
STEP 48 Export Report. Wire ExportMenu to GET /export/:format presigned MinIO URL browser redirect.
```

**Files:** (planned) src/components/platform/ExportMenu.tsx

**Components:** export presign URL

---

## STEP 49 — Scan Chain Failure Analysis KPI Trim

**Date:** 2026-07-06

### Prompt

```text
Remove Failure Correlations and Failure Reports KPI cards from Scan Chain Failure Analysis failureAnalysisKPIs.
```

**Files:** src/lib/scanChainData.ts

**Components:** FailureKPIGrid

---

## STEP 50 — Record Frontend Integration Prompts

**Date:** 2026-07-06

### Prompt

```text
Update prompts.csv and README with VERILUMEN BACKEND DATABASE prompts and frontend integration STEP 40-48 full documentation.
```

**Files:** prompts.csv; README.md

**Components:** Prompt archive STEP 40-50 BACKEND DATABASE

---

## STEP 51 — Enterprise KPI Card Design System

**Date:** 2026-07-07

### Prompt

```text
Refactor entire KPI card system into single EnterpriseKPICard component. 220px height 100% width 22px padding 18px radius #111827 bg purple border. Typography title 16px value 44px subtitle 14px trend 15px badge 12px. Grid xl 4 overview xl 3 section md 2 sm 1 gap 24px. Apply Dashboard Scan Chain Recommendation MBIST LBIST Wafer Cost Alerts Settings.
```

**Files:** src/components/common/EnterpriseKPICard.tsx; src/styles/globals.css; module KPICard wrappers

**Components:** EnterpriseKPICard EnterpriseKPIGrid

---

## STEP 52 — Complete Prompt Archive PDF

**Date:** 2026-07-07

### Prompt

```text
Generate all prompts in one document PDF from prompts.csv and session build prompts.
```

**Files:** docs/VERILUMEN-ALL-PROMPTS.md; docs/VERILUMEN-ALL-PROMPTS.pdf; scripts/generate-all-prompts-pdf.mjs

**Components:** VERILUMEN-ALL-PROMPTS.pdf

---

## STEP 53 — Executive KPI Card Production Ready

**Date:** 2026-07-07

### Prompt

```text
Cursor AI Prompt Enterprise KPI Card Production Ready for Scan Chain Overview. ExecutiveKPICard 220px #121826 gradient trend badge 48px value drill-down modal on click.
```

**Files:** src/components/common/ExecutiveKPICard.tsx; src/components/common/ExecutiveKPIDrillDownModal.tsx; src/components/scan-chain/overview/ExecutiveOverviewKPIGrid.tsx

**Components:** ExecutiveKPICard ExecutiveKPIDrillDownModal ExecutiveOverviewKPIGrid

---

## STEP 54 — Scan Chain Pattern Analysis Tab

**Date:** 2026-07-07

### Prompt

```text
Scan Chain Pattern Analysis production-ready prompt. 11 KPI cards EnterpriseKPIGrid. See docs/PROMPT-SCAN-CHAIN-PATTERN-ANALYSIS.md
```

**Files:** docs/PROMPT-SCAN-CHAIN-PATTERN-ANALYSIS.md; src/components/scan-chain/tabs/PatternAnalysisTab.tsx

**Components:** PatternAnalysisTab PatternKPIGrid

---

## STEP 55 — Frontend Presentation Guide

**Date:** 2026-07-07

### Prompt

```text
Complete frontend presentation documentation for stakeholder demos. Modules tabs KPIs design system architecture demo flow competitive positioning.
```

**Files:** docs/FRONTEND-PRESENTATION.md

**Components:** Frontend presentation guide

---

## STEP 56 — Enterprise KPI Drill-down Analytics Workspace

**Date:** 2026-07-08

### Prompt

```text
Cursor Prompt Enterprise KPI Drill-down Modal. Redesign KPI popup as complete 90vw x 90vh analytics workspace (Synopsys/Siemens/Advantest/Teradyne/KLA quality). NOT documentation modal. 10 rows: Executive Summary (6 cards + sparklines), Historical Trend (6 tabs), Engineering Analytics (dynamic API widgets), Breakdown Analysis (clickable), Root Cause AI Diagnosis, Recommendation Engine, Engineering Timeline, Raw Data Grid (column chooser CSV/Excel), Related Modules (navigate without close), AI Copilot. Footer: record count parser AI model backend DB latency. Semiconductor metadata strip. Loading skeleton error empty states. See docs/PROMPT-ENTERPRISE-KPI-DRILLDOWN-WORKSPACE.md for full spec.
```

**Files:** docs/PROMPT-ENTERPRISE-KPI-DRILLDOWN-WORKSPACE.md; src/types/kpiDrillDown.ts; src/lib/kpiDrillDown/*; src/hooks/useKpiDrillDownWorkspace.ts; src/components/common/kpi-drilldown/*; ExecutiveKPIDrillDownModal; ExecutiveOverviewKPIGrid

**Components:** KpiDrillDownWorkspace KpiWidgetRenderer KpiCopilotPanel

---

## STEP 57 — Executive KPI Typography Visibility

**Date:** 2026-07-08

### Prompt

```text
Fix Executive KPI card titles not visually clear on dark cards. White semibold titles, card layout restructure to prevent overflow clipping, 3-column grid for 7 overview KPIs, section header contrast improvements.
```

**Files:** ExecutiveKPICard.tsx; EnterpriseKPICard.tsx; OverviewDrillDownSection.tsx; globals.css; scanChainData.ts

**Components:** ExecutiveKPICard OverviewSectionHeader

---

## STEP 58 — Hydration Warning UI Primitives

**Date:** 2026-07-08

### Prompt

```text
Fix React hydration mismatch (fdprocessedid browser extension attributes) on Select Input DropdownMenuTrigger. Add suppressHydrationWarning matching Button pattern.
```

**Files:** src/components/ui/select.tsx; input.tsx; dropdown-menu.tsx

**Components:** SelectTrigger Input DropdownMenuTrigger

---

## STEP 59 — Record All Prompts Archive Update

**Date:** 2026-07-08

### Prompt

```text
Save all prompts STEPs 51-59 to prompts.csv, VERILUMEN-ALL-PROMPTS.md, and dedicated prompt documentation files.
```

**Files:** prompts.csv; docs/VERILUMEN-ALL-PROMPTS.md; docs/PROMPT-ENTERPRISE-KPI-DRILLDOWN-WORKSPACE.md

**Components:** Prompt archive STEPs 51-59

---

## STEP 60 — Pattern Analysis KPI Drill-down

**Date:** 2026-07-08

### Prompt

```text
Make the KPI drill-down for the Pattern Analysis tab — wire all 11 pattern KPI cards to the enterprise analytics workspace with unique widget profiles per KPI.
```

**Files:** src/lib/kpiDrillDown/kpiProfiles.ts; buildKpiWorkspace.ts; kpiDrillDownUtils.ts; src/components/common/kpi-drilldown/KpiDrillDownGrid.tsx; KpiDrillDownModal.tsx; src/components/scan-chain/pattern/PatternKPIGrid.tsx

**Components:** KpiDrillDownGrid PatternKPIGrid pattern KPI profiles

---

## STEP 61 — Failure Analysis KPI Drill-down

**Date:** 2026-07-08

### Prompt

```text
Cursor Prompt Failure Analysis KPI Drill-down — redesign Failure Analysis KPI popup as 95vw x 92vh enterprise engineering workspace. 10 rows: Executive Summary (8 cards incl yield/cost), Trend Analytics, Engineering Analytics (9 unique KPI dashboards), Breakdown (tester/lot/wafer/module/die/pattern/scan chain/failure bin/root cause), AI Root Cause, Recommendations, Event Timeline, Raw Data Table, Related Modules, AI Copilot. No documentation blocks. See docs/PROMPT-FAILURE-ANALYSIS-KPI-DRILLDOWN.md
```

**Files:** docs/PROMPT-FAILURE-ANALYSIS-KPI-DRILLDOWN.md; src/types/kpiDrillDown.ts; src/lib/kpiDrillDown/kpiProfiles.ts; buildKpiWorkspace.ts; kpiDrillDownUtils.ts; src/components/scan-chain/failure/FailureKPIGrid.tsx; src/components/common/kpi-drilldown/KpiDrillDownWorkspace.tsx; KpiCopilotPanel.tsx; KpiWorkspaceSections.tsx

**Components:** FailureKPIGrid failure KPI profiles FAILURE_BREAKDOWN_DIMENSIONS failure layout preset

---

## STEP 62 — Record All Prompts Archive Update

**Date:** 2026-07-08

### Prompt

```text
Save all prompts — record STEPs 60-62 (Pattern Analysis drill-down, Failure Analysis drill-down, archive update) in prompts.csv and VERILUMEN-ALL-PROMPTS.md.
```

**Files:** prompts.csv; docs/VERILUMEN-ALL-PROMPTS.md; docs/PROMPT-FAILURE-ANALYSIS-KPI-DRILLDOWN.md

**Components:** Prompt archive STEPs 60-62

---

## STEP 63 — Scan Diagnosis KPI Drill-down

**Date:** 2026-07-08

### Prompt

```text
Cursor Prompt Scan Diagnosis KPI Drill-down — 95vw x 92vh topology-first enterprise diagnosis workspace for 12 Scan Diagnosis KPIs. Failure traceability path, interactive chain topology graph, scan-specific root cause fields, engineering data grid, diagnosis copilot. See docs/PROMPT-SCAN-DIAGNOSIS-KPI-DRILLDOWN.md
```

**Files:** docs/PROMPT-SCAN-DIAGNOSIS-KPI-DRILLDOWN.md; src/types/kpiDrillDown.ts; src/lib/kpiDrillDown/kpiProfiles.ts; buildKpiWorkspace.ts; kpiDrillDownUtils.ts; src/components/common/kpi-drilldown/KpiTraceabilityPath.tsx; KpiTopologyPanel.tsx; ScanDiagnosisSectionedGrid.tsx

**Components:** Scan Diagnosis drill-down topology-first workspace 12 KPI profiles

---

## STEP 64 — Record All Prompts Archive Update

**Date:** 2026-07-08

### Prompt

```text
Save all prompts — record STEPs 63-64 to prompts.csv and VERILUMEN-ALL-PROMPTS.md.
```

**Files:** prompts.csv; docs/VERILUMEN-ALL-PROMPTS.md; docs/PROMPT-SCAN-DIAGNOSIS-KPI-DRILLDOWN.md

**Components:** Prompt archive STEPs 63-64

---

## STEP 65 — Pattern Recommendation Agent KPI Drill-down

**Date:** 2026-07-08

### Prompt

```text
Cursor Prompt Pattern Recommendation Agent KPI Drill-down — 95vw x 92vh AI Pattern Optimization Decision Workspace for 10 Pattern Agent KPIs. Before vs After comparison, AI decision overview, pattern analytics, approval center, simulation, engineering timeline, raw data grid, AI copilot. Config-driven kpiProfiles per KPI. See docs/PROMPT-PATTERN-RECOMMENDATION-AGENT-KPI-DRILLDOWN.md
```

**Files:** docs/PROMPT-PATTERN-RECOMMENDATION-AGENT-KPI-DRILLDOWN.md; src/types/kpiDrillDown.ts; src/lib/kpiDrillDown/kpiProfiles.ts; buildKpiWorkspace.ts; kpiDrillDownUtils.ts; src/components/common/kpi-drilldown/KpiRecommendationPanels.tsx; KpiDrillDownWorkspace.tsx; CenterKPIGrid.tsx

**Components:** Pattern Recommendation Agent optimization workspace 10 KPI profiles approval workflow simulation panels

---

## STEP 66 — Record All Prompts Archive Update

**Date:** 2026-07-08

### Prompt

```text
Save all prompts — record STEPs 65-66 to prompts.csv and VERILUMEN-ALL-PROMPTS.md.
```

**Files:** prompts.csv; docs/VERILUMEN-ALL-PROMPTS.md; docs/PROMPT-PATTERN-RECOMMENDATION-AGENT-KPI-DRILLDOWN.md

**Components:** Prompt archive STEPs 65-66

---

## STEP 67 — Test Optimization Recommendation Agent KPI Drill-down

**Date:** 2026-07-08

### Prompt

```text
Cursor Prompt Test Optimization Recommendation Agent KPI Drill-down — 95vw x 92vh AI Test Optimization Decision Center for 19 Test Opt KPIs. Business-focused yield cost test time risk ROI. Simulation hero centerpiece current vs optimized. Optimization overview business impact action center. Config-driven kpiProfiles. See docs/PROMPT-TEST-OPTIMIZATION-AGENT-KPI-DRILLDOWN.md
```

**Files:** docs/PROMPT-TEST-OPTIMIZATION-AGENT-KPI-DRILLDOWN.md; src/types/kpiDrillDown.ts; src/lib/kpiDrillDown/kpiProfiles.ts; buildKpiWorkspace.ts; kpiDrillDownUtils.ts; KpiRecommendationPanels.tsx; KpiDrillDownWorkspace.tsx

**Components:** Test Optimization Agent decision center 19 KPI profiles simulation hero business impact

---

## STEP 68 — Record All Prompts Archive Update

**Date:** 2026-07-08

### Prompt

```text
Save all prompts — record STEPs 67-68 to prompts.csv and VERILUMEN-ALL-PROMPTS.md.
```

**Files:** prompts.csv; docs/VERILUMEN-ALL-PROMPTS.md; docs/PROMPT-TEST-OPTIMIZATION-AGENT-KPI-DRILLDOWN.md

**Components:** Prompt archive STEPs 67-68

---

## STEP 69 — Scan Debug Recommendation Agent KPI Drill-down

**Date:** 2026-07-08

### Prompt

```text
Cursor Prompt Scan Debug Recommendation Agent KPI Drill-down — 95vw x 92vh AI-assisted Scan Debug Decision Console for 15 Scan Debug KPIs. Split-view 40/60 AI decision panel + engineering visualization. Topology wafer map heatmap per KPI. Config-driven kpiProfiles. See docs/PROMPT-SCAN-DEBUG-AGENT-KPI-DRILLDOWN.md
```

**Files:** docs/PROMPT-SCAN-DEBUG-AGENT-KPI-DRILLDOWN.md; src/types/kpiDrillDown.ts; src/lib/kpiDrillDown/kpiProfiles.ts; buildKpiWorkspace.ts; kpiDrillDownUtils.ts; KpiScanDebugDecisionPanel.tsx; KpiDrillDownWorkspace.tsx

**Components:** Scan Debug Agent decision console 15 KPI profiles split-view debug layout

---

## STEP 70 — Record All Prompts Archive Update

**Date:** 2026-07-08

### Prompt

```text
Save all prompts — record STEPs 69-70 to prompts.csv and VERILUMEN-ALL-PROMPTS.md.
```

**Files:** prompts.csv; docs/VERILUMEN-ALL-PROMPTS.md; docs/PROMPT-SCAN-DEBUG-AGENT-KPI-DRILLDOWN.md

**Components:** Prompt archive STEPs 69-70

---

## STEP 71 — KPI Drill-down FastAPI Integration

**Date:** 2026-07-08

### Prompt

```text
Make the KPI drill-down UI/UX consume the FastAPI backend instead of only the local mock builder. Backend: GET /api/v1/kpi/{kpi_id}/workspace with GlobalFilters query params + Redis cache (60s TTL); kpi_workspace_service builds a payload mirroring the frontend KpiWorkspaceApiResponse shape with module routing (pattern / testOptimization / scanDebug / diagnosis / failure), enriched from KpiSnapshot when available. Frontend: src/lib/api/kpi.ts getKpiWorkspace(kpiId, filters); useKpiDrillDownWorkspace uses React Query when NEXT_PUBLIC_API_MODE=live and falls back to buildKpiWorkspace() in mock mode; footer shows FastAPI vs Mock data source.
```

**Files:** backend/app/routers/kpi.py; backend/app/services/kpi_workspace_service.py; backend/app/data/kpi_profiles.py; backend/app/main.py; backend/tests/test_kpi_workspace.py; src/lib/api/kpi.ts; src/hooks/useKpiDrillDownWorkspace.ts; src/lib/api/index.ts; src/components/common/kpi-drilldown/KpiDrillDownModal.tsx; KpiDrillDownWorkspace.tsx

**Components:** FastAPI kpi workspace endpoint, getKpiWorkspace client, React Query live/mock hook, data-source footer indicator

---

# Part B — Session Prompts (Build + KPI)

## Session 1 — Unified Build Sequence STEP 40–53

**Date:** 2026-07-03

### Prompt

```text
VERILUMEN Unified Build Sequence — merge backend + frontend prompts with dependency order. Add search, AI Diagnose, AI Optimize, recommendation feedback endpoints. Continue STEP numbering from STEP 39.
```

---

## Session 2 — Backend & Database Implementation

**Date:** 2026-07-06

### Prompt

```text
VERILUMEN Backend & Database Implementation Prompt — FastAPI + SQLAlchemy + Postgres/Redis/MinIO. Phases for infra, schema, auth, uploads, dashboard APIs, workers, notifications.
```

---

## Session 3 — Frontend Integration STEP 40+

**Date:** 2026-07-06

### Prompt

```text
VERILUMEN Dashboard Frontend Integration Prompt — API client, auth, module hooks, live dashboard wiring, filters, uploads, notifications, recommendation feedback, export.
```

---

## Session 4 — 20 Prompts to Finish Build

**Date:** 2026-07-06

### Prompt

```text
VERILUMEN 20 Prompts to Finish the Build — gap-analysis driven prompts for parser, live analytics, alert UI, RL consumer, STIL/WGL/PAT parsers, cost engine, deep analytics.
```

---

## Session 5 — P1-7 Enterprise File Parser

**Date:** 2026-07-06

### Prompt

```text
P1-7 Enterprise File Parser — real STDF + LOG parsing in parse_worker.py. Do not rewrite project. Extend existing workers and models.
```

---

## Session 6 — Stage 7 Live Analytics

**Date:** 2026-07-06

### Prompt

```text
Stage 7 Live Analytics & Visualization Engine — replace mock chart generators with PostgreSQL-driven analytics across all modules.
```

---

## Session 7 — Scan Debug KPI List

**Date:** 2026-07-07

### Prompt

```text
List KPI cards for Recommendation Analysis → Scan Debug Recommendation Agent: Broken Chains Detected, Constraint Violations, Timing Debug, Power Debug, Defect Suspects, Investigation Recommendations, etc. (15 KPIs total).
```

---

## Session 8 — Scan Chain Overview Redesign

**Date:** 2026-07-07

### Prompt

```text
Scan Chain Overview tab should be executive summary with drill-down links — not duplicate Pattern/Failure/Diagnosis sub-tabs. KPIs + health summary + trend analytics + mini KPI drill-down sections.
```

---

## Session 9 — Remove AI Detection Accuracy KPI

**Date:** 2026-07-07

### Prompt

```text
Remove AI Detection Accuracy KPI card from Scan Chain Failure Analysis.
```

---

## Session 10 — KPI Same Size Audit

**Date:** 2026-07-07

### Prompt

```text
Check all KPI cards are same size across complete application. Standardize all KPI cards to enterprise design system.
```

---

## Session 11 — Enterprise KPI Card Refactor

**Date:** 2026-07-07

### Prompt

```text
Refactor entire KPI card system into single reusable EnterpriseKPICard component.
Apply across: Scan Chain, Pattern Recommendation, Scan Debug, Test Optimization, MBIST, LBIST, Wafer, Cost Intelligence, Dashboard, Alerts.
Card: 220px height, 100% width, 22px padding, 18px radius, #111827 bg, rgba(124,58,237,.25) border.
Grid: xl 4 cols overview, xl 3 cols section, md 2 cols, sm 1 col, 24px gap.
Identical typography, icon 48x48, badge, trend, sparkline 44px bottom. Truncate overflow. w-full h-full.
```

---

## Session 12 — KPI Typography Standardization

**Date:** 2026-07-07

### Prompt

```text
Standardize all KPI cards typography:
Title: 16px Medium #94A3B8 | Value: 44px Bold #FFFFFF line-height 48px | Subtitle: 14px Regular #64748B
Trend: 15px SemiBold green #10B981 / red #EF4444 | Badge: 12px SemiBold height 26px padding 6px 12px rounded-full
Layout: Icon 48x48 top-left, badge top-right, title, value, subtitle or trend, sparkline 44px bottom.
Apply to Dashboard, Scan Chain, MBIST, LBIST, Wafer, Cost Intelligence, Recommendation, Alerts, Settings.
```

---

## Session 13 — KPI Text Consistency Fix

**Date:** 2026-07-07

### Prompt

```text
Check complete application — KPI card text was not same in all KPI cards. Fix inconsistent value sizes and meta line styling.
```

---

## Session 14 — Fill Gaps and Save

**Date:** 2026-07-07

### Prompt

```text
Check all prompts, fill gaps, save what was made — sync bd-1, commit KPI standardization work.
```

---

## Session 15 — Enterprise KPI Drill-down Analytics Workspace

**Date:** 2026-07-08

### Prompt

```text
Cursor Prompt Enterprise KPI Drill-down Modal — complete 90vw x 90vh engineering analytics workspace with 10 interactive rows, dynamic API widgets, AI copilot, no documentation blocks. Full spec: docs/PROMPT-ENTERPRISE-KPI-DRILLDOWN-WORKSPACE.md
```

---

## Session 16 — Executive KPI Typography Visibility

**Date:** 2026-07-08

### Prompt

```text
KPI card titles not visually clear on Scan Chain Overview — fix contrast, layout clipping, and section header readability.
```

---

## Session 17 — Save All Prompts

**Date:** 2026-07-08

### Prompt

```text
Save the prompt — record all prompts STEPs 51-59 in csv and VERILUMEN-ALL-PROMPTS.md archive.
```

---

## Session 18 — Pattern Analysis KPI Drill-down

**Date:** 2026-07-08

### Prompt

```text
Make the KPI drill-down for the Pattern Analysis tab — 11 clickable KPI cards opening unique engineering analytics workspaces.
```

---

## Session 19 — Failure Analysis KPI Drill-down

**Date:** 2026-07-08

### Prompt

```text
Cursor Prompt Failure Analysis KPI Drill-down — 95vw x 92vh enterprise workspace with 9 unique failure KPI dashboards, failure-specific breakdown dimensions, yield/cost impact, failure timeline, and AI copilot. Full spec: docs/PROMPT-FAILURE-ANALYSIS-KPI-DRILLDOWN.md
```

---

## Session 20 — Save All Prompts

**Date:** 2026-07-08

### Prompt

```text
Save all prompt — archive STEPs 60-62 to prompts.csv and VERILUMEN-ALL-PROMPTS.md.
```

---

## Session 21 — Scan Diagnosis KPI Drill-down

**Date:** 2026-07-08

### Prompt

```text
Cursor Prompt Scan Diagnosis KPI Drill-down — topology-first 95vw x 92vh diagnosis console for 12 KPIs with failure traceability, chain topology graph, and scan engineering data grid. Full spec: docs/PROMPT-SCAN-DIAGNOSIS-KPI-DRILLDOWN.md
```

---

## Session 22 — Save All Prompts

**Date:** 2026-07-08

### Prompt

```text
Save all prompts — archive STEPs 63-64 to prompts.csv and VERILUMEN-ALL-PROMPTS.md.
```

---

## Session 23 — Pattern Recommendation Agent KPI Drill-down

**Date:** 2026-07-08

### Prompt

```text
For the Pattern Recommendation Agent, redesign every KPI drill-down as an AI Pattern Optimization Decision Workspace. 95vw x 92vh dark enterprise UI. Before vs After comparison. AI decision overview, pattern analytics, approval center, simulation, timeline, raw data, copilot. 10 unique KPI workspaces via config-driven kpiProfiles. Architecture: single reusable drill-down framework with per-KPI widget layout, AI template, action buttons, grid schema.
```

---

## Session 24 — Save All Prompts

**Date:** 2026-07-08

### Prompt

```text
Save all prompts — archive STEPs 65-66 to prompts.csv and VERILUMEN-ALL-PROMPTS.md.
```

---

## Session 25 — Test Optimization Recommendation Agent KPI Drill-down

**Date:** 2026-07-08

### Prompt

```text
For the Test Optimization Recommendation Agent, redesign every KPI drill-down as an AI Test Optimization Decision Center focused on business optimization (yield, cost, test time, risk, production efficiency). 95vw x 92vh. Simulation hero panel as centerpiece comparing current vs optimized state. 19 unique KPI workspaces via config-driven kpiProfiles.
```

---

## Session 26 — Save All Prompts

**Date:** 2026-07-08

### Prompt

```text
Save all prompts — archive STEPs 67-68 to prompts.csv and VERILUMEN-ALL-PROMPTS.md.
```

---

## Session 27 — Scan Debug Recommendation Agent KPI Drill-down

**Date:** 2026-07-08

### Prompt

```text
For the Scan Debug Recommendation Agent, redesign every KPI drill-down as an AI-assisted Scan Debug Decision Console. 95vw x 92vh. Split-view 40/60 layout: left AI explanation confidence approval, right interactive engineering visualization. 15 unique KPI workspaces via config-driven kpiProfiles.
```

---

## Session 28 — Save All Prompts

**Date:** 2026-07-08

### Prompt

```text
Save all prompts — archive STEPs 69-70 to prompts.csv and VERILUMEN-ALL-PROMPTS.md.
```

---

## Session 29 — Push Dashboard to GitHub

**Date:** 2026-07-10

### Prompt

```text
Push COMPTY Dashboard code to https://github.com/Verilumen-Labss/dashboard.git. Fix stuck git rebase; restore local main; force-push to Verilumen-Labss/dashboard.
```

---

## Session 30 — Build Fix apiRequest

**Date:** 2026-07-10

### Prompt

```text
Build Error: Export apiRequest doesn't exist in target module (src/lib/api/kpi.ts). Use apiFetch. Fix related TypeScript build errors.
```

---

## Session 31 — Hydration Mismatch fdprocessedid

**Date:** 2026-07-10

### Prompt

```text
Hydration mismatch on Scan Chain Overview buttons — fdprocessedid attribute injected by browser extension. Fix without changing other KPI drill-downs.
```

---

## Session 32 — Overall Scan Health KPI Drill-down

**Date:** 2026-07-10

### Prompt

```text
PROMPT: Overall Scan Health KPI Drill-Down Card — dedicated component/file only for overall-health. Three sections Executive Summary Health Score Breakdown Healthy vs Failing Chains. Props-driven no generic popup. See docs/PROMPT-OVERALL-SCAN-HEALTH-KPI-DRILLDOWN.md.
```

**Files:** `OverallScanHealthDrillCard.tsx`; `OverallScanHealthDrillDownModal.tsx`; `overallScanHealthDrillData.ts`; `ExecutiveOverviewKPIGrid.tsx`

---

## Session 33 — Save All Prompts

**Date:** 2026-07-10

### Prompt

```text
need to save all prompt for this all — archive STEPs 72-76 to prompts.csv, VERILUMEN-ALL-PROMPTS.md, PROMPT-SESSION-2026-07-10.md, ALL_PROMPTS.md.
```

---

# Part C — Final KPI Design System (Implemented)

| Item | Specification |
|---|---|
| Component | `EnterpriseKPICard.tsx` + `EnterpriseKPIGrid` |
| Card height | 220px |
| Padding / radius | 22px / 18px |
| Background / border | `#111827` / `rgba(124,58,237,0.25)` |
| Title | 16px Semibold `#FFFFFF` (Executive) / `#E2E8F0` (Enterprise) |
| Value | 44px Bold `#FFFFFF`, line-height 48px |
| Subtitle | 14px Regular `#64748B` |
| Trend | 15px SemiBold `#10B981` / `#EF4444` |
| Badge | 12px SemiBold, 26px height, 6×12px padding |
| Icon | 48×48 top-left |
| Sparkline | 44px bottom |
| Grid overview | 4 cols @ xl, 2 @ md, 1 @ sm |
| Grid section | 3 cols @ xl, 2 @ md, 1 @ sm |
| Gap | 24px |

**Git commits:** c1-com `bdc03e3` · bd-1/dashboard `56c8fff`

---

# Part D — Session 2026-07-10 Continuation (STEP 77–84)

| STEP | Title | Status |
|------|-------|--------|
| 77 | Total Scan Chains KPI Drill-down | ✅ |
| 78 | Healthy Chains KPI Drill-down | ✅ |
| 79 | Failing Chains KPI Drill-down | ✅ |
| 80 | Scan Coverage KPI Drill Card | ✅ |
| 81 | Average Diagnosis Confidence KPI Drill Card | ✅ |
| 82 | Average Test Time KPI Drill Card | ✅ |
| 83 | Scan Coverage KPI Modal Popup | ✅ |
| 84 | Record All Prompts Session Archive Continuation | ✅ |
| 85 | COMPTY Production Cleanup Verification Audit | ✅ |
| 86 | Production Cleanup README and Save All Prompts | ✅ |

**Session log:** `docs/PROMPT-SESSION-2026-07-10.md` (Sessions 34–43)

**Production audit:** `docs/PRODUCTION-CLEANUP-AUDIT.md` — readiness **56/100**
