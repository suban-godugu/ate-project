/**
 * Serve Vite `dist/` under /embed/test-opt without directory listings.
 * Maps /embed/test-opt/* -> dist/* and SPA-fallbacks to index.html.
 * Proxies /embed/test-opt/api-proxy/* -> Test Optimization API (Render).
 */
import http from "node:http";
import https from "node:https";
import { createReadStream, existsSync, statSync } from "node:fs";
import { extname, join, dirname, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const distRoot = join(root, "dist");
const BASE = "/embed/test-opt";
const PROXY_PREFIX = `${BASE}/api-proxy`;
const port = Number(process.env.PORT || 3043);
const apiTarget = (
  process.env.API_PROXY_TARGET ||
  process.env.TEST_OPT_API_URL ||
  "https://ate-topt-api.onrender.com"
).replace(/\/$/, "");

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

function proxyApi(req, res) {
  const qs = (req.url || "").includes("?") ? `?${(req.url || "").split("?")[1]}` : "";
  const pathOnly = (req.url || "").split("?")[0];
  const upstreamPath = pathOnly.slice(PROXY_PREFIX.length) || "/";
  const targetUrl = new URL(
    `${upstreamPath.startsWith("/") ? upstreamPath : `/${upstreamPath}`}${qs}`,
    `${apiTarget}/`,
  );

  const transport = targetUrl.protocol === "https:" ? https : http;
  const headers = { ...req.headers, host: targetUrl.host };
  delete headers["accept-encoding"];

  const upstream = transport.request(
    targetUrl,
    { method: req.method, headers },
    (upRes) => {
      res.writeHead(upRes.statusCode || 502, upRes.headers);
      upRes.pipe(res);
    },
  );

  upstream.on("error", (err) => {
    res.writeHead(502, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ message: `API proxy error: ${err.message}` }));
  });

  req.pipe(upstream);
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

    if (urlPath === PROXY_PREFIX || urlPath.startsWith(`${PROXY_PREFIX}/`)) {
      proxyApi(req, res);
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

    sendIndex(res);
  })
  .listen(port, "0.0.0.0", () => {
    console.log(`test-opt UI on http://0.0.0.0:${port}${BASE}/`);
    console.log(`api proxy ${PROXY_PREFIX} -> ${apiTarget}`);
  });
