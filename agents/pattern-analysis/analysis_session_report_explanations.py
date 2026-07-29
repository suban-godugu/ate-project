"""
PA-UX-001 — Static explanation catalog for Analysis Session HTML export.

Presentation-only: no imports from model builders, engines, or exporters.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence


SectionGuide = Dict[str, Any]

CORE_SECTION_IDS = (
    "overview",
    "session_summary",
    "requirement_1_ingestion",
    "requirement_2_vectors",
    "requirement_3_metadata",
    "requirement_4_toggle",
    "embeddings",
    "clustering",
    "redundancy",
    "similarity",
    "pattern_outcomes",
    "validation",
    "appendix",
)

ML_SECTION_IDS = (
    "anomaly_by_lot",
    "anomaly",
    "failure_risk_by_lot",
    "failure_risk",
    "root_cause_by_lot",
    "root_cause",
    "recommendations_by_lot",
    "recommendations",
)

ALL_SECTION_IDS = CORE_SECTION_IDS + ML_SECTION_IDS


def _guide(
    *,
    description: str,
    why_it_matters: str,
    formula: str = "",
    example: str = "",
    interpretation: str = "",
    info_card: str = "",
) -> SectionGuide:
    return {
        "description": description,
        "why_it_matters": why_it_matters,
        "formula": formula,
        "example": example,
        "interpretation": interpretation,
        "info_card": info_card,
    }


SECTION_GUIDES: Dict[str, SectionGuide] = {
    "overview": _guide(
        description=(
            "The Cover section identifies the Analysis Session under review: the STIL "
            "stimulus file, cryptographic session hash, manufacturing scale (LOTs and "
            "ATE logs), and pipeline completion status."
        ),
        why_it_matters=(
            "Engineers and auditors need a single authoritative identity block before "
            "reviewing metrics. The session hash ties every artifact in this report to "
            "one deterministic analysis run."
        ),
        example=(
            "Educational Example — Workflow:\n"
            "STIL file ingested → ATE logs parsed → toggle metrics computed → "
            "embeddings generated → clustering and similarity artifacts written → "
            "this report assembled from PA-Analysis-Session_report_model.json."
        ),
        interpretation=(
            "Read STIL File as the design stimulus source. Session Hash is the "
            "fingerprint of the full session artifact set. LOTs and ATE Logs describe "
            "manufacturing breadth. Completion % reflects requirement readiness across the "
            "pipeline. Engineering Status summarizes whether all required artifacts "
            "are present."
        ),
        info_card=(
            "What is a Session Hash? A deterministic SHA-256 digest computed from "
            "session artifacts. Any change to inputs or pipeline outputs produces a "
            "different hash, enabling audit traceability."
        ),
    ),
    "session_summary": _guide(
        description=(
            "The Executive Summary rolls up key counts and cross-requirement KPIs into a "
            "single dashboard: dataset scale, toggle coverage, embedding coverage, "
            "cluster structure, redundancy signals, and outcome failures."
        ),
        why_it_matters=(
            "Managers and new team members can assess session health in one view "
            "before drilling into requirement-specific sections."
        ),
        example=(
            "Educational Example:\n"
            "1,000 patterns · 90 ATE logs · 52 clusters · 340 redundancy candidates · "
            "12 FAIL outcomes — a typical large-session rollup."
        ),
        interpretation=(
            "Higher Toggle Coverage Avg % generally indicates broader physical-cell "
            "exercise. Embeddings and Clusters show how much of the pattern space was "
            "vectorized and grouped. Redundancy Candidates flag near-duplicate units "
            "for review. FAIL Outcomes count patterns with at least one failing "
            "execution."
        ),
        info_card=(
            "The Manifest table below lists the STIL source, session hash, generation "
            "timestamp, and a preview of ATE log inputs for this session."
        ),
    ),
    "requirement_1_ingestion": _guide(
        description=(
            "Requirement 1 covers STIL structural ingest (PA-FR-001): the design stimulus "
            "file, session manifest, and ATE log inventory that anchor the Analysis Session."
        ),
        why_it_matters=(
            "Every downstream metric depends on a valid ingest. Engineers verify the STIL "
            "source and session manifest before interpreting vectors, metadata, or coverage."
        ),
        example=(
            "Educational Example:\n"
            "chip.stil ingested → manifest records session hash, LOTs, and ATE log paths."
        ),
        interpretation=(
            "STIL File is the authoritative stimulus. Session Hash fingerprints the full "
            "artifact set. LOTs and ATE Logs describe manufacturing breadth at ingest time."
        ),
        info_card=(
            "Requirement 1 is read-only presentation of PA-Analysis-Session_manifest.json "
            "and session overview artifacts."
        ),
    ),
    "requirement_2_vectors": _guide(
        description=(
            "Requirement 2 presents scan vector materialization (PA-FR-002): reconstructed "
            "pattern×log vectors used for audit and downstream analysis."
        ),
        why_it_matters=(
            "Vectors confirm that scan stimulus was expanded and indexed per execution unit "
            "before toggle, embedding, and correlation stages."
        ),
        example=(
            "Educational Example:\n"
            "P001 · die_3.log · run_id 7 → one CVM vector row in the session artifact."
        ),
        interpretation=(
            "Scan Vectors is the count of vector rows in scope. The table shows Top-N "
            "pattern×log units; full vectors remain in PA-Analysis-Session_scan_vectors.json."
        ),
    ),
    "requirement_3_metadata": _guide(
        description=(
            "Requirement 3 summarizes session metadata and pattern×chain inventory "
            "(PA-FR-003 context): scale counts and summary rollups from ingest artifacts."
        ),
        why_it_matters=(
            "Metadata answers how large the session is—patterns, executions, and "
            "pattern×chain keys—before reviewing toggle or ML sections."
        ),
        example=(
            "Educational Example:\n"
            "1,000 patterns · 12 execution records · 48 pattern×chain summary keys."
        ),
        interpretation=(
            "Patterns and Execution Records describe dataset scale. Pattern×Chain Keys "
            "counts distinct summary buckets available for drill-down."
        ),
    ),
    "requirement_4_toggle": _guide(
        description=(
            "Requirement 4 presents toggle coverage and density (PA-FR-004): how many "
            "physical memory cells changed state and how actively cells transitioned "
            "during testing."
        ),
        why_it_matters=(
            "Toggle coverage and density quantify how thoroughly the design was "
            "exercised. Low coverage may indicate untested regions; density reflects "
            "switching activity per possible transition."
        ),
        formula=(
            "File rollup (PA-FR-004):\n"
            "toggle_coverage_pct = (|toggled_cells_global| / total_physical_cells) × 100\n"
            "toggle_density_pct = (total_toggle_count / file_max_trans) × 100\n"
            "where file_max_trans = patterns_analyzed × (total_physical_cells − scan_chains_analyzed)\n\n"
            "Scan-chain level:\n"
            "toggle_coverage_pct = (ch_toggled_cells_count / ch_len) × 100\n"
            "toggle_density_pct = (ch_toggles / (ch_len − 1)) × 100"
        ),
        example=(
            "Educational Example:\n"
            "Chip cells: 5,382 · Cells toggled: 3,703\n"
            "Toggle Coverage = 3,703 / 5,382 × 100 = 68.80%\n"
            "Toggle Density = transitions / max_possible_transitions × 100"
        ),
        interpretation=(
            "Coverage Avg/Max/Min % summarize per-execution toggle coverage across "
            "the session. Higher coverage means more unique cells toggled at least once. "
            "Density Avg % measures transition activity relative to the maximum possible "
            "transitions. PASS and FAIL counts reflect latest ATE execution results."
        ),
        info_card=(
            "What is Toggle Density? The percentage of all possible bit transitions "
            "that actually occurred during testing. Higher density generally indicates "
            "richer dynamic test activity."
        ),
    ),
    "embeddings": _guide(
        description=(
            "Pattern embeddings convert each pattern×source-log execution unit into a "
            "fixed-dimension numeric vector. Vectors capture structural features of "
            "scan behavior without storing raw bitstreams in the report."
        ),
        why_it_matters=(
            "Embeddings enable deterministic similarity search, clustering, and "
            "redundancy analysis. Without vectors, cross-pattern comparison at scale "
            "would require pairwise bit-level comparison."
        ),
        formula=(
            "Pattern unit → feature extraction → fixed-dimension vector (e.g. 128-D)\n"
            "Similarity metric: cosine similarity between unit vectors"
        ),
        example=(
            "Educational Example:\n"
            "Pattern A bitstream 101001… → 128-dimensional vector → used in "
            "similarity search and cluster assignment."
        ),
        interpretation=(
            "Embeddings counts how many units were successfully vectorized. Skipped "
            "indicates units excluded (e.g. missing data). Dimension is the vector "
            "length. Version and Metric identify the feature schema and similarity "
            "measure used downstream."
        ),
        info_card=(
            "Vectors are omitted from this HTML report for size; only metadata rows "
            "are shown. Full vectors remain in PA-Analysis-Session_embeddings.json."
        ),
    ),
    "clustering": _guide(
        description=(
            "Clustering groups pattern×log units with similar embedding vectors into "
            "clusters. Each cluster has a representative pattern and an average "
            "intra-cluster similarity score."
        ),
        why_it_matters=(
            "Clusters reveal structural families in the pattern set, focus engineering "
            "review on representative units, and provide context for redundancy detection."
        ),
        formula=(
            "Units assigned to nearest centroid by cosine similarity (exhaustive, "
            "deterministic tie-break). Singleton clusters contain exactly one unit."
        ),
        example=(
            "Educational Example:\n"
            "1,000 patterns → 52 clusters → average ~19 patterns per cluster."
        ),
        interpretation=(
            "Clusters is the total cluster count. Units is the number of pattern×log "
            "assignments. Singletons are clusters with one member. Largest Cluster and "
            "Average Size describe distribution. Threshold is the similarity cutoff used "
            "during clustering."
        ),
        info_card=(
            "A cluster groups units that behave similarly in embedding space. "
            "Review the representative pattern of large clusters first."
        ),
    ),
    "redundancy": _guide(
        description=(
            "Redundancy analysis flags near-duplicate pattern×log units within "
            "clusters—pairs whose embedding vectors are highly similar and may "
            "represent redundant test coverage."
        ),
        why_it_matters=(
            "Identifying redundant patterns can reduce test time, storage, and "
            "review effort without sacrificing defect-detection confidence."
        ),
        formula=(
            "Candidate pair: raw_similarity ≥ similarity_threshold within cluster\n"
            "confidence_score derived from embedding similarity (presentation only)"
        ),
        example=(
            "Educational Example:\n"
            "Cluster with 120 patterns → only 8 unique behaviours → "
            "112 potentially redundant patterns for engineering review."
        ),
        interpretation=(
            "Candidates is the number of flagged pairs. Units Represented counts "
            "distinct units involved. Clusters Evaluated is how many clusters were "
            "scanned. Avg/Highest Confidence summarize match strength."
        ),
        info_card=(
            "Redundancy is advisory. High similarity does not automatically mean a "
            "pattern can be removed—engineering judgment is required."
        ),
    ),
    "similarity": _guide(
        description=(
            "Similarity analysis computes exact top-N cosine neighbors for every "
            "pattern×source-log unit. Cosine similarity measures the angle between "
            "two embedding vectors."
        ),
        why_it_matters=(
            "Similarity pairs help engineers find structurally related patterns, "
            "identify stable vs divergent behavior, and corroborate clustering results."
        ),
        formula=(
            "cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)\n"
            "Range: 0.0 (orthogonal) to 1.0 (identical direction)"
        ),
        example=(
            "Educational Example — reading cosine similarity:\n"
            "1.00 — nearly identical\n"
            "0.95 — very similar\n"
            "0.80 — moderately similar\n"
            "0.50 — different"
        ),
        interpretation=(
            "Units and Pairs describe the similarity graph size. Average Similarity "
            "is the mean across all stored pairs. Max Similarity shows the strongest "
            "match in the artifact. Stable Patterns have consistently high average "
            "similarity; Divergent Patterns have lower averages."
        ),
        info_card=(
            "Cosine Similarity: a mathematical measure of how similar two embedding "
            "vectors are, based on the angle between them in vector space."
        ),
    ),
    "pattern_outcomes": _guide(
        description=(
            "Pattern Outcome Correlation aggregates PASS/FAIL results across LOTs and "
            "executions for each pattern×chain combination, highlighting cross-LOT "
            "consistency and failure concentration."
        ),
        why_it_matters=(
            "Manufacturing teams need to see which patterns fail consistently, "
            "which fail only on certain LOTs, and where data quality flags apply."
        ),
        example=(
            "Educational Example:\n"
            "A pattern PASS on LOT-A but FAIL on LOT-B may indicate a "
            "lot-specific manufacturing issue rather than a design defect."
        ),
        interpretation=(
            "PASS/FAIL/Unknown counts summarize outcome labels. Outcomes is the "
            "number of distinct pattern×chain outcome records. Cross-LOT Outcomes "
            "indicates patterns observed across multiple manufacturing lots. "
            "Validation reflects data-quality checks on the outcome artifact."
        ),
        info_card=(
            "L1 PASS/FAIL outcomes from ATE logs remain authoritative. This section "
            "aggregates them for multi-LOT session review."
        ),
    ),
    "validation": _guide(
        description=(
            "The Validation Summary is a deterministic checklist of requirement completion "
            "across the Analysis Session pipeline, derived from artifact presence "
            "and readability."
        ),
        why_it_matters=(
            "Before signing off an analysis, engineers verify every required pipeline requirement "
            "produced a complete artifact. Warnings highlight non-fatal issues."
        ),
        example=(
            "Educational Example:\n"
            "phase_1_ingest: Complete · phase_4_toggle: Complete · "
            "phase_5_embeddings: Complete → overall Validation Status: Complete"
        ),
        interpretation=(
            "Complete means the artifact is present and readable. Partial or Missing "
            "requires engineering follow-up. Completion % reflects overall pipeline "
            "progress. Warnings count non-blocking issues recorded during validation."
        ),
        info_card=(
            "Validation does not re-run analysis. It only checks that expected "
            "artifacts exist and conform to the report model."
        ),
    ),
    "appendix": _guide(
        description=(
            "The Audit Appendix lists cryptographic hashes, generation timestamps, "
            "and provenance for every session artifact. Engineering Data Exchange (EDE) "
            "artifacts listed here can be consumed by external manufacturing analytics "
            "and sign-off tools."
        ),
        why_it_matters=(
            "Auditors and downstream systems need verifiable lineage from raw inputs "
            "to exported analysis products without re-computing metrics."
        ),
        example=(
            "Educational Example — Engineering Data Exchange workflow:\n"
            "Analysis Session → PA-Analysis-Session_*.json artifacts → "
            "EDE export (pattern_analysis_master.json) → Manufacturing Analytics"
        ),
        interpretation=(
            "Each provenance row shows logical_name (artifact role), artifact_filename, "
            "status, generated_by module, version, sha256 hash, and generation_timestamp. "
            "Use sha256 to verify artifact integrity against on-disk files."
        ),
        info_card=(
            "Engineering Data Exchange (EDE) performs join-only normalization of "
            "session artifacts for external consumers. It never recalculates metrics."
        ),
    ),
    "anomaly_by_lot": _guide(
        description=(
            "Advisory unsupervised anomaly scores at pattern × LOT grain, aggregating "
            "ATE log executions within each manufacturing lot."
        ),
        why_it_matters=(
            "LOT-scoped anomalies surface unusual pattern behavior that may indicate "
            "process variation without replacing authoritative PASS/FAIL outcomes."
        ),
        interpretation=(
            "Scores are advisory only. Higher anomaly scores suggest executions that "
            "deviate from typical behavior within the session. Grain is pattern_x_lot."
        ),
        info_card="ML outputs are advisory. L1 PASS/FAIL outcomes remain authoritative.",
    ),
    "anomaly": _guide(
        description=(
            "Advisory unsupervised anomaly scores at pattern × source_log grain for "
            "log-level drill-down."
        ),
        why_it_matters="Identifies unusual individual ATE log executions for investigation.",
        interpretation="Advisory scores at per-log resolution. Compare with LOT-level view above.",
        info_card="Log-level drill-down; does not mutate L1 Analysis Session artifacts.",
    ),
    "failure_risk_by_lot": _guide(
        description=(
            "Advisory failure-risk predictions at pattern × LOT grain."
        ),
        why_it_matters=(
            "Prioritizes patterns that the model predicts may fail, aggregated across "
            "logs within each LOT."
        ),
        interpretation=(
            "Predicted FAIL counts patterns scored above the failure threshold. "
            "Scores are advisory; observed PASS/FAIL from ATE logs remain authoritative."
        ),
        info_card="LOT grain aggregates log executions for manufacturing-scale review.",
    ),
    "failure_risk": _guide(
        description="Advisory failure-risk predictions at pattern × source_log grain.",
        why_it_matters="Log-level failure-risk drill-down for targeted investigation.",
        interpretation="Advisory scores per ATE log execution.",
        info_card="Scores are advisory; L1 PASS/FAIL outcomes remain authoritative.",
    ),
    "root_cause_by_lot": _guide(
        description=(
            "Advisory investigation priority rankings at pattern × LOT grain."
        ),
        why_it_matters=(
            "Ranks candidates for engineering investigation based on observed failures "
            "and contributing signals."
        ),
        interpretation=(
            "Rankings are investigation priorities, not causal diagnoses. "
            "Observed FAIL counts patterns with failing executions."
        ),
        info_card="Not a causal diagnosis — use for prioritization only.",
    ),
    "root_cause": _guide(
        description="Advisory investigation priority at pattern × source_log grain.",
        why_it_matters="Log-level ranked investigation candidates.",
        interpretation="Investigation scores rank review priority; not root-cause proof.",
        info_card="Log-level drill-down for ranked investigation candidates.",
    ),
    "recommendations_by_lot": _guide(
        description=(
            "Advisory pattern prioritization at pattern × LOT grain, fusing failure "
            "risk, anomaly, and root-cause signals."
        ),
        why_it_matters="Provides ranked recommended actions for manufacturing review.",
        interpretation="High Priority counts top-tier recommendations. All outputs are advisory.",
        info_card="Fuses multiple ML signals into a single prioritized action list.",
    ),
    "recommendations": _guide(
        description="Advisory pattern prioritization at pattern × source_log grain.",
        why_it_matters="Log-level fused recommendations for targeted action.",
        interpretation="Priority tier and recommended_action guide review order.",
        info_card="Log-level drill-down for fused ML recommendations.",
    ),
}


KPI_TOOLTIPS: Dict[str, str] = {
    "STIL File": "Standard Test Interface Language file defining scan patterns for this session.",
    "Session Hash": "Deterministic SHA-256 fingerprint of the full session artifact set.",
    "Generated": "UTC timestamp when the report model was built.",
    "LOTs": "Number of manufacturing lots (wafer groups) represented in ATE logs.",
    "ATE Logs": "Number of automatic test equipment log files ingested.",
    "Patterns": "Count of distinct test patterns in the STIL file.",
    "Execution Records": "Total pattern×chain×log execution rows analyzed.",
    "Executions": "Distinct execution units in the session summary.",
    "Completion %": "Percentage of pipeline requirements with complete artifacts.",
    "Engineering Status": "Overall engineering analysis completion badge.",
    "Report Version": "Engineering Report presentation schema version.",
    "Model Hash": "SHA-256 hash of PA-Analysis-Session_report_model.json.",
    "Toggle Coverage Avg %": "Mean toggle coverage across all executions in the session.",
    "Clusters": "Number of embedding clusters identified.",
    "Redundancy Candidates": "Near-duplicate unit pairs flagged for review.",
    "Similarity Pairs": "Total stored cosine-similarity neighbor pairs.",
    "FAIL Outcomes": "Patterns with at least one failing execution.",
    "Scan Vectors": "Count of reconstructed scan vector records.",
    "PASS": "Executions or outcomes with a passing latest result.",
    "FAIL": "Executions or outcomes with a failing latest result.",
    "Coverage Avg %": "Average toggle coverage percentage across executions.",
    "Coverage Max %": "Maximum toggle coverage percentage observed.",
    "Coverage Min %": "Minimum toggle coverage percentage observed.",
    "Density Avg %": "Average toggle density — transitions relative to max possible.",
    "Embeddings": "Pattern×log units successfully converted to vectors.",
    "Skipped": "Units excluded from embedding generation.",
    "Dimension": "Length of each embedding vector.",
    "Version": "Embedding feature schema version.",
    "Metric": "Similarity measure used (typically cosine).",
    "Units": "Total pattern×log units in the analysis scope.",
    "Singletons": "Clusters containing exactly one unit.",
    "Largest Cluster": "Size of the biggest cluster by unit count.",
    "Average Size": "Mean number of units per cluster.",
    "Threshold": "Similarity threshold used for clustering or redundancy.",
    "Candidates": "Redundant or near-duplicate pairs flagged.",
    "Units Represented": "Distinct units appearing in redundancy candidates.",
    "Clusters Evaluated": "Clusters scanned for redundancy.",
    "Avg Confidence": "Mean confidence score across redundancy candidates.",
    "Highest Confidence": "Strongest redundancy match confidence.",
    "Embedding Version": "Version tag of the embedding artifact.",
    "Average Similarity": "Mean cosine similarity across all stored pairs.",
    "Max Similarity": "Highest cosine similarity in the artifact.",
    "Pairs": "Total similarity neighbor pairs stored.",
    "Unknown": "Outcomes without a definitive PASS or FAIL label.",
    "Outcomes": "Distinct pattern×chain outcome records.",
    "Cross-LOT Outcomes": "Outcomes observed across multiple manufacturing lots.",
    "Validation": "Data-quality validation status of the outcome artifact.",
    "Validation Status": "Overall session validation result.",
    "Warnings": "Count of non-fatal validation warnings.",
    "Model": "ML model version identifier.",
    "Grain": "Analysis resolution: pattern_x_lot or pattern_x_source_log.",
    "Scores": "Total anomaly scores computed.",
    "Displayed": "Rows shown in this report (Top-N cap may apply).",
    "Anomalies": "Units flagged as anomalous by the model.",
    "Advisory": "Whether outputs are advisory (not authoritative).",
    "Predictions": "Total failure-risk predictions.",
    "Predicted FAIL": "Patterns predicted to fail by the model.",
    "Rankings": "Total root-cause investigation rankings.",
    "Observed FAIL": "Patterns with observed failing executions.",
    "Recommendations": "Total fused ML recommendations.",
    "High Priority": "Recommendations in the highest priority tier.",
}


CHART_GUIDES: Dict[str, Dict[str, str]] = {
    "Top Pattern/Chain Failures": {
        "description": "Bar chart of FAIL counts grouped by pattern and scan chain.",
        "how_to_read": "Longer bars indicate more failing executions for that pattern×chain key.",
        "example": "Educational Example: P042|CH3 with bar value 15 means 15 FAIL executions.",
    },
    "Cluster Size Distribution": {
        "description": "Distribution of units across cluster sizes.",
        "how_to_read": "Shows how many clusters contain each size bucket of units.",
        "example": "Educational Example: a spike at size 1 indicates many singleton clusters.",
    },
    "Cluster Similarity Distribution": {
        "description": "Histogram of average intra-cluster cosine similarity.",
        "how_to_read": "Higher values indicate tighter, more homogeneous clusters.",
        "example": "Educational Example: peak near 0.95 means most clusters are very cohesive.",
    },
    "Redundancy Confidence Distribution": {
        "description": "Distribution of confidence scores for redundancy candidate pairs.",
        "how_to_read": "Higher confidence suggests stronger near-duplicate evidence.",
        "example": "Educational Example: scores above 0.98 are typical redundancy candidates.",
    },
    "Similarity Score Distribution": {
        "description": "Histogram of cosine similarity scores across all stored pairs.",
        "how_to_read": "Shows how similar pattern units are overall in this session.",
        "example": "Educational Example: mass near 1.0 means many near-identical pairs.",
    },
    "PASS/FAIL Outcome Distribution": {
        "description": "Breakdown of pattern outcome labels across the session.",
        "how_to_read": "Compare PASS vs FAIL counts for overall yield context.",
        "example": "Educational Example: 950 PASS and 50 FAIL across 1,000 outcomes.",
    },
}


TABLE_GUIDES: Dict[str, Dict[str, Any]] = {
    "Manifest": {
        "description": "Session manifest: STIL source, hash, timestamp, and ATE log inventory.",
        "columns": {
            "stil_file": "STIL stimulus filename.",
            "session_hash": "Deterministic session fingerprint.",
            "generated_timestamp": "When the session was generated.",
            "ate_log_count": "Number of ATE logs in the session.",
            "ate_logs_preview": "First few log filenames; full list in session artifacts.",
        },
        "example_row": "Educational Example: chip.stil · abc123… · 2026-07-20 · 90 logs",
    },
    "Top Pattern / Chain Coverage": {
        "description": "Per pattern×chain toggle coverage and PASS/FAIL rollup.",
        "columns": {
            "pattern_chain": "Pattern ID and scan chain joined (e.g. P001|CH1).",
            "execution_count": "Number of executions for this pattern×chain.",
            "pass_count": "Executions with PASS latest result.",
            "fail_count": "Executions with FAIL latest result.",
            "toggle_coverage_pct_avg": "Mean toggle coverage across executions.",
            "toggle_coverage_pct_max": "Maximum toggle coverage observed.",
            "toggle_coverage_pct_min": "Minimum toggle coverage observed.",
            "toggle_density_pct_avg": "Mean toggle density across executions.",
        },
        "example_row": "Educational Example: P001|CH1 · 10 execs · 8 PASS · 2 FAIL · 72% avg coverage",
    },
    "Top Executions": {
        "description": "Individual pattern×chain×log execution rows with toggle metrics.",
        "columns": {
            "pattern_id": "Test pattern identifier.",
            "scan_chain_id": "Scan chain within the pattern.",
            "source_log": "ATE log filename.",
            "run_id": "Execution run identifier.",
            "toggle_count": "Number of bit transitions observed.",
            "toggle_coverage_pct": "Percentage of cells toggled at least once.",
            "toggle_density_pct": "Transitions relative to max possible.",
            "latest_result": "Most recent PASS or FAIL result.",
        },
        "example_row": "Educational Example: P001 · CH1 · die_3.log · toggle 42 · 68.8% coverage · PASS",
    },
    "Top Scan Vectors": {
        "description": "Reconstructed scan vector metadata per execution.",
        "columns": {
            "pattern_id": "Test pattern identifier.",
            "source_log": "ATE log source.",
            "run_id": "Execution run identifier.",
        },
        "example_row": "Educational Example: P001 · die_3.log · run_id 7",
    },
    "Top Embeddings (metadata)": {
        "description": "Embedding metadata per pattern×log unit (vectors omitted).",
        "columns": {
            "pattern_id": "Test pattern identifier.",
            "source_log": "ATE log source.",
            "run_id": "Execution run identifier.",
            "feature_version": "Feature extraction schema version.",
            "created_timestamp": "When the embedding was generated.",
        },
        "example_row": "Educational Example: P001 · die_3.log · feature v1.0",
    },
    "Largest Clusters": {
        "description": "Clusters ranked by size with representative patterns.",
        "columns": {
            "cluster_id": "Unique cluster identifier.",
            "representative_pattern": "Medoid or representative pattern ID.",
            "pattern_count": "Distinct patterns in the cluster.",
            "execution_count": "Total executions assigned.",
            "average_similarity": "Mean cosine similarity within the cluster.",
        },
        "example_row": "Educational Example: C001 · P042 · 19 patterns · 0.94 avg similarity",
    },
    "Top Unit Assignments": {
        "description": "Individual unit-to-cluster assignments with similarity to centroid.",
        "columns": {
            "unit_id": "Unique pattern×log unit identifier.",
            "pattern_id": "Test pattern identifier.",
            "cluster_id": "Assigned cluster.",
            "similarity_to_centroid": "Cosine similarity to cluster centroid.",
        },
        "example_row": "Educational Example: U_P001_die3 · P001 · C001 · 0.97",
    },
    "Top Redundancy Candidates": {
        "description": "Near-duplicate unit pairs flagged within clusters.",
        "columns": {
            "pattern_a": "First pattern in the candidate pair.",
            "pattern_b": "Second pattern in the candidate pair.",
            "cluster_id": "Cluster where the pair was found.",
            "raw_similarity": "Cosine similarity between the two units.",
            "confidence_score": "Presentation confidence for the redundancy flag.",
            "review_status": "Engineering review state.",
        },
        "example_row": "Educational Example: P001 vs P002 · C001 · 0.99 similarity",
    },
    "Top Similarity Pairs": {
        "description": "Highest-ranked cosine similarity neighbors per unit.",
        "columns": {
            "unit_a": "First unit in the pair.",
            "unit_b": "Second unit (neighbor).",
            "pattern_a": "Pattern ID of unit A.",
            "pattern_b": "Pattern ID of unit B.",
            "rank": "Neighbor rank (1 = closest).",
            "cosine_similarity": "Cosine similarity score.",
        },
        "example_row": "Educational Example: U_A · U_B · P001 · P002 · rank 1 · 0.98",
    },
    "Stable Patterns": {
        "description": "Patterns with consistently high average similarity to neighbors.",
        "columns": {
            "rank": "Rank by average similarity (descending).",
            "pattern_id": "Test pattern identifier.",
            "average_similarity": "Mean similarity across neighbor pairs.",
        },
        "example_row": "Educational Example: rank 1 · P001 · 0.97 avg similarity",
    },
    "Divergent Patterns": {
        "description": "Patterns with lower average similarity — structurally distinct.",
        "columns": {
            "rank": "Rank by average similarity (ascending).",
            "pattern_id": "Test pattern identifier.",
            "average_similarity": "Mean similarity across neighbor pairs.",
        },
        "example_row": "Educational Example: rank 1 · P099 · 0.42 avg similarity",
    },
    "Top Failing Pattern Outcomes": {
        "description": "Pattern×chain outcomes with failure concentration.",
        "columns": {
            "pattern_id": "Test pattern identifier.",
            "scan_chain_id": "Scan chain identifier.",
            "latest_result": "Most recent PASS or FAIL.",
            "pass_count": "Total passing executions.",
            "fail_count": "Total failing executions.",
            "execution_count": "Total executions.",
            "lot_count": "Number of LOTs where this pattern ran.",
            "cross_lot": "Whether the pattern appears in multiple LOTs.",
        },
        "example_row": "Educational Example: P042 · CH1 · FAIL · 2 pass · 8 fail · 3 LOTs",
    },
    "Requirement Completion": {
        "description": "Checklist of pipeline requirement completion statuses.",
        "columns": {
            "phase": "Pipeline requirement identifier.",
            "status": "Complete, Partial, or Missing.",
        },
        "example_row": "Educational Example: phase_4_toggle · Complete",
    },
    "Artifact Provenance": {
        "description": "Cryptographic inventory of all session artifacts for audit.",
        "columns": {
            "logical_name": "Semantic role of the artifact.",
            "artifact_filename": "On-disk JSON filename.",
            "status": "Whether the artifact was loaded successfully.",
            "generated_by": "Pipeline module that produced the artifact.",
            "version": "Artifact schema version.",
            "sha256": "SHA-256 content hash.",
            "generation_timestamp": "When the artifact was written.",
        },
        "example_row": "Educational Example: manifest · PA-Analysis-Session_manifest.json · Complete",
    },
}


def get_section_guide(section_id: str) -> SectionGuide:
    return dict(SECTION_GUIDES.get(section_id, {}))


def get_kpi_tooltip(label: str) -> str:
    return KPI_TOOLTIPS.get(label, "")


def get_chart_guide(chart_title: str) -> Dict[str, str]:
    return dict(CHART_GUIDES.get(chart_title, {}))


def get_table_guide(table_title: str) -> Dict[str, Any]:
    return dict(TABLE_GUIDES.get(table_title, {}))


def _kpi_map(kpis: Sequence[Mapping[str, Any]]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for item in kpis:
        if not isinstance(item, Mapping):
            continue
        label = str(item.get("label") or "")
        display = str(item.get("display") or "—")
        if label:
            result[label] = display
    return result


def _clause(display: str) -> bool:
    return bool(display) and display != "—"


def build_observation(
    section_id: str,
    kpis: Sequence[Mapping[str, Any]],
    tables: Sequence[Mapping[str, Any]] = (),
) -> str:
    """Build a factual Key Observation from existing KPI display strings."""
    k = _kpi_map(kpis)
    parts: List[str] = []

    if section_id == "overview":
        if _clause(k.get("Patterns", "")):
            parts.append(f"This session analyzes {k['Patterns']} patterns.")
        if _clause(k.get("ATE Logs", "")):
            parts.append(f"{k['ATE Logs']} ATE logs are included across {k.get('LOTs', '—')} LOTs.")
        elif _clause(k.get("LOTs", "")):
            parts.append(f"Data spans {k['LOTs']} manufacturing lots.")
        if _clause(k.get("Completion %", "")):
            parts.append(f"Pipeline completion is {k['Completion %']}%.")
        if _clause(k.get("Engineering Status", "")):
            parts.append(f"Engineering status: {k['Engineering Status']}.")

    elif section_id == "session_summary":
        if _clause(k.get("Toggle Coverage Avg %", "")):
            parts.append(f"Average toggle coverage across the session is {k['Toggle Coverage Avg %']}%.")
        if _clause(k.get("Clusters", "")):
            parts.append(f"{k['Clusters']} embedding clusters were identified.")
        if _clause(k.get("Redundancy Candidates", "")):
            parts.append(f"{k['Redundancy Candidates']} redundancy candidates flagged for review.")
        if _clause(k.get("FAIL Outcomes", "")):
            parts.append(f"{k['FAIL Outcomes']} patterns have failing outcomes.")

    elif section_id == "requirement_1_ingestion":
        if _clause(k.get("STIL File", "")):
            parts.append(f"STIL source file: {k['STIL File']}.")
        if _clause(k.get("ATE Logs", "")):
            parts.append(f"{k['ATE Logs']} ATE logs ingested across {k.get('LOTs', '—')} LOTs.")
        elif _clause(k.get("LOTs", "")):
            parts.append(f"Ingest spans {k['LOTs']} manufacturing lots.")

    elif section_id == "requirement_2_vectors":
        if _clause(k.get("Scan Vectors", "")):
            parts.append(f"{k['Scan Vectors']} scan vectors reconstructed.")

    elif section_id == "requirement_3_metadata":
        if _clause(k.get("Patterns", "")):
            parts.append(f"Session metadata covers {k['Patterns']} patterns.")
        if _clause(k.get("Execution Records", "")):
            parts.append(f"{k['Execution Records']} execution records in summary scope.")
        if _clause(k.get("Pattern×Chain Keys", "")):
            parts.append(f"{k['Pattern×Chain Keys']} pattern×chain summary keys available.")

    elif section_id == "requirement_4_toggle":
        if _clause(k.get("Coverage Avg %", "")):
            parts.append(f"Average toggle coverage is {k['Coverage Avg %']}%.")
        if _clause(k.get("Coverage Min %", "")) and _clause(k.get("Coverage Max %", "")):
            parts.append(
                f"Coverage ranges from {k['Coverage Min %']}% (min) to {k['Coverage Max %']}% (max)."
            )
        if _clause(k.get("Density Avg %", "")):
            parts.append(f"Average toggle density is {k['Density Avg %']}%.")
        if _clause(k.get("PASS", "")) and _clause(k.get("FAIL", "")):
            parts.append(f"Executions: {k['PASS']} PASS, {k['FAIL']} FAIL.")
        if _clause(k.get("Execution Records", "")):
            parts.append(f"{k['Execution Records']} execution records in scope.")

    elif section_id == "embeddings":
        embedded = k.get("Embeddings", "—")
        skipped = k.get("Skipped", "—")
        if _clause(embedded):
            parts.append(f"{embedded} units were embedded.")
        if _clause(skipped) and skipped not in ("0", "0.0"):
            parts.append(f"{skipped} units were skipped.")
        if _clause(k.get("Dimension", "")):
            parts.append(f"Embedding dimension is {k['Dimension']}.")

    elif section_id == "clustering":
        if _clause(k.get("Clusters", "")) and _clause(k.get("Units", "")):
            parts.append(f"{k['Units']} units grouped into {k['Clusters']} clusters.")
        if _clause(k.get("Average Size", "")):
            parts.append(f"Average cluster size is {k['Average Size']}.")
        if _clause(k.get("Singletons", "")):
            parts.append(f"{k['Singletons']} singleton clusters.")

    elif section_id == "redundancy":
        if _clause(k.get("Candidates", "")):
            parts.append(f"{k['Candidates']} redundancy candidate pairs identified.")
        if _clause(k.get("Units Represented", "")):
            parts.append(f"{k['Units Represented']} distinct units are represented.")

    elif section_id == "similarity":
        if _clause(k.get("Pairs", "")):
            parts.append(f"{k['Pairs']} similarity pairs stored.")
        if _clause(k.get("Average Similarity", "")):
            parts.append(f"Average cosine similarity is {k['Average Similarity']}.")
        if _clause(k.get("Max Similarity", "")):
            parts.append(f"Maximum similarity observed is {k['Max Similarity']}.")

    elif section_id == "pattern_outcomes":
        if _clause(k.get("PASS", "")) and _clause(k.get("FAIL", "")):
            parts.append(f"Outcomes: {k['PASS']} PASS, {k['FAIL']} FAIL, {k.get('Unknown', '0')} unknown.")
        if _clause(k.get("Cross-LOT Outcomes", "")):
            parts.append(f"{k['Cross-LOT Outcomes']} outcomes span multiple LOTs.")

    elif section_id == "validation":
        if _clause(k.get("Validation Status", "")):
            parts.append(f"Validation status is {k['Validation Status']}.")
        if _clause(k.get("Completion %", "")):
            parts.append(f"Completion is {k['Completion %']}%.")
        warnings = k.get("Warnings", "—")
        if _clause(warnings) and warnings not in ("0", "0.0"):
            parts.append(f"{warnings} validation warning(s) recorded.")

    elif section_id == "appendix":
        for table in tables:
            if not isinstance(table, Mapping):
                continue
            if table.get("title") == "Artifact Provenance":
                total = table.get("total_rows")
                if total is not None:
                    parts.append(f"{total} artifacts listed in the provenance inventory.")
                break

    elif section_id.startswith("anomaly"):
        if _clause(k.get("Anomalies", "")):
            parts.append(f"{k['Anomalies']} anomalies detected (advisory).")
        if _clause(k.get("Scores", "")):
            parts.append(f"{k['Scores']} scores computed at {k.get('Grain', 'pattern')} grain.")

    elif section_id.startswith("failure_risk"):
        if _clause(k.get("Predicted FAIL", "")):
            parts.append(f"{k['Predicted FAIL']} patterns predicted to fail (advisory).")

    elif section_id.startswith("root_cause"):
        if _clause(k.get("Observed FAIL", "")):
            parts.append(f"{k['Observed FAIL']} patterns with observed FAIL executions.")
        if _clause(k.get("Rankings", "")):
            parts.append(f"{k['Rankings']} investigation rankings produced.")

    elif section_id.startswith("recommendations"):
        if _clause(k.get("Recommendations", "")):
            parts.append(f"{k['Recommendations']} recommendations generated.")
        if _clause(k.get("High Priority", "")):
            parts.append(f"{k['High Priority']} are high priority.")

    return " ".join(parts)
