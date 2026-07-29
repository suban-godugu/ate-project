# 10 — User Guide

**Related:** [01 System Architecture](01_SYSTEM_ARCHITECTURE.md) · [04 API](04_API_SPECIFICATION.md) · [09 Deployment](09_DEPLOYMENT_GUIDE.md)

---

## 1. What This Product Does

The Failure Analysis Agent helps semiconductor FA and yield engineers:

1. Upload STIL and tester log data  
2. Detect failure patterns and compute rates  
3. Classify faults and find recurring issues  
4. Correlate failures to patterns  
5. Analyze die and wafer spatial trends  
6. Rank **probable** fault types (not definitive root causes)  
7. Generate and export engineering reports  

## 2. Getting Started

1. Start PostgreSQL and apply migrations ([09 Deployment](09_DEPLOYMENT_GUIDE.md)).  
2. Start the API on port **8000**.  
3. Start `ate-dashboard` on port **3000**.  
4. Open `http://localhost:3000`.  

For identity headers in production, see [07 Security](07_SECURITY_ARCHITECTURE.md). Local setups often use a default service role via the proxy.

## 3. Dashboard Map (`ate-dashboard`)

| Route | Module | What you do |
|-------|--------|-------------|
| `/` | — | Overview / home |
| `/upload` | FA-FR-001 | Drag-and-drop file upload |
| `/datasets` | FA-FR-001 | Browse datasets; server-side scan |
| `/stats` | FA-FR-001 | Ingestion / parser statistics |
| `/patterns` | FA-FR-002 | Run detection; view pattern charts |
| `/failure-rates` | FA-FR-003 | Compute rates; trends / heatmaps |
| `/recurrence` | FA-FR-005 | Recurring failures & hotspots |
| `/correlation` | FA-FR-006 | Correlation matrix / network |
| `/die-analysis` | FA-FR-007 | Die map, clusters, hotspots |
| `/wafer-analysis` | FA-FR-008 | Wafer yield, radial / edge trends |
| `/fault-prediction` | FA-FR-009 | Ranked fault hypotheses + feedback |
| `/reports` | FA-FR-010 | Generate, history, multi-format export |
| `/history` | — | Cross-run history |

**Note:** FA-FR-004 (classification) is available via API (`/api/v1/classification`) and evaluation flows; there may be no dedicated sidebar page.

## 4. Recommended Production Workflow

```mermaid
flowchart LR
  U[Upload / Dataset] --> P[Patterns]
  P --> R[Failure rates]
  R --> C[Classification API]
  C --> REC[Recurrence]
  REC --> COR[Correlation]
  COR --> D[Die]
  D --> W[Wafer]
  W --> F[Fault prediction]
  F --> REP[Reports]
```

Each production step requires **completed upstream** results for the same upload/dataset. If a step returns `422`, check lineage (run missing upstream modules first).

## 5. Interpreting AI Output

- Predictions are **probable fault types** with confidence and evidence.  
- Always review die/wafer maps and correlation before process changes.  
- Use feedback on the prediction screen to improve future scoring.  
- Reports consolidate all modules; production generation expects FA-FR-001→009 complete.

## 6. Exports

From **Reports**: PDF, HTML, CSV, XLSX, JSON (availability depends on generators installed). Downloads also exist under `/api/v1/reports/download/...` ([04 API](04_API_SPECIFICATION.md)).

## 7. Evaluation Workbench

Separate UI (`frontend/`, port 5173) for dataset evaluation, training experiments, and metric reports. It does not replace the production FA-FR dashboard. See [05 AI Architecture](05_AI_ARCHITECTURE.md).

## 8. CLI Alternatives

```powershell
python main.py --log-dir path\to\logs --stil-file path\to\file.stil
python main.py --log-dir tests/fixtures --use-adapter-ingestion --recursive
python dashboard.py
```

Useful for offline batches and acceptance fixtures.

## 9. Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `422 INVALID_*_SOURCE` | Upstream not run | Complete prior FA-FR steps |
| `403` | Role not allowed | Check `X-Role` / IdP groups |
| Empty charts | No completed analysis | Run detect/compute for that dataset |
| Migration errors | Schema drift | `alembic upgrade head` |
| Upload rejected | Type/size/security | See [06](06_PARSER_FRAMEWORK.md), [07](07_SECURITY_ARCHITECTURE.md) |

## 10. Cross-References

- Architecture overview → [01](01_SYSTEM_ARCHITECTURE.md)
- Full endpoint list → [04](04_API_SPECIFICATION.md)
- Install & ops → [09](09_DEPLOYMENT_GUIDE.md)
