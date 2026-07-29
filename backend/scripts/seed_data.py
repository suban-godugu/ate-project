"""Seed row definitions matching dashboard src/types shapes."""

EXECUTIVE_KPIS = [
    ("total-test-cost", "Total Test Cost", "$2.4M", None, -4.2, "down", [42, 38, 40, 36, 34, 33, 31]),
    ("cost-per-wafer", "Cost per Wafer", "$184", None, -2.8, "down", [210, 205, 198, 192, 188, 186, 184]),
    ("cost-per-die", "Cost per Die", "$0.018", None, -5.1, "down", [22, 21, 20, 19.5, 19, 18.5, 18]),
    ("test-time", "Test Time", "42.6s", None, -3.2, "down", [48, 47, 46, 45, 44, 43, 42.6]),
    ("overall-yield", "Overall Yield", "93.8%", None, 1.4, "up", [91, 91.5, 92, 92.5, 93, 93.5, 93.8]),
    ("defect-rate", "Defect Rate", "6.2%", None, -0.8, "down", [8, 7.5, 7.2, 7, 6.8, 6.5, 6.2]),
]

SCAN_CHAIN_KPIS = [
    ("overview:total-chains", "Total Scan Chains", "1,248", None, 2.1, "up", [1180, 1200, 1220, 1235, 1248]),
    ("overview:failing-chains", "Failing Chains", "37", None, -8.4, "down", [52, 48, 45, 41, 37]),
    ("overview:pass-rate", "Pass Rate", "97.0%", None, 1.2, "up", [95.2, 95.8, 96.2, 96.6, 97.0]),
]

MBIST_FAILURE_ROWS = [
    {"sessionId": "LB-20260629-001", "logicBlock": "LB-CPU-042", "controller": "CTRL-A1", "misrSignature": "0xA4F28B1C", "expectedSignature": "0xA4F28B1C", "coverage": 98.2, "status": "Failed", "timestamp": "2026-06-29 10:12"},
    {"sessionId": "LB-20260629-002", "logicBlock": "LB-GPU-118", "controller": "CTRL-B2", "misrSignature": "0x8B2C104E", "expectedSignature": "0x8B2C109A", "coverage": 94.6, "status": "Critical", "timestamp": "2026-06-29 10:08"},
    {"sessionId": "LB-20260629-003", "logicBlock": "LB-NOC-007", "controller": "CTRL-C1", "misrSignature": "0x4E891432", "expectedSignature": "0x4E891432", "coverage": 96.8, "status": "Failed", "timestamp": "2026-06-29 09:54"},
    {"sessionId": "LB-20260629-004", "logicBlock": "LB-PCIe-056", "controller": "CTRL-A2", "misrSignature": "0xC0120048", "expectedSignature": "0xC0120048", "coverage": 97.4, "status": "Warning", "timestamp": "2026-06-29 09:42"},
    {"sessionId": "LB-20260629-005", "logicBlock": "LB-DSP-089", "controller": "CTRL-D1", "misrSignature": "0x2F8A44AC", "expectedSignature": "0x2F8A44B8", "coverage": 92.1, "status": "Critical", "timestamp": "2026-06-29 09:30"},
    {"sessionId": "LB-20260629-006", "logicBlock": "LB-CACHE-014", "controller": "CTRL-B1", "misrSignature": "0x6D1028F0", "expectedSignature": "0x6D1028F0", "coverage": 95.8, "status": "Failed", "timestamp": "2026-06-29 09:18"},
    {"sessionId": "LB-20260629-007", "logicBlock": "LB-IO-032", "controller": "CTRL-C2", "misrSignature": "0x9A3B6C12", "expectedSignature": "0x9A3B6C12", "coverage": 93.4, "status": "Warning", "timestamp": "2026-06-29 09:06"},
    {"sessionId": "LB-20260629-008", "logicBlock": "LB-SEC-201", "controller": "CTRL-A3", "misrSignature": "0x1104F088", "expectedSignature": "0x1104F09C", "coverage": 91.2, "status": "Failed", "timestamp": "2026-06-29 08:58"},
    {"sessionId": "LB-20260628-009", "logicBlock": "LB-MEM-033", "controller": "CTRL-B3", "misrSignature": "0x2208A044", "expectedSignature": "0x2208A044", "coverage": 94.1, "status": "Failed", "timestamp": "2026-06-28 14:20"},
    {"sessionId": "LB-20260628-010", "logicBlock": "LB-USB-017", "controller": "CTRL-D2", "misrSignature": "0xFF102388", "expectedSignature": "0xFF102390", "coverage": 90.5, "status": "Critical", "timestamp": "2026-06-28 13:05"},
]

# The seed script currently expects a separate LBIST row set.
# Reuse the existing logic-block-focused rows until dedicated LBIST fixtures land.
LBIST_FAILURE_ROWS = MBIST_FAILURE_ROWS

COST_PRODUCT_ROWS = [
    {"product": "Chip-X7", "lot": "LOT-4421", "wafer": "W-12", "totalCost": "$42,800", "costPerDie": "$0.48", "yield": "92.4%", "estimatedSavings": "$8,200"},
    {"product": "Chip-X7", "lot": "LOT-4822", "wafer": "W-08", "totalCost": "$38,600", "costPerDie": "$0.44", "yield": "94.1%", "estimatedSavings": "$6,400"},
    {"product": "Chip-A3", "lot": "LOT-3105", "wafer": "W-22", "totalCost": "$52,400", "costPerDie": "$0.52", "yield": "88.6%", "estimatedSavings": "$12,800"},
    {"product": "Chip-A3", "lot": "LOT-3106", "wafer": "W-15", "totalCost": "$48,200", "costPerDie": "$0.49", "yield": "90.2%", "estimatedSavings": "$9,600"},
    {"product": "Chip-X7", "lot": "LOT-4823", "wafer": "W-04", "totalCost": "$44,100", "costPerDie": "$0.46", "yield": "91.8%", "estimatedSavings": "$7,400"},
    {"product": "Chip-X7", "lot": "LOT-4421", "wafer": "W-12", "totalCost": "$41,200", "costPerDie": "$0.47", "yield": "93.1%", "estimatedSavings": "$7,900"},
    {"product": "Chip-A3", "lot": "LOT-8832", "wafer": "W-18", "totalCost": "$46,800", "costPerDie": "$0.50", "yield": "89.4%", "estimatedSavings": "$10,200"},
    {"product": "Chip-X7", "lot": "LOT-9921", "wafer": "W-06", "totalCost": "$39,900", "costPerDie": "$0.45", "yield": "94.8%", "estimatedSavings": "$5,800"},
]

EXECUTIVE_PATTERN_ROWS = [
    {"id": "PAT-001", "testTime": 42.6, "cost": 12400, "failRate": 2.4, "detectPower": 88, "roiScore": 92, "recommendation": "Keep"},
    {"id": "PAT-002", "testTime": 38.2, "cost": 10800, "failRate": 3.1, "detectPower": 85, "roiScore": 78, "recommendation": "Review"},
    {"id": "PAT-003", "testTime": 35.0, "cost": 9600, "failRate": 4.8, "detectPower": 72, "roiScore": 54, "recommendation": "Remove"},
    {"id": "PAT-004", "testTime": 28.4, "cost": 7200, "failRate": 1.9, "detectPower": 91, "roiScore": 88, "recommendation": "Keep"},
    {"id": "PAT-005", "testTime": 24.1, "cost": 6400, "failRate": 2.2, "detectPower": 89, "roiScore": 86, "recommendation": "Keep"},
]

EXECUTIVE_COST_TREND = [
    {"day": "Mon", "totalCost": 420000, "costPerWafer": 210},
    {"day": "Tue", "totalCost": 405000, "costPerWafer": 205},
    {"day": "Wed", "totalCost": 398000, "costPerWafer": 198},
    {"day": "Thu", "totalCost": 384000, "costPerWafer": 192},
    {"day": "Fri", "totalCost": 376000, "costPerWafer": 188},
    {"day": "Sat", "totalCost": 372000, "costPerWafer": 186},
    {"day": "Sun", "totalCost": 368000, "costPerWafer": 184},
]

MBIST_KPIS = [
    ("overview:total-instances", "Total Memory Instances", "1,248", None, 2.1, "up", [1180, 1200, 1220, 1235, 1248]),
    ("overview:failed", "Failed Memories", "86", None, -6.4, "down", [112, 105, 98, 94, 86]),
    ("overview:coverage", "Memory Coverage", "97.4%", None, 0.9, "up", [95.2, 96, 96.6, 97, 97.4]),
]

LBIST_KPIS = [
    ("overview:total-blocks", "Logic Blocks Tested", "842", None, 3.2, "up", [780, 800, 815, 830, 842]),
    ("overview:failed", "Failed Blocks", "38", None, -9.1, "down", [52, 48, 44, 41, 38]),
    ("overview:coverage", "LBIST Coverage", "96.2%", None, 1.4, "up", [93.8, 94.2, 94.8, 95.6, 96.2]),
]

WAFER_KPIS = [
    ("overview:total-wafers", "Wafers Analyzed", "248", None, 4.2, "up", [210, 220, 228, 238, 248]),
    ("overview:avg-yield", "Average Yield", "91.4%", None, 1.1, "up", [89, 89.8, 90.2, 91, 91.4]),
    ("overview:defect-rate", "Defect Rate", "8.6%", None, -0.9, "down", [10, 9.6, 9.2, 8.9, 8.6]),
]

COST_KPIS = [
    ("overview:total-cost", "Total Test Cost", "$2.4M", None, -4.2, "down", [2.8, 2.6, 2.5, 2.45, 2.4]),
    ("overview:cost-per-wafer", "Cost per Wafer", "$184", None, -2.8, "down", [210, 205, 198, 192, 184]),
    ("overview:roi", "Optimization ROI", "22%", None, 5.4, "up", [14, 16, 18, 20, 22]),
]

RECOMMENDATION_KPIS = [
    ("overview:total", "Total Recommendations", "186", None, 12.4, "up", [142, 152, 165, 172, 186]),
    ("overview:critical", "Critical Recommendations", "24", None, -8.2, "down", [32, 28, 26, 25, 24]),
    ("overview:yield", "Estimated Yield Improvement", "+5.8%", None, 1.4, "up", [3.2, 4, 4.8, 5.2, 5.8]),
]

RECOMMENDATIONS = [
    ("pattern", "Pattern Optimization", "Critical", 94.0, "Reduce test time by ~12%", "Consolidate redundant MBIST patterns on Core-A", "pending"),
    ("pattern", "Scan Compression", "High", 88.0, "-6.2s runtime", "Compress pattern segments 3-5 on SC-4821", "pending"),
    ("scan-debug", "Root Cause Analysis", "Critical", 91.0, "+1.2% yield", "Add hold-time margin pattern for SC-3107", "pending"),
    ("scan-debug", "Clock Debug", "High", 87.0, "$18K savings", "Retest affected patterns on LOT-4421", "approved"),
    ("test-optimization", "Adaptive Testing", "High", 89.0, "-8.4s test time", "Reduce redundant LBIST patterns on GPU block", "pending"),
    ("test-optimization", "Cost Reduction", "Medium", 84.0, "$42K savings", "Merge overlapping MBIST and scan patterns", "pending"),
    ("pattern", "MBIST Pattern Optimization", "High", 91.0, "+0.8% yield", "Repair address decoder segment MEM-004821", "pending"),
    ("scan-debug", "LBIST Debug", "Medium", 82.0, "+1.4% coverage", "Extend LBIST coverage for NOC cluster", "pending"),
    ("test-optimization", "Wafer Retest", "Low", 78.0, "+0.4% yield", "Retest edge dies only on W-12", "approved"),
    ("pattern", "Wafer Yield Improvement", "Critical", 92.0, "+2.1% yield", "Hotspot retest optimization on edge-ring defect", "pending"),
    ("scan-debug", "Memory Repair", "High", 86.0, "+0.6% yield", "Allocate spare row redundancy on Bank-2", "pending"),
    ("test-optimization", "Runtime Reduction", "Medium", 80.0, "-4.8s runtime", "Parallel LBIST execution on Core-B", "pending"),
]

SCAN_CHAIN_FAILURES = [
    ("SC-4821", "PAT-1042", "Core-A", 1842, "Stuck-at", "Clock skew on chain boundary", "Confirmed"),
    ("SC-3107", "PAT-0891", "Core-B", 920, "Transition", "Suspected hold violation", "Investigating"),
    ("SC-7892", "PAT-007", "Core-C", 1204, "Bridging", "Via resistance anomaly", "Pending"),
    ("SC-2441", "PAT-056", "Core-A", 640, "Stuck-at", "Scan enable timing", "Confirmed"),
    ("SC-9012", "PAT-203", "Core-D", 1580, "Transition", "Hold time marginality", "Investigating"),
    ("SC-1567", "PAT-118", "Core-B", 880, "Delay", "Clock tree skew", "Pending"),
    ("SC-3344", "PAT-042", "Core-A", 2048, "Stuck-at", "Chain boundary defect", "Confirmed"),
    ("SC-5566", "PAT-891", "Core-C", 1120, "Transition", "Pattern ordering issue", "Investigating"),
]

ALERTS = [
    ("Scan Chain", "Critical", "Open", "Critical Scan Chain Failure", "SC-4821 pattern failure detected on LOT-4421"),
    ("MBIST", "Critical", "Investigating", "MBIST Repair Threshold", "SRAM Bank-2 repair failure threshold exceeded"),
    ("Wafer", "High", "Open", "Yield Drop Warning", "Wafer W-08 yield below 90% on edge dies"),
    ("LBIST", "High", "Investigating", "MISR Mismatch", "MISR signature mismatch on LB-GPU block"),
    ("Cost", "Medium", "Open", "Cost Budget Alert", "Test cost exceeded budget threshold by 12%"),
    ("AI Recommendation", "High", "Pending", "Optimization Pending", "Critical optimization pending engineer approval"),
    ("Scan Chain", "Medium", "Resolved", "Coverage Drop", "Coverage drop on PAT-118 pattern"),
    ("Wafer", "Critical", "Open", "Defect Hotspot", "Defect hotspot detected in zone C"),
]

WAFER_DEFECTS = [
    ("near-full", 96.0, 72.4, 42, 128, 64),
    ("centre", 91.0, 81.2, 64, 96, 96),
    ("edge-ring", 88.0, 84.6, 48, 180, 48),
    ("scratch", 85.0, 86.1, 72, 32, 160),
    ("donut", 84.0, 87.8, 55, 100, 100),
    ("local", 82.0, 88.4, 60, 140, 80),
    ("edge-loc", 80.0, 89.2, 45, 190, 40),
    ("random", 76.0, 90.1, 30, 80, 120),
]
