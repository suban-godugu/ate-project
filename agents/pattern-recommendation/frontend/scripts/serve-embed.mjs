/**
 * Serve Vite dist under /embed/pattern-rec/ so asset URLs resolve on Render.
 */
import { cpSync, mkdirSync, rmSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const dist = join(root, "dist");
const staged = join(root, ".render-dist");
const embedDir = join(staged, "embed", "pattern-rec");
const port = process.env.PORT || "3041";

if (!existsSync(dist)) {
  console.error("dist/ missing — run npm run build first");
  process.exit(1);
}

rmSync(staged, { recursive: true, force: true });
mkdirSync(embedDir, { recursive: true });
cpSync(dist, embedDir, { recursive: true });

const child = spawn(
  "npx",
  ["serve", "-s", staged, "-l", String(port)],
  { stdio: "inherit", cwd: root, shell: true },
);

child.on("exit", (code) => process.exit(code ?? 1));
