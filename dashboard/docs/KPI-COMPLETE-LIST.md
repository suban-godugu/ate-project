# COMPTY / VERILUMEN — Complete KPI List

**Scope:** Dashboard · Scan Chain Analysis · Wafer Analysis · Recommendation Analysis  
**Date:** 2026-07-14  
**Related:** [`UI-MODULE-DOCUMENTATION.md`](./UI-MODULE-DOCUMENTATION.md)

---

## Summary counts

| Module / Tab | KPI count |
|--------------|----------:|
| Dashboard | 6 |
| Scan Chain · Overview (executive) | 7 |
| Scan Chain · Overview · Pattern Summary | 6 |
| Scan Chain · Overview · Failure Summary | 6 |
| Scan Chain · Overview · Diagnosis Summary | 6 |
| Scan Chain · Pattern Analysis | 11 |
| Scan Chain · Failure Analysis | 9 |
| Scan Chain · Scan Diagnosis | 12 |
| Wafer · Overview · Input & Die Stats | 5 |
| Wafer · Overview · Defect Classification | 9 |
| Wafer · Overview · Bottom Summary | 7 |
| Wafer · Each Defect Tab (×9) | 8 each = 72 |
| Recommendation · Pattern Agent | 10 |
| Recommendation · Scan Debug Agent | 15 |
| Recommendation · Test Optimization Agent | 19 |
| **Unique display KPIs (excluding ×9 defect duplicates)** | **~128** |
| **Total KPI card instances on UI** | **~200** |

---

# 1. Dashboard — Executive KPIs (6)

| # | ID | Title | Example value |
|---|----|-------|---------------|
| 1 | `total-test-cost` | Total Test Cost | $2.4M |
| 2 | `cost-per-wafer` | Cost per Wafer | $184 |
| 3 | `cost-per-die` | Cost per Die | $0.018 |
| 4 | `test-time` | Test Time | 42.6s |
| 5 | `yield` | Yield | 94.2% |
| 6 | `roi-improvement` | ROI Improvement | +18.4% |

---

# 2. Scan Chain Analysis

## 2.1 Overview — Executive KPIs (7)

| # | ID | Title | Example value |
|---|----|-------|---------------|
| 1 | `overall-health` | Overall Scan Health | 77.9% |
| 2 | `total-chains` | Total Scan Chains | 2,933 |
| 3 | `healthy-chains` | Healthy Chains | 2,284 |
| 4 | `failing-chains` | Failing Chains | 142 |
| 5 | `scan-coverage` | Scan Coverage | 96.8% |
| 6 | `avg-diagnosis-confidence` | Average Diagnosis Confidence | 91% |
| 7 | `avg-test-time` | Average Test Time | 18.4s |

## 2.2 Overview — Pattern Analysis Summary (6)

| # | ID | Title | Example value |
|---|----|-------|---------------|
| 1 | `files-ingested` | Pattern Files Ingested | 2,846 |
| 2 | `pattern-coverage-kpi` | Pattern Coverage | 98.42% |
| 3 | `pattern-clusters` | Pattern Clusters | 126 |
| 4 | `redundant-patterns` | Redundant Patterns | 38 |
| 5 | `metadata-extracted` | Metadata Extracted | 2,846 |
| 6 | `embeddings-generated` | Embeddings Generated | 2,846 |

## 2.3 Overview — Failure Analysis Summary (6)

| # | ID | Title | Example value |
|---|----|-------|---------------|
| 1 | `overall-failure-rate` | Overall Failure Rate | 2.84% |
| 2 | `failing-patterns` | Failing Test Patterns | 1,246 |
| 3 | `root-cause-confidence` | Root Cause Confidence | 94% |
| 4 | `recurring-failures` | Recurring Failures | 183 |
| 5 | `lot-failure-rate` | Lot Failure Rate | 3.11% |
| 6 | `wafer-failure-rate` | Wafer Failure Rate | 2.43% |

## 2.4 Overview — Scan Diagnosis Summary (6)

| # | ID | Title | Example value |
|---|----|-------|---------------|
| 1 | `sd-failing-chains` | Failing Scan Chains | 14 |
| 2 | `sd-failing-cells` | Failing Scan Cells | 73 |
| 3 | `sd-chain-breaks` | Chain Breaks Detected | 9 |
| 4 | `sd-avg-confidence` | Average Diagnosis Confidence | 91% |
| 5 | `sd-diagnosis-reports` | Diagnosis Reports | 4 |
| 6 | `sd-pending-review` | Diagnoses Pending Review | 6 |

## 2.5 Overview — Alerts Preview counts (3)

| # | Title | Example value |
|---|-------|---------------|
| 1 | Critical Alerts | 1 |
| 2 | High Alerts | 2 |
| 3 | Warning Alerts | 1 |

---

## 2.6 Pattern Analysis Tab — KPIs (11)

| # | ID | Title | Example value |
|---|----|-------|---------------|
| 1 | `files-ingested` | Pattern Files Ingested | 2,846 |
| 2 | `vectors-parsed` | Scan Vectors Parsed | 99.7% |
| 3 | `file-integrity` | File Integrity | 100% |
| 4 | `pattern-coverage-kpi` | Pattern Coverage | 98.42% |
| 5 | `metadata-extracted` | Metadata Extracted | 2,846 |
| 6 | `embeddings-generated` | Embeddings Generated | 2,846 |
| 7 | `pattern-clusters` | Pattern Clusters | 126 |
| 8 | `redundant-patterns` | Redundant Patterns | 38 |
| 9 | `similarity-analyses` | Similarity Analyses | 2,846 |
| 10 | `pass-fail-linked` | Pass / Fail Linked | 2,741 / 2,846 |
| 11 | `quality-reports` | Quality Reports | 24 |

---

## 2.7 Failure Analysis Tab — KPIs (9)

| # | ID | Title | Example value |
|---|----|-------|---------------|
| 1 | `imported-files` | Imported Test Files | 248 |
| 2 | `overall-failure-rate` | Overall Failure Rate | 2.84% |
| 3 | `failing-patterns` | Failing Test Patterns | 1,246 |
| 4 | `die-failure-rate` | Die Failure Rate | 1.92% |
| 5 | `wafer-failure-rate` | Wafer Failure Rate | 2.43% |
| 6 | `lot-failure-rate` | Lot Failure Rate | 3.11% |
| 7 | `fault-categories` | Fault Categories | 5 |
| 8 | `root-cause-confidence` | Root Cause Confidence | 94% |
| 9 | `recurring-failures` | Recurring Failures | 183 |

---

## 2.8 Scan Diagnosis Tab — KPIs (12)

### Detection & Identification

| # | ID | Title | Example value |
|---|----|-------|---------------|
| 1 | `sd-failing-chains` | Failing Scan Chains | 14 |
| 2 | `sd-failing-cells` | Failing Scan Cells | 73 |
| 3 | `sd-chain-breaks` | Chain Breaks Detected | 9 |
| 4 | `sd-shift-capture` | Shift / Capture Issues | 21 |

### Topology & Ranking

| # | ID | Title | Example value |
|---|----|-------|---------------|
| 5 | `sd-topology-chains` | Chains in Topology | 128 |
| 6 | `sd-chains-ranked` | Chains Ranked | 14 |
| 7 | `sd-failure-correlations` | Failure Correlations | 61 |
| 8 | `sd-top-failing-chain` | Top Failing Chain | SC_14 |

### Diagnosis & Reporting

| # | ID | Title | Example value |
|---|----|-------|---------------|
| 9 | `sd-diagnosis-reports` | Diagnosis Reports | 4 |
| 10 | `sd-debug-locations` | Debug Locations | 31 |
| 11 | `sd-avg-confidence` | Average Diagnosis Confidence | 91% |
| 12 | `sd-pending-review` | Diagnoses Pending Review | 6 |

---

# 3. Wafer Analysis

## 3.1 Overview — Input & Die Statistics (5)

| # | Title | Example value |
|---|-------|---------------|
| 1 | Number of Wafers | 1,248 |
| 2 | Number of Dies | 992,640 |
| 3 | Good Dies | 931,284 |
| 4 | Bad Dies | 61,356 |
| 5 | Defect Clusters | 342 |

## 3.2 Overview — Defect Classification cards (9)

| # | Title | Primary | Wafers | Confidence |
|---|-------|---------|--------|------------|
| 1 | Centre | 88% | 42 | 78% |
| 2 | Donut | 89.4% | 38 | 80% |
| 3 | Edge-Ring | 90.8% | 56 | 82% |
| 4 | Scratch | 92.2% | 24 | 84% |
| 5 | Near-Full | 93.6% | 12 | 86% |
| 6 | Normal | 88% | 312 | 88% |
| 7 | Edge-Loc | 89.4% | 48 | 90% |
| 8 | Local | 90.8% | 36 | 78% |
| 9 | Random | 92.2% | 280 | 80% |

## 3.3 Overview — Bottom Summary (7)

| # | Title | Example value |
|---|-------|---------------|
| 1 | Total Wafers | 1,248 |
| 2 | Total Dies | 992,640 |
| 3 | Good Dies | 931,284 |
| 4 | Bad Dies | 61,356 |
| 5 | Average Yield | 93.8% |
| 6 | Estimated Savings | $284K |
| 7 | AI Confidence | 91.4% |

## 3.4 Defect Tabs — Shared KPI titles (8 per tab × 9 tabs)

Same 8 titles on every defect tab (Centre, Donut, Edge-Ring, Scratch, Near-Full, Normal, Edge-Loc, Local, Random):

| # | Title |
|---|-------|
| 1 | Total Wafers |
| 2 | Good Dies |
| 3 | Bad Dies |
| 4 | Average Yield |
| 5 | Average Confidence |
| 6 | Total Dies |
| 7 | Defect Severity |
| 8 | Estimated Yield Loss |

### Values by defect tab

| Title | Centre | Donut | Edge-Ring | Scratch | Near-Full | Normal | Edge-Loc | Local | Random |
|-------|--------|-------|-----------|---------|-----------|--------|----------|-------|--------|
| Total Wafers | 42 | 38 | 56 | 24 | 12 | 312 | 48 | 36 | 280 |
| Good Dies | 748 | 744 | 740 | 736 | 732 | 728 | 724 | 720 | 716 |
| Bad Dies | 48 | 54 | 60 | 66 | 72 | 78 | 84 | 90 | 96 |
| Average Yield | 88% | 89.4% | 90.8% | 92.2% | 93.6% | 88% | 89.4% | 90.8% | 92.2% |
| Average Confidence | 78% | 80% | 82% | 84% | 86% | 88% | 90% | 78% | 80% |
| Total Dies | 796 | 796 | 796 | 796 | 796 | 796 | 796 | 796 | 796 |
| Defect Severity | High | High | High | Medium | Medium | Medium | Low | Low | Low |
| Estimated Yield Loss | 12.0% | 10.6% | 9.2% | 7.8% | 6.4% | 12.0% | 10.6% | 9.2% | 7.8% |

---

# 4. Recommendation Analysis

## 4.1 Pattern Recommendation Agent (10)

| # | Title | Example value |
|---|-------|---------------|
| 1 | Redundant Patterns | 34 / 342 |
| 2 | Removal Recommended | 28 |
| 3 | Removal Confidence | 92% |
| 4 | Reorder Recommendations | 42 |
| 5 | ATPG Additions Suggested | 18 |
| 6 | Fault Models Targeted | 4 |
| 7 | Low-Power Sets | 12 |
| 8 | Estimated Power Saving | 21.6% |
| 9 | Coverage Delta | 98.1% → 99.3% |
| 10 | Total Recommendations | 104 |

---

## 4.2 Scan Debug Recommendation Agent (15)

### Scan Chain Debug

| # | Title | Example value |
|---|-------|---------------|
| 1 | Broken Chains Detected | 7 |
| 2 | Debug Recommendations | 14 |
| 3 | Average Confidence | 88% |

### ATPG Constraint Review

| # | Title | Example value |
|---|-------|---------------|
| 4 | Constraint Violations | 23 |
| 5 | Review Recommendations | 19 |
| 6 | Coverage Impact | +1.8% |

### Timing Debug

| # | Title | Example value |
|---|-------|---------------|
| 7 | Timing Violations | 11 |
| 8 | Timing Debug Recommendations | 16 |
| 9 | Worst Slack | −42 ps |

### Power Related Debug

| # | Title | Example value |
|---|-------|---------------|
| 10 | Power Violations | 9 |
| 11 | Power Debug Recommendations | 12 |
| 12 | Peak Switching Activity | 74% |

### Physical Defect Investigation

| # | Title | Example value |
|---|-------|---------------|
| 13 | Defect Suspects | 31 |
| 14 | Investigation Recommendations | 18 |
| 15 | Defect Localization Accuracy | 91% |

---

## 4.3 Test Optimization Recommendation Agent (19)

### Adaptive Testing

| # | Title | Example value |
|---|-------|---------------|
| 1 | Adaptive Recommendations | 22 |
| 2 | Test Time Reduction | 18% |
| 3 | Flow Variants Evaluated | 8 |

### Test Stop Optimization

| # | Title | Example value |
|---|-------|---------------|
| 4 | Stop Recommendations | 17 |
| 5 | Escapes Prevented | 43 |
| 6 | Active Stop Rules | 9 |

### Risk-Based Testing

| # | Title | Example value |
|---|-------|---------------|
| 7 | High-Risk Devices | 58 |
| 8 | Risk Recommendations | 24 |
| 9 | Average Risk Score | 0.74 |

### Yield Optimization

| # | Title | Example value |
|---|-------|---------------|
| 10 | Current Yield | 87.4% |
| 11 | Yield Recommendations | 21 |
| 12 | Projected Yield Gain | +3.1% |

### Cost Reduction

| # | Title | Example value |
|---|-------|---------------|
| 13 | Estimated Cost Saving | $48K |
| 14 | Cost Recommendations | 16 |
| 15 | Cost Per Device | $0.38 |

### Multi-Site Optimization

| # | Title | Example value |
|---|-------|---------------|
| 16 | Active Test Sites | 16 |
| 17 | Site Recommendations | 11 |
| 18 | Site Correlation Delta | ±2.3% |

### Summary

| # | Title | Example value |
|---|-------|---------------|
| 19 | Total Recommendations | 111 |

---

# Flat master list (title only)

### Dashboard
1. Total Test Cost  
2. Cost per Wafer  
3. Cost per Die  
4. Test Time  
5. Yield  
6. ROI Improvement  

### Scan Chain · Overview
7. Overall Scan Health  
8. Total Scan Chains  
9. Healthy Chains  
10. Failing Chains  
11. Scan Coverage  
12. Average Diagnosis Confidence  
13. Average Test Time  

### Scan Chain · Pattern Analysis
14. Pattern Files Ingested  
15. Scan Vectors Parsed  
16. File Integrity  
17. Pattern Coverage  
18. Metadata Extracted  
19. Embeddings Generated  
20. Pattern Clusters  
21. Redundant Patterns  
22. Similarity Analyses  
23. Pass / Fail Linked  
24. Quality Reports  

### Scan Chain · Failure Analysis
25. Imported Test Files  
26. Overall Failure Rate  
27. Failing Test Patterns  
28. Die Failure Rate  
29. Wafer Failure Rate  
30. Lot Failure Rate  
31. Fault Categories  
32. Root Cause Confidence  
33. Recurring Failures  

### Scan Chain · Scan Diagnosis
34. Failing Scan Chains  
35. Failing Scan Cells  
36. Chain Breaks Detected  
37. Shift / Capture Issues  
38. Chains in Topology  
39. Chains Ranked  
40. Failure Correlations  
41. Top Failing Chain  
42. Diagnosis Reports  
43. Debug Locations  
44. Average Diagnosis Confidence (Diagnosis)  
45. Diagnoses Pending Review  

### Wafer · Overview
46. Number of Wafers  
47. Number of Dies  
48. Good Dies  
49. Bad Dies  
50. Defect Clusters  
51–59. Centre · Donut · Edge-Ring · Scratch · Near-Full · Normal · Edge-Loc · Local · Random (classification cards)  
60–66. Total Wafers · Total Dies · Good Dies · Bad Dies · Average Yield · Estimated Savings · AI Confidence (summary bar)  

### Wafer · Defect tabs (same 8 titles × 9 tabs)
67. Total Wafers  
68. Good Dies  
69. Bad Dies  
70. Average Yield  
71. Average Confidence  
72. Total Dies  
73. Defect Severity  
74. Estimated Yield Loss  

### Recommendation · Pattern Agent
75. Redundant Patterns  
76. Removal Recommended  
77. Removal Confidence  
78. Reorder Recommendations  
79. ATPG Additions Suggested  
80. Fault Models Targeted  
81. Low-Power Sets  
82. Estimated Power Saving  
83. Coverage Delta  
84. Total Recommendations  

### Recommendation · Scan Debug Agent
85. Broken Chains Detected  
86. Debug Recommendations  
87. Average Confidence  
88. Constraint Violations  
89. Review Recommendations  
90. Coverage Impact  
91. Timing Violations  
92. Timing Debug Recommendations  
93. Worst Slack  
94. Power Violations  
95. Power Debug Recommendations  
96. Peak Switching Activity  
97. Defect Suspects  
98. Investigation Recommendations  
99. Defect Localization Accuracy  

### Recommendation · Test Optimization Agent
100. Adaptive Recommendations  
101. Test Time Reduction  
102. Flow Variants Evaluated  
103. Stop Recommendations  
104. Escapes Prevented  
105. Active Stop Rules  
106. High-Risk Devices  
107. Risk Recommendations  
108. Average Risk Score  
109. Current Yield  
110. Yield Recommendations  
111. Projected Yield Gain  
112. Estimated Cost Saving  
113. Cost Recommendations  
114. Cost Per Device  
115. Active Test Sites  
116. Site Recommendations  
117. Site Correlation Delta  
118. Total Recommendations  

---

*Example values are from mock data. Some Overview summary KPIs share IDs with Pattern / Failure / Diagnosis tab KPIs.*
