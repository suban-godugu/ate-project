# Master Index — Technical AI Agent Specifications

**Project:** Semiconductor Failure Analysis AI Agent  
**Package:** `prompt_recording/`  
**Template:** Technical AI Agent Specification Template (28 sections)  
**Version:** 1.0  
**Date:** 2026-07-17  

---

## 1. Project Overview

The Semiconductor Failure Analysis AI Agent is an enterprise engineering platform that:

1. Ingests and validates STIL and semiconductor tester logs (FA-FR-001)  
2. Detects failure patterns (FA-FR-002)  
3. Computes multi-level failure rates (FA-FR-003)  
4. Classifies fault types (FA-FR-004)  
5. Identifies recurring failures (FA-FR-005)  
6. Correlates failures to patterns (FA-FR-006)  
7. Performs die-level spatial analysis (FA-FR-007)  
8. Performs wafer-level yield and spatial analysis (FA-FR-008)  
9. Predicts probable fault types with explainable confidence (FA-FR-009)  
10. Generates enterprise engineering reports and exports (FA-FR-010)  

Production analytics are **lineage-gated** and **append-only**. AI assists engineering judgment; it does not replace validated root-cause laboratory conclusions.

---

## 2. Document Catalog

| # | Document | Agent / Capability | Short Description |
|---|----------|--------------------|-------------------|
| 00 | [README.md](README.md) | Folder guide | Purpose, naming, usage, FR↔spec relationship |
| — | [MASTER_INDEX.md](MASTER_INDEX.md) | Index | This navigation and revision history |
| 01 | [FA-FR-001_Technical_AI_Agent_Specification.md](FA-FR-001_Technical_AI_Agent_Specification.md) | Test Data Ingestion Engine | Upload, parse, validate, normalize, store STIL/logs |
| 02 | [FA-FR-002_Technical_AI_Agent_Specification.md](FA-FR-002_Technical_AI_Agent_Specification.md) | Failure Pattern Detection Engine | Detect and rank failing scan/test patterns |
| 03 | [FA-FR-003_Technical_AI_Agent_Specification.md](FA-FR-003_Technical_AI_Agent_Specification.md) | Failure Rate Computation Engine | Device/lot/wafer/pattern failure rates and trends |
| 04 | [FA-FR-004_Technical_AI_Agent_Specification.md](FA-FR-004_Technical_AI_Agent_Specification.md) | Fault Classification Engine | Taxonomy-driven / hybrid fault type classification |
| 05 | [FA-FR-005_Technical_AI_Agent_Specification.md](FA-FR-005_Technical_AI_Agent_Specification.md) | Recurring Failure Identification Engine | Cross-lot/recurrence signatures and hotspots |
| 06 | [FA-FR-006_Technical_AI_Agent_Specification.md](FA-FR-006_Technical_AI_Agent_Specification.md) | Failure-to-Pattern Correlation Engine | Statistical correlation matrix and relationship graph |
| 07 | [FA-FR-007_Technical_AI_Agent_Specification.md](FA-FR-007_Technical_AI_Agent_Specification.md) | Die-Level Failure Analysis Engine | Per-die health, clusters, hotspots, disposition |
| 08 | [FA-FR-008_Technical_AI_Agent_Specification.md](FA-FR-008_Technical_AI_Agent_Specification.md) | Wafer-Level Failure Analysis Engine | Yield, radial/edge-center, wafer maps |
| 09 | [FA-FR-009_Technical_AI_Agent_Specification.md](FA-FR-009_Technical_AI_Agent_Specification.md) | AI-Based Fault Type Prediction Engine | Ranked probable faults, confidence, feedback |
| 10 | [FA-FR-010_Technical_AI_Agent_Specification.md](FA-FR-010_Technical_AI_Agent_Specification.md) | Enterprise Reporting Engine | Template reports, benchmarks, multi-format export |

---

## 3. Navigation Index (by Concern)

| Concern | Primary Documents |
|---------|-------------------|
| Ingestion & parsers | FA-FR-001 |
| Patterns & rates | FA-FR-002, FA-FR-003 |
| Classification & recurrence | FA-FR-004, FA-FR-005 |
| Correlation & spatial | FA-FR-006, FA-FR-007, FA-FR-008 |
| AI prediction | FA-FR-009 |
| Reporting & decision support | FA-FR-010 |
| Security / NFR (all) | Sections 8, 20, 21 in each document |
| Test & acceptance (all) | Sections 22–23 in each document |

---

## 4. Pipeline Dependency Map

```text
001 Ingestion
 └── 002 Pattern Detection
      └── 003 Failure Rates
           └── 004 Classification
                └── 005 Recurrence
                     └── 006 Correlation
                          └── 007 Die Analysis
                               └── 008 Wafer Analysis
                                    └── 009 Fault Prediction
                                         └── 010 Reporting
```

---

## 5. Shared Stack Reference

| Layer | Technologies |
|-------|----------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, ShadCN UI, React Query, Zustand, Framer Motion, Recharts |
| Backend | Python 3.13, FastAPI, SQLAlchemy, AsyncIO, Pydantic, Alembic |
| Database | PostgreSQL |
| AI | OpenAI GPT, Prompt Engineering, Rule Engine, Hybrid AI + Deterministic Logic |
| Storage / Cache | MinIO, Redis |
| Test / Deploy | Pytest, Benchmark Framework, Docker, Kubernetes, GitHub Actions |

---

## 6. Revision History

| Version | Date | Author Role | Description |
|---------|------|-------------|-------------|
| 1.0 | 2026-07-17 | Principal Enterprise AI Architect | Initial generation of all FA-FR-001…010 Technical AI Agent Specifications into `prompt_recording/` per uploaded template |

---

## 7. Review Status

| Gate | Status |
|------|--------|
| Template structure (28 sections) | Required on every FA-FR doc |
| Enterprise Architecture Review | Pending stakeholder sign-off |
| Technical Design Review | Pending stakeholder sign-off |
| AI Review Board | Pending stakeholder sign-off |
| QA / Production Readiness | Pending stakeholder sign-off |

See section **28. Approval** inside each FA-FR document for individual sign-off blocks.
