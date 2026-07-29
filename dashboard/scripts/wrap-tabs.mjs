import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const componentsDir = path.join(__dirname, "../src/components");

const MODULE_MAP = {
  "scan-chain": "scan-chain",
  mbist: "mbist",
  lbist: "lbist",
  wafer: "wafer-analysis",
  "cost-intelligence": "cost-intelligence",
  alerts: "alerts",
  recommendation: "recommendation-analysis",
};

function findTabFiles(dir, acc = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) findTabFiles(full, acc);
    else if (entry.name.endsWith("Tab.tsx")) acc.push(full);
  }
  return acc;
}

function moduleFromPath(filePath) {
  const rel = path.relative(componentsDir, filePath);
  const folder = rel.split(path.sep)[0];
  return MODULE_MAP[folder];
}

function wrapFile(filePath) {
  let src = fs.readFileSync(filePath, "utf8");
  if (src.includes("TabLiveShell")) return false;

  const module = moduleFromPath(filePath);
  if (!module) {
    console.warn("Skip (no module):", filePath);
    return false;
  }

  const hookMatch = src.match(/useFiltered\w+Data\(\)/);
  if (!hookMatch) {
    console.warn("Skip (no hook):", filePath);
    return false;
  }
  const hookCall = hookMatch[0];

  if (!src.includes('from "@/components/platform/TabLiveShell"')) {
    src = src.replace(
      /("use client";\n\n)/,
      '$1import { TabLiveShell } from "@/components/platform/TabLiveShell";\n'
    );
  }

  const isDefect = filePath.includes("DefectClassTab.tsx");

  // Multiline destructuring: const { ... } = useHook();
  const multiRe = new RegExp(
    `const \\{\\s*([\\s\\S]*?)\\} = ${hookCall.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")};`
  );
  if (multiRe.test(src)) {
    src = src.replace(multiRe, `const liveData = ${hookCall};\n  const {$1} = liveData;`);
  } else {
    // Single-line split destructuring
    const splitRe = new RegExp(
      `(const \\{[\\s\\S]*?\\} =\\s*)\\n\\s*${hookCall.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")};`
    );
    if (splitRe.test(src)) {
      src = src.replace(splitRe, `const liveData = ${hookCall};\n  $1liveData;`);
    } else {
      src = src.replace(
        new RegExp(`const ([^=]+)= ${hookCall.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")};`),
        `const liveData = ${hookCall};\n  const $1= liveData;`
      );
    }
  }

  const shellOpen = isDefect
    ? `<TabLiveShell module="${module}" tab={defectClass} hookResult={liveData}>`
    : `<TabLiveShell module="${module}" hookResult={liveData}>`;

  src = src.replace(
    /return \(\s*\n(\s*)<div className="dashboard-content/,
    `return (\n$1${shellOpen}\n$1  <div className="dashboard-content`
  );

  // Close before final );
  src = src.replace(/\n(\s*)<\/div>\s*\n(\s*)\);(\s*\n\})/, `\n$1  </div>\n$1</TabLiveShell>\n$2);$3`);

  fs.writeFileSync(filePath, src);
  return true;
}

const files = findTabFiles(componentsDir);
let count = 0;
for (const f of files) {
  if (wrapFile(f)) {
    count++;
    console.log("Wrapped:", path.relative(componentsDir, f));
  }
}
console.log(`Done: ${count} files updated`);
