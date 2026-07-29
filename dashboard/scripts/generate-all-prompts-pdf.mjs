/**
 * Generates docs/VERILUMEN-ALL-PROMPTS.md and .pdf from prompts.csv + session prompts.
 * Run: node scripts/generate-all-prompts-pdf.mjs
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const bdRoot = path.resolve(root, "../../bd-1/dashboard");

function parseCsv(text) {
  const rows = [];
  let i = 0;
  const len = text.length;

  function readField() {
    let field = "";
    if (text[i] === '"') {
      i++;
      while (i < len) {
        if (text[i] === '"') {
          if (text[i + 1] === '"') {
            field += '"';
            i += 2;
          } else {
            i++;
            break;
          }
        } else {
          field += text[i++];
        }
      }
      if (text[i] === ",") i++;
    } else {
      while (i < len && text[i] !== "\n" && text[i] !== "\r") {
        if (text[i] === ",") break;
        field += text[i++];
      }
      if (text[i] === ",") i++;
    }
    return field;
  }

  const headers = [];
  while (i < len && text[i] !== "\n" && text[i] !== "\r") {
    headers.push(readField());
  }
  while (text[i] === "\n" || text[i] === "\r") i++;

  while (i < len) {
    const row = {};
    for (let h = 0; h < headers.length; h++) {
      row[headers[h]] = readField();
    }
    if (Object.values(row).some((v) => v && String(v).trim())) rows.push(row);
    while (text[i] === "\n" || text[i] === "\r") i++;
  }
  return rows;
}

/** Session prompts from KPI + build conversations (Jul 3–7, 2026) */
const SESSION_PROMPTS = [
  {
    date: "2026-07-03",
    title: "Unified Build Sequence STEP 40–53",
    body: "VERILUMEN Unified Build Sequence — merge backend + frontend prompts with dependency order. Add search, AI Diagnose, AI Optimize, recommendation feedback endpoints. Continue STEP numbering from STEP 39.",
  },
  {
    date: "2026-07-06",
    title: "Backend & Database Implementation",
    body: "VERILUMEN Backend & Database Implementation Prompt — FastAPI + SQLAlchemy + Postgres/Redis/MinIO. Phases for infra, schema, auth, uploads, dashboard APIs, workers, notifications.",
  },
  {
    date: "2026-07-06",
    title: "Frontend Integration STEP 40+",
    body: "VERILUMEN Dashboard Frontend Integration Prompt — API client, auth, module hooks, live dashboard wiring, filters, uploads, notifications, recommendation feedback, export.",
  },
  {
    date: "2026-07-06",
    title: "20 Prompts to Finish Build",
    body: "VERILUMEN 20 Prompts to Finish the Build — gap-analysis driven prompts for parser, live analytics, alert UI, RL consumer, STIL/WGL/PAT parsers, cost engine, deep analytics.",
  },
  {
    date: "2026-07-06",
    title: "P1-7 Enterprise File Parser",
    body: "P1-7 Enterprise File Parser — real STDF + LOG parsing in parse_worker.py. Do not rewrite project. Extend existing workers and models.",
  },
  {
    date: "2026-07-06",
    title: "Stage 7 Live Analytics",
    body: "Stage 7 Live Analytics & Visualization Engine — replace mock chart generators with PostgreSQL-driven analytics across all modules.",
  },
  {
    date: "2026-07-07",
    title: "Scan Debug KPI List",
    body: "List KPI cards for Recommendation Analysis → Scan Debug Recommendation Agent: Broken Chains Detected, Constraint Violations, Timing Debug, Power Debug, Defect Suspects, Investigation Recommendations, etc. (15 KPIs total).",
  },
  {
    date: "2026-07-07",
    title: "Scan Chain Overview Redesign",
    body: "Scan Chain Overview tab should be executive summary with drill-down links — not duplicate Pattern/Failure/Diagnosis sub-tabs. KPIs + health summary + trend analytics + mini KPI drill-down sections.",
  },
  {
    date: "2026-07-07",
    title: "Remove AI Detection Accuracy KPI",
    body: "Remove AI Detection Accuracy KPI card from Scan Chain Failure Analysis.",
  },
  {
    date: "2026-07-07",
    title: "KPI Same Size Audit",
    body: "Check all KPI cards are same size across complete application. Standardize all KPI cards to enterprise design system.",
  },
  {
    date: "2026-07-07",
    title: "Enterprise KPI Card Refactor",
    body: `Refactor entire KPI card system into single reusable EnterpriseKPICard component.
Apply across: Scan Chain, Pattern Recommendation, Scan Debug, Test Optimization, MBIST, LBIST, Wafer, Cost Intelligence, Dashboard, Alerts.
Card: 220px height, 100% width, 22px padding, 18px radius, #111827 bg, rgba(124,58,237,.25) border.
Grid: xl 4 cols overview, xl 3 cols section, md 2 cols, sm 1 col, 24px gap.
Identical typography, icon 48x48, badge, trend, sparkline 44px bottom. Truncate overflow. w-full h-full.`,
  },
  {
    date: "2026-07-07",
    title: "KPI Typography Standardization",
    body: `Standardize all KPI cards typography:
Title: 16px Medium #94A3B8 | Value: 44px Bold #FFFFFF line-height 48px | Subtitle: 14px Regular #64748B
Trend: 15px SemiBold green #10B981 / red #EF4444 | Badge: 12px SemiBold height 26px padding 6px 12px rounded-full
Layout: Icon 48x48 top-left, badge top-right, title, value, subtitle or trend, sparkline 44px bottom.
Apply to Dashboard, Scan Chain, MBIST, LBIST, Wafer, Cost Intelligence, Recommendation, Alerts, Settings.`,
  },
  {
    date: "2026-07-07",
    title: "KPI Text Consistency Fix",
    body: "Check complete application — KPI card text was not same in all KPI cards. Fix inconsistent value sizes and meta line styling.",
  },
  {
    date: "2026-07-07",
    title: "Fill Gaps and Save",
    body: "Check all prompts, fill gaps, save what was made — sync bd-1, commit KPI standardization work.",
  },
];

function buildMarkdown(csvRows) {
  const lines = [];
  lines.push("# VERILUMEN / COMPTY — Complete Prompt Archive");
  lines.push("");
  lines.push(`**Generated:** ${new Date().toISOString().slice(0, 10)}`);
  lines.push("");
  lines.push("**Repositories:**");
  lines.push("- Frontend (dev): `c1-com/ate-dashboard`");
  lines.push("- Frontend (sync): `bd-1/dashboard`");
  lines.push("- Backend: `bd-1/backend`");
  lines.push("");
  lines.push("---");
  lines.push("");
  lines.push("# Part A — STEP Prompt Archive (prompts.csv)");
  lines.push("");
  lines.push(`Total entries: **${csvRows.length}**`);
  lines.push("");

  for (const row of csvRows) {
    const step = row.Step || "?";
    const title = row["Prompt Title"] || "";
    const full = row["Full Prompt"] || "";
    const date = row.Date || "";
    const files = row["Generated Files"] || "";
    const components = row["Generated Components"] || "";

    lines.push(`## ${step} — ${title}`);
    if (date) lines.push(`\n**Date:** ${date}\n`);
    lines.push("### Prompt\n");
    lines.push("```text");
    lines.push(full.replace(/\r\n/g, "\n"));
    lines.push("```\n");
    if (files) lines.push(`**Files:** ${files}\n`);
    if (components) lines.push(`**Components:** ${components}\n`);
    lines.push("---\n");
  }

  lines.push("# Part B — Session Prompts (Build + KPI)\n");
  SESSION_PROMPTS.forEach((p, i) => {
    lines.push(`## Session ${i + 1} — ${p.title}`);
    lines.push(`\n**Date:** ${p.date}\n`);
    lines.push("### Prompt\n");
    lines.push("```text");
    lines.push(p.body);
    lines.push("```\n");
    lines.push("---\n");
  });

  lines.push("# Part C — Final KPI Design System (Implemented)\n");
  lines.push("| Item | Specification |");
  lines.push("|---|---|");
  lines.push("| Component | `EnterpriseKPICard.tsx` + `EnterpriseKPIGrid` |");
  lines.push("| Card height | 220px |");
  lines.push("| Padding / radius | 22px / 18px |");
  lines.push("| Background / border | `#111827` / `rgba(124,58,237,0.25)` |");
  lines.push("| Title | 16px Medium `#94A3B8` |");
  lines.push("| Value | 44px Bold `#FFFFFF`, line-height 48px |");
  lines.push("| Subtitle | 14px Regular `#64748B` |");
  lines.push("| Trend | 15px SemiBold `#10B981` / `#EF4444` |");
  lines.push("| Badge | 12px SemiBold, 26px height, 6×12px padding |");
  lines.push("| Icon | 48×48 top-left |");
  lines.push("| Sparkline | 44px bottom |");
  lines.push("| Grid overview | 4 cols @ xl, 2 @ md, 1 @ sm |");
  lines.push("| Grid section | 3 cols @ xl, 2 @ md, 1 @ sm |");
  lines.push("| Gap | 24px |");
  lines.push("");
  lines.push("**Git commits:** c1-com `bdc03e3` · bd-1/dashboard `56c8fff`");
  lines.push("");

  return lines.join("\n");
}

function markdownToPdf(mdPath, pdfPath) {
  const py = path.join(__dirname, "markdown-to-pdf.py");
  execSync(`python "${py}" "${mdPath}" "${pdfPath}"`, { stdio: "inherit", timeout: 180000 });
}

function main() {
  const csvRows = parseCsv(fs.readFileSync(path.join(root, "prompts.csv"), "utf8"));
  const markdown = buildMarkdown(csvRows);

  for (const base of [root, bdRoot]) {
    const docsDir = path.join(base, "docs");
    fs.mkdirSync(docsDir, { recursive: true });
    const mdPath = path.join(docsDir, "VERILUMEN-ALL-PROMPTS.md");
    const pdfPath = path.join(docsDir, "VERILUMEN-ALL-PROMPTS.pdf");
    fs.writeFileSync(mdPath, markdown, "utf8");
    console.log("Wrote:", mdPath);
    try {
      markdownToPdf(mdPath, pdfPath);
    } catch (e) {
      console.error("PDF failed for", base, e.message);
    }
  }
}

main();
