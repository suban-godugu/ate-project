/**
 * Serve Vite `dist/` under /embed/pattern-rec without directory listings.
 * Maps /embed/pattern-rec/* -> dist/* and SPA-fallbacks to index.html.
 */
import http from "node:http";
import { createReadStream, existsSync, statSync } from "node:fs";
import { extname, join, dirname, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const distRoot = join(root, "dist");
const BASE = "/embed/pattern-rec";
const port = Number(process.env.PORT || 3041);

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".json": "application/json",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".map": "application/json",
};

function sendFile(res, filePath) {
  const type = MIME[extname(filePath).toLowerCase()] || "application/octet-stream";
  res.writeHead(200, { "Content-Type": type, "Cache-Control": "public, max-age=60" });
  createReadStream(filePath).pipe(res);
}

function sendIndex(res) {
  sendFile(res, join(distRoot, "index.html"));
}

if (!existsSync(join(distRoot, "index.html"))) {
  console.error("dist/index.html missing — run npm run build first");
  process.exit(1);
}

http
  .createServer((req, res) => {
    const raw = (req.url || "/").split("?")[0];
    let urlPath = decodeURIComponent(raw);

    if (urlPath === "/" || urlPath === "") {
      res.writeHead(302, { Location: `${BASE}/` });
      res.end();
      return;
    }

    if (!urlPath.startsWith(BASE)) {
      res.writeHead(404, { "Content-Type": "text/plain" });
      res.end("Not found");
      return;
    }

    let rel = urlPath.slice(BASE.length) || "/";
    if (rel === "" || rel === "/") {
      sendIndex(res);
      return;
    }
    if (rel.endsWith("/")) {
      rel = `${rel}index.html`;
    }

    const candidate = normalize(join(distRoot, rel.replace(/^\//, "")));
    if (!candidate.startsWith(distRoot)) {
      res.writeHead(403).end("Forbidden");
      return;
    }

    if (existsSync(candidate) && statSync(candidate).isFile()) {
      sendFile(res, candidate);
      return;
    }

    // SPA fallback (never list directories)
    sendIndex(res);
  })
  .listen(port, "0.0.0.0", () => {
    console.log(`pattern-rec UI on http://0.0.0.0:${port}${BASE}/`);
  });
