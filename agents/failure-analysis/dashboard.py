"""Local web dashboard for the Failure Analysis Agent.

Pure standard-library (no external dependencies). Lets you point the agent at a
log directory + STIL file, run the full analysis, and visually inspect the
accuracy/efficiency and complete output analysis in the browser.

Usage:
    # Prefer FastAPI on :8000; this UI defaults to :8050 to avoid port clashes.
    python dashboard.py
    python dashboard.py --port 8080
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from evaluation.data_roots import default_stil_file, primary_dataset_root

# Always resolve from this file — never from the caller's terminal cwd.
PROJECT_ROOT = Path(__file__).resolve().parent
MAIN_SCRIPT = PROJECT_ROOT / "main.py"
REPORT_PATH = PROJECT_ROOT / "failure_analysis_report.json"
DASHBOARD_PATH = PROJECT_ROOT / "dashboard_data.json"

# Back-compat alias used elsewhere in this module.
BASE_DIR = PROJECT_ROOT

DEFAULT_API_BASE = os.getenv("FA_API_BASE", "http://127.0.0.1:8000")
DEFAULT_API_PORT = int(os.getenv("FA_API_PORT", "8000"))

_resolved_root = primary_dataset_root()
DEFAULT_LOG_DIR = str(_resolved_root) if _resolved_root else ""
_stil = default_stil_file(_resolved_root)
DEFAULT_STIL_FILE = str(_stil) if _stil else ""

_run_lock = threading.Lock()
_run_state: dict = {
    "running": False,
    "returncode": None,
    "log": "",
    "started_at": None,
    "finished_at": None,
    "elapsed_s": None,
}


def _api_port_from_base(api_base: str) -> int:
    parsed = urlparse(api_base)
    if parsed.port:
        return int(parsed.port)
    return 443 if parsed.scheme == "https" else DEFAULT_API_PORT


def _backend_healthy(health_url: str) -> bool:
    """Return True only for a live FastAPI /health response."""
    try:
        with urllib.request.urlopen(health_url, timeout=2) as resp:
            if resp.status != 200:
                return False
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                return False
            return payload.get("status") == "ok" and "failure-analysis" in str(
                payload.get("service", "")
            )
    except Exception:  # noqa: BLE001
        return False


def _start_uvicorn(api_port: int) -> subprocess.Popen:
    """Start FastAPI from the project root (absolute interpreter + cwd)."""
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(PROJECT_ROOT)
        if not existing
        else os.pathsep.join([str(PROJECT_ROOT), existing])
    )
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(api_port),
        ],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_main_script(log_dir: str, stil_file: str, recursive: bool) -> tuple[int, str]:
    """
    Offline CLI fallback. Always uses an absolute path to main.py and sets
    cwd=PROJECT_ROOT so the launch never depends on the terminal working directory.
    """
    if not MAIN_SCRIPT.is_file():
        raise FileNotFoundError(f"main.py not found at {MAIN_SCRIPT}")

    cmd = [sys.executable, str(MAIN_SCRIPT)]
    if log_dir:
        cmd.extend(["--log-dir", log_dir])
    if stil_file:
        cmd.extend(["--stil-file", stil_file])
    if recursive:
        cmd.append("--recursive")

    completed = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, out


def _infer_dataset_id(log_dir: str, stil_file: str) -> str | None:
    """Best-effort dataset_id for the evaluation API from path names."""
    haystack = f"{log_dir} {stil_file}".lower().replace("\\", "/")
    if "1000" in haystack:
        return "Production_SCAN_stuck_at_1000pat"
    if "2000" in haystack:
        return "Production_SCAN_stuck_at_2000pat"
    if "full" in haystack:
        return "Production_SCAN_stuck_at_Full"
    if "29642" in haystack:
        return "scale_29642"
    if "29625" in haystack:
        return "scale_29625"
    return None


def _post_evaluation_run(run_url: str, log_dir: str, stil_file: str) -> tuple[int, str]:
    """Call the analysis API. Prefer this whenever the backend is healthy."""
    payload = json.dumps(
        {
            "dataset_id": _infer_dataset_id(log_dir, stil_file),
            "modules": None,
            "max_logs": 30,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        run_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return (0 if resp.status == 200 else int(resp.status)), body


def _run_agent(log_dir: str, stil_file: str, recursive: bool) -> None:
    """
    Run Analysis workflow:

    1. If FastAPI is already healthy on FA_API_BASE (:8000 by default), call the
       evaluation/analysis API — do **not** spawn another backend or main.py.
    2. If the backend is down, start uvicorn from PROJECT_ROOT, wait for /health,
       then call the API.
    3. If the API still cannot be used, fall back to
       ``[sys.executable, str(MAIN_SCRIPT)]`` with ``cwd=PROJECT_ROOT``.
    """
    api_base = os.getenv("FA_API_BASE", DEFAULT_API_BASE).rstrip("/")
    health_url = f"{api_base}/health"
    run_url = f"{api_base}/api/v1/evaluation/run"
    api_port = _api_port_from_base(api_base)

    start = time.time()
    with _run_lock:
        _run_state.update(
            running=True,
            returncode=None,
            log="",
            started_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            finished_at=None,
            elapsed_s=None,
        )

    buffer: list[str] = []
    uvicorn_proc: subprocess.Popen | None = None
    started_backend_here = False
    rc = 1

    def _log(line: str) -> None:
        buffer.append(line if line.endswith("\n") else line + "\n")
        with _run_lock:
            _run_state["log"] = "".join(buffer[-400:])

    try:
        _log(f"PROJECT_ROOT={PROJECT_ROOT}")
        _log(f"MAIN_SCRIPT={MAIN_SCRIPT}")
        _log(f"API base={api_base}")

        if _backend_healthy(health_url):
            _log("Existing FastAPI backend detected — reusing it (no new process).")
        else:
            _log(
                "Backend not healthy — starting uvicorn "
                f"(backend.main:app) on 127.0.0.1:{api_port} …"
            )
            uvicorn_proc = _start_uvicorn(api_port)
            started_backend_here = True
            for _ in range(60):
                if _backend_healthy(health_url):
                    _log("Backend healthy.")
                    break
                if uvicorn_proc.poll() is not None:
                    leftover = ""
                    if uvicorn_proc.stdout is not None:
                        leftover = uvicorn_proc.stdout.read() or ""
                    raise RuntimeError(
                        "uvicorn exited before becoming healthy.\n" + leftover[-2000:]
                    )
                time.sleep(0.5)
            else:
                raise RuntimeError(
                    f"Timed out waiting for FastAPI /health at {health_url}"
                )

        if _backend_healthy(health_url):
            # When the backend is available, call the API only — do not spawn
            # another Python analysis process (requirement 7).
            _log("Executing analysis via POST /api/v1/evaluation/run …")
            try:
                rc, body = _post_evaluation_run(run_url, log_dir, stil_file)
                _log(body[:4000])
                if rc == 0:
                    _log(
                        "API analysis completed. "
                        "Load Last Results still reads failure_analysis_report.json "
                        "if previously produced by the CLI fallback."
                    )
            except urllib.error.URLError as exc:
                _log(f"API call failed ({exc}); falling back to absolute main.py …")
                rc, out = _run_main_script(log_dir, stil_file, recursive)
                _log(out[-4000:] if out else "(no output)")
        else:
            _log("API unavailable after startup attempt — falling back to main.py …")
            rc, out = _run_main_script(log_dir, stil_file, recursive)
            _log(out[-4000:] if out else "(no output)")

    except Exception as exc:  # noqa: BLE001
        _log(f"ERROR: {exc}")
        _log("Attempting absolute-path main.py fallback …")
        try:
            rc, out = _run_main_script(log_dir, stil_file, recursive)
            _log(out[-4000:] if out else "(no output)")
        except Exception as fallback_exc:  # noqa: BLE001
            _log(f"FALLBACK ERROR: {fallback_exc}")
            rc = 1
    finally:
        # Never kill a pre-existing backend. Leave uvicorn we started running so
        # subsequent Run Analysis clicks can reuse it.
        if started_backend_here and uvicorn_proc is not None and uvicorn_proc.poll() is None:
            _log("Leaving started uvicorn process running for subsequent API calls.")

    elapsed = time.time() - start
    with _run_lock:
        _run_state.update(
            running=False,
            returncode=rc,
            finished_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            elapsed_s=round(elapsed, 2),
            log="".join(buffer[-400:]),
        )


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silence default logging
        pass

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, code: int, payload: dict) -> None:
        self._send(code, json.dumps(payload).encode("utf-8"), "application/json")

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/index"):
            self._send(200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if self.path.startswith("/api/report"):
            if REPORT_PATH.is_file():
                data = REPORT_PATH.read_text(encoding="utf-8", errors="replace")
                self._send(200, data.encode("utf-8"), "application/json")
            else:
                self._send_json(404, {"error": "No report yet. Run the agent first."})
            return
        if self.path.startswith("/api/status"):
            with _run_lock:
                self._send_json(200, dict(_run_state))
            return
        if self.path.startswith("/api/defaults"):
            self._send_json(
                200,
                {
                    "log_dir": DEFAULT_LOG_DIR,
                    "stil_file": DEFAULT_STIL_FILE,
                    "report_exists": REPORT_PATH.is_file(),
                    "project_root": str(PROJECT_ROOT),
                    "main_script": str(MAIN_SCRIPT),
                    "api_base": DEFAULT_API_BASE,
                    "dashboard_note": (
                        "Run Analysis prefers FastAPI at FA_API_BASE; "
                        "falls back to absolute main.py only if the API is unavailable."
                    ),
                },
            )
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if not self.path.startswith("/api/run"):
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            payload = {}

        with _run_lock:
            if _run_state["running"]:
                self._send_json(409, {"error": "An analysis is already running."})
                return

        thread = threading.Thread(
            target=_run_agent,
            args=(
                payload.get("log_dir", "").strip(),
                payload.get("stil_file", "").strip(),
                bool(payload.get("recursive", False)),
            ),
            daemon=True,
        )
        thread.start()
        self._send_json(200, {"started": True})


INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Failure Analysis Agent - Dashboard</title>
<style>
  :root{
    --bg:#0b1020; --panel:#141b2e; --panel2:#1b2440; --line:#243154;
    --txt:#e7ecf6; --mut:#93a0bd; --accent:#4da3ff; --accent2:#7c5cff;
    --ok:#33d69f; --warn:#ffb020; --bad:#ff5d6c;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:"Segoe UI",Roboto,Arial,sans-serif;background:
    radial-gradient(1200px 600px at 80% -10%,#16223f 0,transparent 60%),var(--bg);
    color:var(--txt);}
  header{display:flex;align-items:center;gap:14px;padding:18px 26px;border-bottom:1px solid var(--line);
    position:sticky;top:0;background:rgba(11,16,32,.86);backdrop-filter:blur(8px);z-index:5}
  .logo{width:34px;height:34px;border-radius:8px;background:linear-gradient(135deg,var(--accent),var(--accent2));
    display:flex;align-items:center;justify-content:center;font-weight:800;color:#06122b}
  header h1{font-size:18px;margin:0;letter-spacing:.3px}
  header .sub{color:var(--mut);font-size:12px;margin-left:auto}
  .wrap{padding:22px 26px;max-width:1280px;margin:0 auto}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:18px}
  .panel h2{margin:0 0 14px;font-size:15px;letter-spacing:.4px;color:#cdd8f3;text-transform:uppercase}
  .ctrl{display:grid;grid-template-columns:1fr 1fr auto;gap:14px;align-items:end}
  .field label{display:block;font-size:12px;color:var(--mut);margin-bottom:6px}
  .field input[type=text]{width:100%;padding:10px 12px;border-radius:9px;border:1px solid var(--line);
    background:var(--panel2);color:var(--txt);font-size:13px}
  .row2{display:flex;gap:14px;align-items:center;margin-top:12px;flex-wrap:wrap}
  .chk{display:flex;align-items:center;gap:8px;color:var(--mut);font-size:13px}
  button{cursor:pointer;border:0;border-radius:10px;padding:11px 18px;font-weight:700;font-size:13px;
    background:linear-gradient(135deg,var(--accent),var(--accent2));color:#06122b}
  button.ghost{background:var(--panel2);color:var(--txt);border:1px solid var(--line)}
  button:disabled{opacity:.5;cursor:not-allowed}
  .status{font-size:13px;color:var(--mut);margin-top:12px;min-height:18px}
  .kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:14px}
  .kpi{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);
    border-radius:12px;padding:14px}
  .kpi .v{font-size:24px;font-weight:800}
  .kpi .l{font-size:11px;color:var(--mut);margin-top:4px;text-transform:uppercase;letter-spacing:.4px}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
  th{color:var(--mut);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.4px}
  .badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:700}
  .b-ok{background:rgba(51,214,159,.16);color:var(--ok)}
  .b-warn{background:rgba(255,176,32,.16);color:var(--warn)}
  .b-bad{background:rgba(255,93,108,.16);color:var(--bad)}
  .bar{height:8px;border-radius:6px;background:var(--panel2);overflow:hidden}
  .bar > i{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2))}
  .mut{color:var(--mut)}
  .pill{font-size:11px;color:var(--mut);background:var(--panel2);border:1px solid var(--line);
    padding:2px 8px;border-radius:999px;margin-right:6px;display:inline-block;margin-bottom:4px}
  pre.log{background:#070b16;border:1px solid var(--line);border-radius:10px;padding:12px;max-height:240px;
    overflow:auto;font-size:12px;color:#b9c6e6;white-space:pre-wrap}
  .empty{color:var(--mut);font-size:13px;padding:10px 0}
  .legend{font-size:12px;color:var(--mut);margin-top:8px}
  .dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:middle}
  @media(max-width:1000px){.kpis{grid-template-columns:repeat(3,1fr)}.ctrl{grid-template-columns:1fr}.grid2{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
  <div class="logo">V</div>
  <h1>Scan Chain Failure Analysis Agent</h1>
  <div class="sub">Verilumen Labs - Output Analysis Dashboard (UI :8050 · API :8000)</div>
</header>
<div class="wrap">

  <div class="panel">
    <h2>Run Analysis</h2>
    <div class="ctrl">
      <div class="field"><label>Log directory (tester .log files)</label>
        <input id="logDir" type="text" placeholder="path to logs"/></div>
      <div class="field"><label>STIL file</label>
        <input id="stilFile" type="text" placeholder="path to .stil"/></div>
      <div><button id="runBtn">Run Agent</button></div>
    </div>
    <div class="row2">
      <label class="chk"><input id="recursive" type="checkbox"/> Search sub-folders (recursive)</label>
      <button id="loadBtn" class="ghost">Load Last Results</button>
    </div>
    <div id="status" class="status"></div>
    <pre id="runLog" class="log" style="display:none"></pre>
  </div>

  <div id="results" style="display:none">

    <div class="panel">
      <h2>Key Metrics</h2>
      <div class="kpis" id="kpis"></div>
    </div>

    <div class="panel">
      <h2>Requirements &amp; Acceptance Criteria</h2>
      <table id="acceptTable"><thead><tr>
        <th>Requirement</th><th>Acceptance Criteria</th><th>Status</th><th>Evidence</th>
      </tr></thead><tbody></tbody></table>
    </div>

    <div class="panel">
      <h2>Ingestion &amp; Validation (FA-FR-001)</h2>
      <div id="ingest"></div>
    </div>

    <div class="grid2">
      <div class="panel">
        <h2>Fault Classification (FA-FR-004)</h2>
        <table id="faultTable"><thead><tr><th>Category</th><th>Count</th><th>Share</th></tr></thead><tbody></tbody></table>
        <div id="faultDefs" class="legend"></div>
      </div>
      <div class="panel">
        <h2>Detection Accuracy (FA-FR-002)</h2>
        <div id="detBox"></div>
      </div>
    </div>

    <div class="panel">
      <h2>Die-Level Analysis (FA-FR-007)</h2>
      <table id="dieTable"><thead><tr>
        <th>Die</th><th>Wafer</th><th>Failing</th><th>Severity</th><th>Class</th>
        <th>Disposition</th><th>Faults</th>
      </tr></thead><tbody></tbody></table>
      <div id="dieSeverityNote" class="legend"></div>
    </div>

    <div class="grid2">
      <div class="panel">
        <h2>Wafer Map (FA-FR-008)</h2>
        <div id="waferMap"></div>
        <div class="legend">
          <span><span class="dot" style="background:var(--bad)"></span>Failing die</span>
          &nbsp;&nbsp;
          <span><span class="dot" style="background:var(--ok)"></span>Passing die</span>
        </div>
      </div>
      <div class="panel">
        <h2>Wafer Ranking &amp; Signature (FA-FR-008)</h2>
        <table id="waferTable"><thead><tr>
          <th>Wafer</th><th>Lot</th><th>Fail Rate</th><th>Signature</th><th>Outlier</th>
        </tr></thead><tbody></tbody></table>
      </div>
    </div>

    <div class="panel">
      <h2>Fault-Type Prediction (FA-FR-009)</h2>
      <div id="rootMeta" class="legend" style="margin-bottom:10px"></div>
      <table id="rootTable"><thead><tr>
        <th>Scan Chain</th><th>Predicted Cause</th><th>Confidence</th><th>Evidence</th>
      </tr></thead><tbody></tbody></table>
    </div>

    <div class="grid2">
      <div class="panel">
        <h2>Recurring Failures (FA-FR-005)</h2>
        <div id="recurBox"></div>
      </div>
      <div class="panel">
        <h2>Correlation (FA-FR-006)</h2>
        <div id="corrBox"></div>
      </div>
    </div>

  </div>
</div>

<script>
const $ = s => document.querySelector(s);
const el = (t,c,h)=>{const e=document.createElement(t);if(c)e.className=c;if(h!=null)e.innerHTML=h;return e;};
const pct = x => (x==null?'-':(x*100).toFixed(2)+'%');
const num = x => (x==null?'-':Number(x).toLocaleString());

function badge(status){
  const s=(status||'').toUpperCase();
  const cls = s==='MET'?'b-ok':(s==='PARTIAL'?'b-warn':'b-bad');
  return `<span class="badge ${cls}">${s||'-'}</span>`;
}

async function poll(){
  const r = await fetch('/api/status'); const st = await r.json();
  const log = $('#runLog');
  if(st.log){ log.style.display='block'; log.textContent = st.log; log.scrollTop = log.scrollHeight; }
  if(st.running){
    $('#status').textContent = 'Running analysis... (started '+st.started_at+')';
    $('#runBtn').disabled = true;
    setTimeout(poll, 1500);
  } else {
    $('#runBtn').disabled = false;
    if(st.returncode!=null){
      const okmsg = st.returncode===0 ? 'completed successfully' :
        (st.returncode===2 ? 'completed (with validation warnings)' : 'failed (code '+st.returncode+')');
      $('#status').textContent = 'Analysis '+okmsg+(st.elapsed_s? ' in '+st.elapsed_s+'s':'')+'. Loading results...';
      loadReport();
    }
  }
}

async function runAgent(){
  $('#status').textContent = 'Starting...';
  const body = {log_dir:$('#logDir').value, stil_file:$('#stilFile').value, recursive:$('#recursive').checked};
  const r = await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(r.status===409){ $('#status').textContent='Already running.'; return; }
  poll();
}

async function loadReport(){
  const r = await fetch('/api/report');
  if(!r.ok){ $('#status').textContent='No results yet - run the agent first.'; return; }
  const rep = await r.json();
  render(rep);
  $('#results').style.display='block';
}

function render(rep){
  const a = rep.analysis||{}; const s=a.summary||{};
  const det = (a.detection||{}).detection_accuracy||{};
  // KPIs
  const kpis = [
    ['Dies Tested', num(s.total_dies_tested)],
    ['Failing Dies', num(s.total_failing_dies)],
    ['Die Failure Rate', pct(s.overall_die_failure_rate)],
    ['Detection Accuracy', (det.accuracy_pct!=null? det.accuracy_pct.toFixed(2)+'%':'-')],
    ['Failing Patterns', num(s.total_failing_patterns)],
    ['Fault-Type Predictions', num(s.fault_type_prediction_count ?? s.root_cause_prediction_count)],
  ];
  const kc=$('#kpis'); kc.innerHTML='';
  kpis.forEach(([l,v])=>{const c=el('div','kpi');c.appendChild(el('div','v',v));c.appendChild(el('div','l',l));kc.appendChild(c);});

  // Acceptance table
  const trace = (a.failure_summary||{}).requirement_traceability||{};
  const tb=$('#acceptTable tbody'); tb.innerHTML='';
  Object.keys(trace).filter(k=>k.startsWith('FA-FR')).sort().forEach(k=>{
    const v=trace[k];
    const tr=el('tr');
    tr.innerHTML=`<td><b>${k}</b><br><span class="mut">${v.description||''}</span></td>
      <td>${v.acceptance_criteria||''}</td><td>${badge(v.status)}</td><td class="mut">${v.evidence||''}</td>`;
    tb.appendChild(tr);
  });

  // Ingestion
  const ing=rep.ingestion||{}; const stil=ing.stil||{}; const cv=ing.cross_validation||{};
  const md=stil.metadata||{};
  $('#ingest').innerHTML = `
    <span class="pill">Tester logs: ${num((ing.tester_logs||{}).files_parsed_successfully)} parsed</span>
    <span class="pill">STDF validation: ${(ing.stdf||{}).validation_passed}</span>
    <span class="pill">STIL chains: ${num(stil.scan_chain_count)}</span>
    <span class="pill">STIL patterns: ${num(md.pattern_count_verified)}</span>
    <span class="pill">Cross-validation: ${badge(cv.passed?'MET':'PARTIAL')}</span>
    <div class="legend" style="margin-top:8px">${(cv.notes||[]).join(' &bull; ')}</div>`;

  // Fault classification
  const fc=a.fault_classification||{}; const cs=fc.category_summary||{};
  const ft=$('#faultTable tbody'); ft.innerHTML='';
  const cats=Object.keys(cs);
  if(cats.length===0){ ft.appendChild(el('tr',null,'<td colspan=3 class="empty">No fault categories (no failures).</td>')); }
  cats.forEach(c=>{
    const v=cs[c]; const tr=el('tr');
    tr.innerHTML=`<td>${c}</td><td>${num(v.count)}</td>
      <td><div class="bar"><i style="width:${(v.percentage*100).toFixed(1)}%"></i></div>
      <span class="mut">${(v.percentage*100).toFixed(1)}%</span></td>`;
    ft.appendChild(tr);
  });
  const defs=fc.category_definitions||{};
  $('#faultDefs').innerHTML = '<b>Category definitions:</b><br>' +
    Object.keys(defs).map(k=>`<b>${k}</b>: ${defs[k]}`).join('<br>');

  // Detection accuracy box
  $('#detBox').innerHTML = `
    <div style="font-size:30px;font-weight:800">${det.accuracy_pct!=null?det.accuracy_pct.toFixed(2)+'%':'-'}
      ${badge(det.meets_threshold?'MET':'PARTIAL')}</div>
    <div class="bar" style="margin:10px 0"><i style="width:${det.accuracy_pct||0}%"></i></div>
    <div class="legend">Parsed ${num(det.parsed_executions)} / ${num(det.expected_executions)} declared executions;
      malformed blocks: ${num(det.malformed_blocks)}; threshold ${pct(det.threshold)}.</div>
    <div class="legend" style="margin-top:6px">${det.method||''}</div>`;

  // Die table
  const dl=a.die_level_analysis||{}; const dfeed=dl.dashboard_feed||[];
  if(dl.severity_caveat) $('#dieSeverityNote').textContent=dl.severity_caveat;
  const dt=$('#dieTable tbody'); dt.innerHTML='';
  dfeed.forEach(d=>{
    const sevLabel=d.severity_determinable
      ? ((d.die_failure_severity!=null?(d.die_failure_severity*100).toFixed(4)+'%':'-'))
      : (d.severity_label||'N/A');
    const cls=d.severity_class==='PASS'?'b-ok':(d.severity_class==='CATASTROPHIC_FAIL'?'b-bad':(d.severity_determinable?'b-warn':'b-warn'));
    const dis=d.disposition==='RELEASE'?'b-ok':(d.disposition==='SCRAP'?'b-bad':'b-warn');
    const faults=Object.entries(d.fault_breakdown||{}).map(([k,v])=>`${k}:${v}`).join(', ')||'-';
    const tr=el('tr');
    tr.innerHTML=`<td>${d.die_id}</td><td>${d.wafer_id}</td><td>${num(d.failing_pattern_count)}</td>
      <td>${sevLabel}</td>
      <td><span class="badge ${cls}">${d.severity_determinable?d.severity_class:(d.severity_label||'N/A')}</span></td>
      <td><span class="badge ${dis}">${d.disposition}</span></td><td class="mut">${faults}</td>`;
    dt.appendChild(tr);
  });

  // Wafer map (SVG scatter from spatial_map)
  const wl=a.wafer_level_analysis||{}; const sp=wl.spatial_map||[];
  drawWaferMap(sp);
  const wt=$('#waferTable tbody'); wt.innerHTML='';
  (wl.wafer_ranking||[]).forEach(w=>{
    const tr=el('tr');
    const outBadge=w.is_outlier?'<span class="badge b-bad">OUTLIER</span>':'<span class="mut">-</span>';
    tr.innerHTML=`<td>${w.wafer_id}</td><td>${w.lot_id}</td><td>${pct(w.failure_rate??(w.failure_rate_pct/100))}</td>
      <td><span class="pill">${w.spatial_signature||'-'}</span></td><td>${outBadge}</td>`;
    wt.appendChild(tr);
  });

  // Root cause
  const rc=a.fault_type_predictions||a.root_cause_predictions||{};
  $('#rootMeta').innerHTML = `<b>Phase:</b> ${rc.phase||'-'} &mdash; ${rc.phase_description||''}`;
  const rt=$('#rootTable tbody'); rt.innerHTML='';
  (rc.predictions||[]).forEach(p=>{
    const conf=(p.confidence_score*100).toFixed(0);
    const tr=el('tr');
    tr.innerHTML=`<td class="mut">${(p.scan_chain_id||'').split('__').pop()}</td>
      <td><b>${p.predicted_fault_type||p.predicted_root_cause}</b></td>
      <td style="min-width:120px"><div class="bar"><i style="width:${conf}%"></i></div>
        <span class="mut">${p.confidence_score}</span></td>
      <td class="mut">${(p.evidence||[]).join('<br>')}</td>`;
    rt.appendChild(tr);
  });

  // Recurring & correlation
  const rec=a.recurring_failures||{};
  $('#recurBox').innerHTML=`
    <div class="pill">Recurring patterns: ${num(rec.recurring_pattern_count)}</div>
    <div class="pill">Unique failing: ${num(rec.total_unique_failing_patterns)}</div>
    <div class="pill">Min lots: ${num(rec.min_lots_threshold)}</div>
    <div class="legend" style="margin-top:8px">${rec.recurring_definition||''}</div>`;
  const corr=a.failure_pattern_correlation||{};
  const tops=(corr.top_failing_patterns||[]).slice(0,8);
  $('#corrBox').innerHTML = (tops.length? '<table><thead><tr><th>Pattern</th><th>Failures</th><th>Score</th></tr></thead><tbody>'+
    tops.map(t=>`<tr><td>${t.pattern_id}</td><td>${num(t.failure_count)}</td><td>${t.correlation_score??'-'}</td></tr>`).join('')+
    '</tbody></table>' : '<div class="empty">No correlated patterns.</div>');
}

function drawWaferMap(points){
  const box=$('#waferMap');
  if(!points || points.length===0){ box.innerHTML='<div class="empty">No spatial coordinates available.</div>'; return; }
  const xs=points.map(p=>p.wafer_x).filter(v=>v!=null);
  const ys=points.map(p=>p.wafer_y).filter(v=>v!=null);
  const W=420,H=320,pad=30;
  const minX=Math.min(...xs,0),maxX=Math.max(...xs,1),minY=Math.min(...ys,0),maxY=Math.max(...ys,1);
  const sx=v=>pad+(W-2*pad)*((v-minX)/((maxX-minX)||1));
  const sy=v=>H-pad-(H-2*pad)*((v-minY)/((maxY-minY)||1));
  let svg=`<svg width="100%" viewBox="0 0 ${W} ${H}">
    <circle cx="${W/2}" cy="${H/2}" r="${Math.min(W,H)/2-pad+8}" fill="none" stroke="#243154"/>`;
  points.forEach(p=>{
    if(p.wafer_x==null||p.wafer_y==null) return;
    const c=p.is_failing?'#ff5d6c':'#33d69f';
    svg+=`<circle cx="${sx(p.wafer_x).toFixed(1)}" cy="${sy(p.wafer_y).toFixed(1)}" r="7" fill="${c}" opacity="0.85">
      <title>${p.die_id} (${p.wafer_x},${p.wafer_y}) failing=${p.is_failing}</title></circle>`;
  });
  svg+='</svg>';
  box.innerHTML=svg;
}

$('#runBtn').addEventListener('click', runAgent);
$('#loadBtn').addEventListener('click', loadReport);
(async ()=>{
  const d = await (await fetch('/api/defaults')).json();
  $('#logDir').value=d.log_dir; $('#stilFile').value=d.stil_file;
  if(d.report_exists) loadReport();
})();
</script>
</body></html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Failure Analysis Agent dashboard.")
    # Default UI port is 8050 so it does not collide with FastAPI on :8000.
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    if args.port == DEFAULT_API_PORT:
        print(
            f"WARNING: dashboard port {args.port} matches FA_API_PORT. "
            "FastAPI health checks and this UI will conflict. "
            "Prefer --port 8050 (default) and keep the API on 8000.",
            file=sys.stderr,
        )

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    print(f"Failure Analysis Agent dashboard running at {url}")
    print(f"Expects FastAPI backend at {DEFAULT_API_BASE} (FA_API_BASE).")
    print(f"PROJECT_ROOT={PROJECT_ROOT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
