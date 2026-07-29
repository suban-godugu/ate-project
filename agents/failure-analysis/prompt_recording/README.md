# prompt_recording — Technical AI Agent Specifications

## Purpose

This folder holds **regenerated Technical AI Agent Specifications** derived from Functional Requirements **FA-FR-001 through FA-FR-010** for the Semiconductor Failure Analysis AI Agent.

Documents follow the structure of **Technical_AI_Agent_Specification_Template.docx** (28 mandatory sections, exact heading order).

These files are **documentation only**. They do not replace or modify application source code, APIs, databases, or the existing `docs/` architecture set.

## Folder Structure

```text
prompt_recording/
├── README.md                                              ← this file
├── MASTER_INDEX.md                                        ← navigation & revision history
├── FA-FR-001_Technical_AI_Agent_Specification.md          ← Test Data Ingestion
├── FA-FR-002_Technical_AI_Agent_Specification.md          ← Failure Pattern Detection
├── FA-FR-003_Technical_AI_Agent_Specification.md          ← Failure Rate Computation
├── FA-FR-004_Technical_AI_Agent_Specification.md          ← Fault Classification
├── FA-FR-005_Technical_AI_Agent_Specification.md          ← Recurring Failure Identification
├── FA-FR-006_Technical_AI_Agent_Specification.md          ← Failure-to-Pattern Correlation
├── FA-FR-007_Technical_AI_Agent_Specification.md          ← Die-Level Failure Analysis
├── FA-FR-008_Technical_AI_Agent_Specification.md          ← Wafer-Level Failure Analysis
├── FA-FR-009_Technical_AI_Agent_Specification.md          ← AI-Based Fault Type Prediction
└── FA-FR-010_Technical_AI_Agent_Specification.md          ← Enterprise Failure Analysis Reporting
```

## Naming Convention

| Pattern | Meaning |
|---------|---------|
| `FA-FR-NNN_Technical_AI_Agent_Specification.md` | One complete technical specification per functional requirement |
| `MASTER_INDEX.md` | Cross-document index and revision history |
| `README.md` | Folder purpose and usage guide |

Version identifiers appear inside each document under **Document Information** and **Approval**.

## How These Documents Should Be Used

| Audience | Use |
|----------|-----|
| Enterprise Architecture | Capability and NFR review |
| Technical Design Review | API, schema, workflow, and AI behavior |
| AI Review Board | Reasoning strategy, confidence, fallbacks, hallucination controls |
| Development Team | Implementation-ready contracts and rules |
| QA | Test cases and acceptance criteria |
| DevOps | Logging, monitoring, security, constraints |
| Customer / Production | Formal specification package |

**Recommended workflow:** Read `MASTER_INDEX.md` → open the relevant FA-FR specification → use Traceability Matrix and Reviewer Checklist for sign-off.

## Relationship: Functional Requirements ↔ Technical AI Specifications

| Functional Requirement (intent) | Technical AI Agent Specification (this folder) |
|---------------------------------|------------------------------------------------|
| States *what* the system must do | States *how* the agent is designed, constrained, integrated, tested, and operated |
| FR ID, description, priority | Full 28-section enterprise template |
| Business outcome | Architecture, API, DB, AI behavior, dashboard, security, AC |

Pipeline lineage (production path):

```text
FA-FR-001 → 002 → 003 → 004 → 005 → 006 → 007 → 008 → 009 → 010
```

Each specification documents its module as a bounded AI/analytics agent within that lineage. Upstream gates and append-only persistence are mandatory on the production path.

## Technology Stack (shared)

Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS v4, ShadCN UI, React Query, Zustand, Framer Motion, Recharts  

Backend: Python 3.13, FastAPI, SQLAlchemy, AsyncIO, Pydantic, Alembic  

Data: PostgreSQL · MinIO · Redis  

AI: OpenAI GPT, Prompt Engineering, Rule Engine, Hybrid AI + Deterministic Logic  

Quality / Deploy: Pytest, Benchmark Framework, Docker, Kubernetes, GitHub Actions

## Integrity Rules for This Folder

- Create **new** Markdown files only under `prompt_recording/`.
- Do **not** modify application source, APIs, models, configs, or existing `docs/` as part of maintaining these specs unless a separate change request is approved.
- Specs must remain aligned with FA-FR intent; do not silently alter functional requirements.

## Template Compliance

Every `FA-FR-NNN_Technical_AI_Agent_Specification.md` contains sections **1–28** in this exact order:

1. Document Information  
2. Project Overview  
3. Business Objective  
4. Technical Overview  
5. Technology Stack  
6. Agent Responsibilities  
7. Functional Requirements  
8. Non-Functional Requirements  
9. AI Behavior Specification  
10. Input Specification  
11. Output Specification  
12. Business Rules  
13. Key Engineering Rules  
14. Constraints  
15. API Specification  
16. Database Design  
17. Dashboard Integration  
18. AI Workflow  
19. Error Handling  
20. Logging & Monitoring  
21. Security  
22. Test Cases  
23. Acceptance Criteria  
24. Risks & Assumptions  
25. Dependencies  
26. Traceability Matrix  
27. Reviewer Checklist  
28. Approval  
