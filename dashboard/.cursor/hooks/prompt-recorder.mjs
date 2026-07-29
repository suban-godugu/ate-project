import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const HOOKS_DIR = __dirname;
const STATE_FILE = path.join(HOOKS_DIR, ".session-state.json");

const CSV_HEADER =
  "Step,Date,Prompt Title,Full Prompt,Generated Files,Generated Components";
const README_INSERT_BEFORE = "## Design Tokens";
const SKIP_PATH_PREFIXES = [
  ".cursor/hooks/.session-state.json",
  ".cursor/hooks/.pending-prompt.json",
  "node_modules/",
  ".next/",
];

export function findProjectRoot(hookInput = {}) {
  const candidates = [];

  if (Array.isArray(hookInput.workspace_roots)) {
    candidates.push(...hookInput.workspace_roots);
  }

  candidates.push(process.cwd());
  candidates.push(path.resolve(HOOKS_DIR, "../.."));
  candidates.push(path.resolve(HOOKS_DIR, "../../.."));

  for (const root of candidates) {
    if (!root) continue;
    const normalized = path.resolve(root);
    if (fs.existsSync(path.join(normalized, "prompts.csv"))) {
      return normalized;
    }
    const nested = path.join(normalized, "ate-dashboard");
    if (fs.existsSync(path.join(nested, "prompts.csv"))) {
      return nested;
    }
  }

  return path.resolve(HOOKS_DIR, "../..");
}

export function loadSessionState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      return JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
    }
  } catch {
    // ignore corrupt state
  }
  return null;
}

export function saveSessionState(state) {
  fs.mkdirSync(HOOKS_DIR, { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), "utf8");
}

export function clearSessionState() {
  if (fs.existsSync(STATE_FILE)) {
    fs.unlinkSync(STATE_FILE);
  }
}

function escapeCsv(value) {
  const text = String(value ?? "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function parseCsvLine(line) {
  const fields = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (inQuotes) {
      if (char === '"') {
        if (line[i + 1] === '"') {
          current += '"';
          i += 1;
        } else {
          inQuotes = false;
        }
      } else {
        current += char;
      }
    } else if (char === '"') {
      inQuotes = true;
    } else if (char === ",") {
      fields.push(current);
      current = "";
    } else {
      current += char;
    }
  }

  fields.push(current);
  return fields;
}

function formatCsvRow(fields) {
  return fields.map(escapeCsv).join(",");
}

export function getNextStepId(projectRoot) {
  const csvPath = path.join(projectRoot, "prompts.csv");
  if (!fs.existsSync(csvPath)) {
    return "STEP 1";
  }

  const content = fs.readFileSync(csvPath, "utf8");
  let maxStep = 0;

  for (const line of content.split(/\r?\n/)) {
    const match = line.match(/^STEP\s+(\d+),/i);
    if (match) {
      maxStep = Math.max(maxStep, Number(match[1]));
    }
  }

  return `STEP ${maxStep + 1}`;
}

export function deriveTitle(prompt) {
  const firstLine = prompt
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find(Boolean);

  if (!firstLine) return "Untitled Prompt";

  const cleaned = firstLine
    .replace(/^cursor ai prompt\s*[–-]\s*/i, "")
    .replace(/^#+\s*/, "")
    .trim();

  if (cleaned.length <= 80) return cleaned;
  return `${cleaned.slice(0, 77).trim()}...`;
}

export function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

export function shouldSkipPrompt(prompt) {
  const trimmed = String(prompt ?? "").trim();
  if (!trimmed) return true;
  if (trimmed.length < 3) return true;
  return false;
}

export function isDuplicatePrompt(projectRoot, prompt) {
  const csvPath = path.join(projectRoot, "prompts.csv");
  if (!fs.existsSync(csvPath)) return false;

  const lines = fs.readFileSync(csvPath, "utf8").split(/\r?\n/).filter(Boolean);
  if (lines.length <= 1) return false;

  const lastLine = lines[lines.length - 1];
  const fields = parseCsvLine(lastLine);
  const lastPrompt = fields[3] ?? "";
  return lastPrompt.trim() === prompt.trim();
}

export function inferComponents(files) {
  const names = new Set();

  for (const file of files) {
    const base = path.basename(file, path.extname(file));
    if (base.endsWith("Tab")) names.add(base);
    else if (/^[A-Z]/.test(base)) names.add(base);
  }

  return Array.from(names).slice(0, 12).join(" ");
}

export function normalizeTrackedPath(projectRoot, filePath) {
  const relative = path
    .relative(projectRoot, filePath)
    .replace(/\\/g, "/");

  if (!relative || relative.startsWith("..")) return null;

  for (const prefix of SKIP_PATH_PREFIXES) {
    if (relative.startsWith(prefix) || relative.includes(`/${prefix}`)) {
      return null;
    }
  }

  if (relative === "prompts.csv" || relative === "README.md") {
    return null;
  }

  return relative;
}

export function appendPromptRecord(projectRoot, { stepId, date, title, prompt }) {
  const csvPath = path.join(projectRoot, "prompts.csv");
  const row = formatCsvRow([
    stepId,
    date,
    title,
    prompt.trim(),
    "",
    "",
  ]);

  if (!fs.existsSync(csvPath)) {
    fs.writeFileSync(csvPath, `${CSV_HEADER}\n${row}\n`, "utf8");
  } else {
    fs.appendFileSync(csvPath, `${row}\n`, "utf8");
  }

  appendReadmeEntry(projectRoot, { stepId, title, prompt, date });
}

export function appendReadmeEntry(projectRoot, { stepId, title, prompt, date }) {
  const readmePath = path.join(projectRoot, "README.md");
  if (!fs.existsSync(readmePath)) return;

  const entry = [
    "",
    `### ${stepId} — ${title}`,
    "",
    `_Auto-recorded on ${date}_`,
    "",
    "```",
    prompt.trim(),
    "```",
    "",
  ].join("\n");

  let content = fs.readFileSync(readmePath, "utf8");
  const marker = "<!-- PROMPT_ARCHIVE_END -->";

  if (content.includes(marker)) {
    content = content.replace(marker, `${entry}${marker}`);
  } else if (content.includes(README_INSERT_BEFORE)) {
    content = content.replace(README_INSERT_BEFORE, `${entry}${README_INSERT_BEFORE}`);
  } else {
    content += `\n${entry}`;
  }

  fs.writeFileSync(readmePath, content, "utf8");
}

export function updatePromptArtifacts(projectRoot, stepId, files) {
  const csvPath = path.join(projectRoot, "prompts.csv");
  if (!fs.existsSync(csvPath)) return;

  const lines = fs.readFileSync(csvPath, "utf8").split(/\r?\n/);
  const header = lines[0];
  const dataLines = lines.slice(1).filter(Boolean);
  const fileList = files.join("; ");
  const components = inferComponents(files);

  for (let i = dataLines.length - 1; i >= 0; i -= 1) {
    const fields = parseCsvLine(dataLines[i]);
    if (fields[0] === stepId) {
      fields[4] = fileList;
      fields[5] = components;
      dataLines[i] = formatCsvRow(fields);
      break;
    }
  }

  fs.writeFileSync(csvPath, [header, ...dataLines, ""].join("\n"), "utf8");
}

export function trackEditedFile(projectRoot, filePath) {
  const relative = normalizeTrackedPath(projectRoot, filePath);
  if (!relative) return;

  const state = loadSessionState();
  if (!state?.stepId) return;

  const files = new Set(state.files ?? []);
  files.add(relative);
  saveSessionState({ ...state, files: Array.from(files) });
}
