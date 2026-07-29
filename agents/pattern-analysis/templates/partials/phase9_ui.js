
    /* PA-UI-009 PHASE 9 UI */
    let correlationNavigationAvailable = false;
    let lastCorrelationManifest = null;
    let correlationOutcomeRecords = [];
    let corrPage = 0;
    const corrPageSize = 100;
    let corrTableRenderToken = 0;
    let corrSearchQuery = "";
    let corrSearchDebounceTimer = null;
    const corrSearchDebounceMs = 250;
    let corrActiveFilters = { latestResult: "All", dataQuality: "All", scanChain: "All", pattern: "All" };
    let corrSortKey = "pattern_id";
    let corrSortDirection = "asc";
    let corrSelectedRowKey = null;
    let cachedCorrelationAnalytics = null;
    let correlationAnalyticsComputeCount = 0;

    function updateCorrelationNavigationVisibility() {
      const tab = document.getElementById("tab-correlation-btn");
      if (tab) tab.style.display = (activePhaseNum === 9 && correlationNavigationAvailable) ? "block" : "none";
    }
    function applyCorrelationNavigationFromReport(report) {
      correlationNavigationAvailable = !!(report.toggle_coverage && report.toggle_coverage.scan_chain_level && report.toggle_coverage.scan_chain_level.length && report.metadata && report.metadata.ate_log_used);
      updateCorrelationNavigationVisibility();
    }
    function updateCorrelationSummaryPanel(manifest) {
      if (!manifest) return;
      document.getElementById("corr-metadata-rows").textContent = (manifest.metadata_rows ?? "-").toLocaleString();
      document.getElementById("corr-matched-rows").textContent = (manifest.matched_rows ?? "-").toLocaleString();
      document.getElementById("corr-unmatched-metadata").textContent = (manifest.unmatched_metadata ?? "-").toLocaleString();
      document.getElementById("corr-unmatched-ate").textContent = (manifest.unmatched_ate ?? "-").toLocaleString();
      document.getElementById("corr-validation-status").textContent = manifest.validation_status || "-";
      document.getElementById("corr-hash").textContent = manifest.correlation_hash || "-";
      const matched = Number(manifest.matched_rows || 0), metadataRows = Number(manifest.metadata_rows || 0);
      const dashVal = document.getElementById("dash-passfail-val");
      if (dashVal) dashVal.textContent = `${matched.toLocaleString()} / ${metadataRows.toLocaleString()}`;
      const dashDesc = document.getElementById("dash-passfail-desc");
      if (dashDesc) dashDesc.textContent = "Pattern Outcome Correlation (PA-FR-009)";
    }

    /* PA-UI-009.1 Correlation Explorer */
    function displayCorrLatestResult(v) { return v === null || v === undefined ? "Unknown" : v; }
    function displayCorrDataQualityFlags(f) { return Array.isArray(f) && f.length ? f.join(", ") : "NO_FLAGS"; }
    function getLatestResultCategory(row) { return row.latest_result === null || row.latest_result === undefined ? "Unknown" : row.latest_result; }
    function getCorrRowKey(row) { return `${row.pattern_id}|${row.scan_chain_id}`; }
    function getDistinctCorrFlags(rows) { const s = new Set(); rows.forEach(r => (r.data_quality_flags || []).forEach(f => s.add(String(f)))); return Array.from(s).sort(); }
    function getDistinctCorrScanChains(rows) { return Array.from(new Set(rows.map(r => String(r.scan_chain_id)))).sort((a,b)=>a.localeCompare(b,undefined,{numeric:true,sensitivity:"base"})); }
    function getDistinctCorrPatterns(rows) { return Array.from(new Set(rows.map(r => String(r.pattern_id)))).sort(comparePatternSortKey); }
    function buildCorrelationSearchIndex(rows) {
      rows.forEach(row => {
        row._corrSearchPatternId = String(row.pattern_id || "").toLowerCase();
        row._corrSearchScanChainId = String(row.scan_chain_id || "").toLowerCase();
        row._corrSearchLatestResult = String(row.latest_result ?? "unknown").toLowerCase();
        row._corrSearchFlags = (row.data_quality_flags || []).map(f => String(f).toLowerCase()).join(" ");
      });
    }
    function matchesCorrSearch(row, query) {
      if (!query) return true;
      const q = query.toLowerCase();
      return row._corrSearchPatternId.includes(q) || row._corrSearchScanChainId.includes(q) || row._corrSearchLatestResult.includes(q) || row._corrSearchFlags.includes(q);
    }
    function readCorrActiveFiltersFromUi() {
      return {
        latestResult: document.getElementById("corr-filter-latest-result")?.value || "All",
        dataQuality: document.getElementById("corr-filter-data-quality")?.value || "All",
        scanChain: document.getElementById("corr-filter-scan-chain")?.value || "All",
        pattern: document.getElementById("corr-filter-pattern")?.value || "All",
      };
    }
    function applyCorrFilters(rows, filters) {
      return rows.filter(row => {
        if (filters.latestResult !== "All") {
          if (filters.latestResult === "Unknown") { if (row.latest_result !== null && row.latest_result !== undefined) return false; }
          else if (row.latest_result !== filters.latestResult) return false;
        }
        if (filters.dataQuality !== "All") {
          if (filters.dataQuality === "NO_FLAGS") { if ((row.data_quality_flags || []).length) return false; }
          else if (!(row.data_quality_flags || []).includes(filters.dataQuality)) return false;
        }
        if (filters.scanChain !== "All" && String(row.scan_chain_id) !== filters.scanChain) return false;
        if (filters.pattern !== "All" && String(row.pattern_id) !== filters.pattern) return false;
        return true;
      });
    }
    function compareCorrDataQuality(left, right) {
      const af = left.data_quality_flags || [], bf = right.data_quality_flags || [];
      if (af.length !== bf.length) return af.length - bf.length;
      return af.slice().sort().join("|").localeCompare(bf.slice().sort().join("|"));
    }
    function getCorrHistoryLength(row) { return Array.isArray(row.history) ? row.history.length : 0; }
    function sortCorrRows(rows, sortKey, sortDirection) {
      const sorted = rows.slice(), dir = sortDirection === "asc" ? 1 : -1;
      sorted.sort((l, r) => {
        let c = 0;
        if (sortKey === "pattern_id") c = comparePatternSortKey(l.pattern_id, r.pattern_id);
        else if (sortKey === "scan_chain_id") c = String(l.scan_chain_id||"").localeCompare(String(r.scan_chain_id||""), undefined, {numeric:true,sensitivity:"base"});
        else if (sortKey === "latest_result") c = String(getLatestResultCategory(l)).localeCompare(String(getLatestResultCategory(r)));
        else if (sortKey === "pass_count" || sortKey === "fail_count") c = Number(l[sortKey]) - Number(r[sortKey]);
        else if (sortKey === "history_length") c = getCorrHistoryLength(l) - getCorrHistoryLength(r);
        else if (sortKey === "data_quality") c = compareCorrDataQuality(l, r);
        return c * dir;
      });
      return sorted;
    }
    function buildCorrelationVisibleDataset() {
      let rows = correlationOutcomeRecords.filter(r => matchesCorrSearch(r, corrSearchQuery));
      rows = applyCorrFilters(rows, corrActiveFilters);
      return sortCorrRows(rows, corrSortKey, corrSortDirection);
    }
    function buildVisibleCorrRows() {
      const filteredRows = buildCorrelationVisibleDataset();
      const start = corrPage * corrPageSize;
      return { pageRows: filteredRows.slice(start, start + corrPageSize), filteredCount: filteredRows.length };
    }
    function renderCorrStatsLine(filtered, total, pageStart, pageSize) {
      const shown = Math.min(pageSize, Math.max(0, filtered - pageStart));
      return `Showing ${shown.toLocaleString()} of ${filtered.toLocaleString()} filtered rows (${total.toLocaleString()} total)`;
    }
    function populateCorrFilterOptions() {
      const scan = document.getElementById("corr-filter-scan-chain"), pat = document.getElementById("corr-filter-pattern"), qual = document.getElementById("corr-filter-data-quality");
      if (!scan || !pat || !qual) return;
      const ss = scan.value || "All", sp = pat.value || "All", sq = qual.value || "All";
      scan.innerHTML = "<option value=\"All\">All</option>"; getDistinctCorrScanChains(correlationOutcomeRecords).forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = v; scan.appendChild(o); }); scan.value = ss;
      pat.innerHTML = "<option value=\"All\">All</option>"; getDistinctCorrPatterns(correlationOutcomeRecords).forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = v; pat.appendChild(o); }); pat.value = sp;
      qual.innerHTML = "<option value=\"All\">All</option><option value=\"NO_FLAGS\">NO_FLAGS</option>";
      getDistinctCorrFlags(correlationOutcomeRecords).forEach(v => { const o = document.createElement("option"); o.value = v; o.textContent = v; qual.appendChild(o); }); qual.value = sq;
    }
    function resetCorrExplorerUiState() {
      corrSearchQuery = ""; corrPage = 0; corrSortKey = "pattern_id"; corrSortDirection = "asc"; corrSelectedRowKey = null;
      corrActiveFilters = { latestResult: "All", dataQuality: "All", scanChain: "All", pattern: "All" };
      const si = document.getElementById("corr-search-input"); if (si) si.value = "";
      ["corr-filter-latest-result","corr-filter-data-quality","corr-filter-scan-chain","corr-filter-pattern"].forEach(id => { const e = document.getElementById(id); if (e) e.value = "All"; });
      updateCorrSortIndicators();
    }
    function updateCorrSortIndicators() {
      document.querySelectorAll("[data-corr-sort-indicator]").forEach(el => {
        const k = el.getAttribute("data-corr-sort-indicator");
        el.textContent = k === corrSortKey ? (corrSortDirection === "asc" ? "▲" : "▼") : "";
      });
    }
    function onCorrSearchInput(e) { clearTimeout(corrSearchDebounceTimer); corrSearchDebounceTimer = setTimeout(() => { corrSearchQuery = String(e.target.value||"").trim(); corrPage = 0; scheduleCorrelationTableRender(); }, corrSearchDebounceMs); }
    function onCorrFilterChange() { corrActiveFilters = readCorrActiveFiltersFromUi(); corrPage = 0; scheduleCorrelationTableRender(); }
    function onCorrSortHeaderClick(k) {
      if (corrSortKey === k) corrSortDirection = corrSortDirection === "asc" ? "desc" : "asc";
      else { corrSortKey = k; corrSortDirection = (k === "pass_count" || k === "fail_count" || k === "history_length" || k === "data_quality") ? "desc" : "asc"; }
      corrPage = 0; updateCorrSortIndicators(); scheduleCorrelationTableRender();
    }
    function updateCorrelationExplorerVisibility(has) {
      const ex = document.getElementById("corr-explorer-panel"), out = document.getElementById("corr-outcomes-panel");
      if (ex) ex.style.display = has ? "block" : "none";
      if (out) out.style.display = has ? "block" : "none";
    }
    function updateCorrelationPaginationControls(filtered, total, start, end) {
      const info = document.getElementById("corr-pagination-info"), prev = document.getElementById("btn-corr-prev"), next = document.getElementById("btn-corr-next");
      if (info) info.textContent = renderCorrStatsLine(filtered, total, start, end - start);
      if (prev) prev.disabled = corrPage === 0;
      if (next) next.disabled = end >= filtered;
    }
    function scheduleCorrelationTableRender() {
      const token = ++corrTableRenderToken;
      requestAnimationFrame(() => { if (token !== corrTableRenderToken) return; renderCorrelationTable(); });
    }
    function renderCorrelationTable() {
      const tbody = document.getElementById("corr-outcomes-table")?.querySelector("tbody"), empty = document.getElementById("corr-outcomes-empty");
      if (!tbody || !empty) return;
      tbody.innerHTML = "";
      if (!correlationOutcomeRecords.length) { empty.style.display = "block"; empty.textContent = "No correlation outcomes to display. Run correlation to populate the investigation table."; updateCorrelationPaginationControls(0,0,0,0); updateCorrSortIndicators(); return; }
      const { pageRows, filteredCount } = buildVisibleCorrRows(), total = correlationOutcomeRecords.length, start = corrPage * corrPageSize, end = start + pageRows.length;
      if (!filteredCount) { empty.style.display = "block"; empty.textContent = "No outcomes match the current search and filter criteria."; updateCorrelationPaginationControls(0, total, 0, 0); updateCorrSortIndicators(); return; }
      empty.style.display = "none";
      const frag = document.createDocumentFragment();
      pageRows.forEach(row => {
        const tr = document.createElement("tr");
        if (corrSelectedRowKey === getCorrRowKey(row)) tr.classList.add("corr-row-selected");
        tr.addEventListener("click", () => openCorrDetailDrawer(row));
        [row.pattern_id, row.scan_chain_id, displayCorrLatestResult(row.latest_result), row.pass_count ?? 0, row.fail_count ?? 0, getCorrHistoryLength(row), displayCorrDataQualityFlags(row.data_quality_flags)].forEach((v,i) => {
          const td = document.createElement("td"); td.textContent = v != null ? v : ""; if (i === 6) td.className = "corr-flag-cell"; tr.appendChild(td);
        });
        frag.appendChild(tr);
      });
      tbody.appendChild(frag);
      updateCorrelationPaginationControls(filteredCount, total, start, end);
      updateCorrSortIndicators();
    }
    window.prevCorrPage = function() { if (corrPage > 0) { corrPage--; scheduleCorrelationTableRender(); } };
    window.nextCorrPage = function() { const { filteredCount } = buildVisibleCorrRows(); if ((corrPage+1)*corrPageSize < filteredCount) { corrPage++; scheduleCorrelationTableRender(); } };
    function formatCorrExecutionHistory(h) {
      const s = Array.isArray(h) ? h.slice().sort((a,b)=>Number(a.run_id)-Number(b.run_id)) : [];
      return s.length ? s.map((e,i)=>`Run ${i+1}  →  ${e.result||"-"}`).join("\n") : "No execution history";
    }
    function openCorrDetailDrawer(row) {
      const drawer = document.getElementById("corr-detail-drawer"); if (!drawer || !row) return;
      corrSelectedRowKey = getCorrRowKey(row);
      const hist = Array.isArray(row.history) ? row.history.slice().sort((left, right) => Number(left.run_id) - Number(right.run_id)) : [];
      document.getElementById("corr-drawer-pattern").textContent = row.pattern_id || "-";
      document.getElementById("corr-drawer-scan-chain").textContent = row.scan_chain_id || "-";
      document.getElementById("corr-drawer-latest-result").textContent = displayCorrLatestResult(row.latest_result);
      document.getElementById("corr-drawer-pass-count").textContent = row.pass_count != null ? row.pass_count : "-";
      document.getElementById("corr-drawer-fail-count").textContent = row.fail_count != null ? row.fail_count : "-";
      document.getElementById("corr-drawer-history-length").textContent = String(getCorrHistoryLength(row));
      document.getElementById("corr-drawer-history").textContent = formatCorrExecutionHistory(row.history);
      document.getElementById("corr-drawer-run-ids").textContent = hist.length ? hist.map(e => e.run_id).join(", ") : "-";
      document.getElementById("corr-drawer-validation-status").textContent = lastCorrelationManifest?.validation_status || "-";
      document.getElementById("corr-drawer-data-quality").textContent = displayCorrDataQualityFlags(row.data_quality_flags);
      document.getElementById("corr-drawer-manifest-version").textContent = lastCorrelationManifest?.correlation_version != null ? String(lastCorrelationManifest.correlation_version) : "-";
      drawer.style.display = "flex"; scheduleCorrelationTableRender();
    }
    function closeCorrDetailDrawer() { const d = document.getElementById("corr-detail-drawer"); if (d) d.style.display = "none"; }
    function closeCorrDetailDrawerOnBackdrop(e) { if (e.target && e.target.id === "corr-detail-drawer") closeCorrDetailDrawer(); }
    function loadCorrelationOutcomeDataset(body) {
      correlationOutcomeRecords = Array.isArray(body?.pattern_outcomes?.patterns) ? body.pattern_outcomes.patterns : [];
      buildCorrelationSearchIndex(correlationOutcomeRecords);
      resetCorrExplorerUiState(); populateCorrFilterOptions();
      updateCorrelationExplorerVisibility(correlationOutcomeRecords.length > 0);
      invalidateCorrelationAnalyticsCache(); refreshCorrelationAnalyticsDashboard();
      scheduleCorrelationTableRender();
    }

    /* PA-UI-009.2 Correlation Analytics Dashboard */
    function invalidateCorrelationAnalyticsCache() { cachedCorrelationAnalytics = null; }
    function roundCorrAnalytics2(v) { return Math.round(Number(v) * 100) / 100; }
    function computePassFailDistribution(patterns) {
      const counts = { PASS: 0, FAIL: 0, Unknown: 0 };
      patterns.forEach(p => { const k = getLatestResultCategory(p); counts[k] = (counts[k] ?? 0) + 1; });
      return counts;
    }
    function computeTopFailingScanChains(patterns, topN) {
      const m = new Map();
      patterns.forEach(p => m.set(p.scan_chain_id, (m.get(p.scan_chain_id) ?? 0) + Number(p.fail_count || 0)));
      return Array.from(m.entries()).map(([scan_chain_id, fail_count]) => ({ scan_chain_id, fail_count })).filter(x => x.fail_count > 0)
        .sort((a,b) => b.fail_count - a.fail_count || String(a.scan_chain_id).localeCompare(String(b.scan_chain_id), undefined, {numeric:true,sensitivity:"base"})).slice(0, topN || 10);
    }
    function computeTopFailingPatterns(patterns, topN) {
      return patterns.slice().filter(p => Number(p.fail_count||0) > 0).sort((a,b) => Number(b.fail_count)-Number(a.fail_count) || comparePatternSortKey(a.pattern_id,b.pattern_id)).slice(0, topN||10);
    }
    function computeDataQualityOverview(patterns) {
      const counts = new Map(); let noFlags = 0;
      patterns.forEach(p => { const flags = p.data_quality_flags || []; if (!flags.length) noFlags++; else flags.forEach(flag => counts.set(flag, (counts.get(flag)??0)+1)); });
      counts.set("NO_FLAGS", noFlags); return counts;
    }
    function computeCorrelationHealthStats(patterns) {
      const total = patterns.length; if (!total) return { pass_rate:0,fail_rate:0,unknown_rate:0,issues_rate:0,clean_rate:0,total:0 };
      const d = computePassFailDistribution(patterns), issues = patterns.filter(p => (p.data_quality_flags||[]).length).length;
      return { pass_rate: roundCorrAnalytics2(d.PASS/total*100), fail_rate: roundCorrAnalytics2(d.FAIL/total*100), unknown_rate: roundCorrAnalytics2(d.Unknown/total*100), issues_rate: roundCorrAnalytics2(issues/total*100), clean_rate: roundCorrAnalytics2((total-issues)/total*100), total };
    }
    function computeTotalFailEvents(patterns) { return patterns.reduce((s,p)=>s+Number(p.fail_count||0),0); }
    function generateCorrelationInsights(stats, topChains, dataQuality, totalFails) {
      const insights = [`${stats.pass_rate}% of correlated rows passed.`];
      if (totalFails > 0 && topChains.length) insights.push(`${topChains[0].scan_chain_id} has the highest FAIL count.`);
      const dup = dataQuality.get("DUPLICATE_HISTORY") ?? 0;
      insights.push(dup === 0 ? "No duplicate history records detected." : `${dup} duplicate history record(s) detected.`);
      insights.push(`Only ${stats.issues_rate}% of rows contain quality issues.`);
      const top10 = topChains.reduce((s,c)=>s+c.fail_count,0);
      insights.push(`Top 10 scan chains contribute ${totalFails > 0 ? roundCorrAnalytics2(top10/totalFails*100) : 0}% of all FAIL events.`);
      return insights;
    }
    function computeAllCorrelationAnalytics(patterns) {
      correlationAnalyticsComputeCount += 1;
      const topFailingScanChains = computeTopFailingScanChains(patterns, 10);
      return {
        passFailDistribution: computePassFailDistribution(patterns),
        topFailingScanChains,
        topFailingPatterns: computeTopFailingPatterns(patterns, 10),
        dataQualityOverview: computeDataQualityOverview(patterns),
        healthStats: computeCorrelationHealthStats(patterns),
        totalFailEvents: computeTotalFailEvents(patterns),
        insights: generateCorrelationInsights(computeCorrelationHealthStats(patterns), topFailingScanChains, computeDataQualityOverview(patterns), computeTotalFailEvents(patterns)),
      };
    }
    function getOrComputeCorrelationAnalytics(patterns) {
      if (cachedCorrelationAnalytics === null) cachedCorrelationAnalytics = computeAllCorrelationAnalytics(patterns);
      return cachedCorrelationAnalytics;
    }
    function corrAnalyticsColor(key) {
      const p = { PASS:"#34d399", FAIL:"#f87171", Unknown:"#94a3b8", NO_FLAGS:"#60a5fa", DUPLICATE_HISTORY:"#fbbf24", BIT_MISMATCH:"#fb923c", NO_MATCHING_SCAN_CHAIN:"#a78bfa", MISSING_PATTERN:"#f472b6", JOIN_FAILURE:"#ef4444" };
      return p[key] || `hsl(${(String(key).split("").reduce((s,c)=>s+c.charCodeAt(0),0)*17)%360},65%,55%)`;
    }
    function polarToCartesian(cx,cy,r,a) { const rad=((a-90)*Math.PI)/180; return { x: cx+r*Math.cos(rad), y: cy+r*Math.sin(rad) }; }
    function describeDonutArc(cx,cy,or,ir,sa,ea) {
      const s=polarToCartesian(cx,cy,or,ea), e=polarToCartesian(cx,cy,or,sa), is=polarToCartesian(cx,cy,ir,ea), ie=polarToCartesian(cx,cy,ir,sa), la=ea-sa<=180?0:1;
      return [`M ${s.x} ${s.y}`,`A ${or} ${or} 0 ${la} 0 ${e.x} ${e.y}`,`L ${ie.x} ${ie.y}`,`A ${ir} ${ir} 0 ${la} 1 ${is.x} ${is.y}`,"Z"].join(" ");
    }
    function showCorrTooltip(id, stageId, html, cx, cy) {
      const t = document.getElementById(id), st = document.getElementById(stageId); if (!t||!st) return;
      t.innerHTML = html; t.style.display = "block";
      const b = st.getBoundingClientRect(); t.style.left = `${Math.min(Math.max(cx-b.left+12,8), b.width-t.offsetWidth-8)}px`; t.style.top = `${Math.min(Math.max(cy-b.top+12,8), b.height-t.offsetHeight-8)}px`;
    }
    function hideCorrTooltip(id) { const t = document.getElementById(id); if (t) t.style.display = "none"; }
    function renderCorrPassFailDonutChart(analytics) {
      const svg = document.getElementById("corr-passfail-chart"), legend = document.getElementById("corr-passfail-legend"), empty = document.getElementById("corr-passfail-empty");
      if (!svg||!legend||!empty) return; hideCorrTooltip("corr-passfail-tooltip"); svg.innerHTML=""; legend.innerHTML="";
      const slices = [{label:"PASS",value:analytics.passFailDistribution.PASS||0},{label:"FAIL",value:analytics.passFailDistribution.FAIL||0},{label:"Unknown",value:analytics.passFailDistribution.Unknown||0}].filter(s=>s.value>0);
      const total = slices.reduce((s,x)=>s+x.value,0); if (!total) { svg.style.display="none"; empty.style.display="block"; return; }
      svg.style.display="block"; empty.style.display="none"; let ang=0;
      slices.forEach(sl => { const sw=(sl.value/total)*360; if (sw<=0) return; const p=document.createElementNS("http://www.w3.org/2000/svg","path");
        p.setAttribute("d", describeDonutArc(110,120,78,42,ang,ang+sw)); p.setAttribute("fill", corrAnalyticsColor(sl.label));
        p.addEventListener("mouseenter", ev => showCorrTooltip("corr-passfail-tooltip","corr-passfail-chart-stage", `<strong>${sl.label}</strong><br>${sl.value} (${roundCorrAnalytics2(sl.value/total*100)}%)`, ev.clientX, ev.clientY));
        p.addEventListener("mouseleave", () => hideCorrTooltip("corr-passfail-tooltip")); svg.appendChild(p); ang+=sw; });
      slices.forEach(sl => { const it=document.createElement("div"); it.className="clu-chart-legend-item"; it.innerHTML=`<span class="clu-chart-legend-swatch" style="background:${corrAnalyticsColor(sl.label)}"></span><span>${sl.label}: ${sl.value} (${roundCorrAnalytics2(sl.value/total*100)}%)</span>`; legend.appendChild(it); });
    }
    function renderCorrHorizontalBarChart(svgId, emptyId, items, color) {
      const svg = document.getElementById(svgId), empty = document.getElementById(emptyId); if (!svg||!empty) return; svg.innerHTML="";
      if (!items.length) { svg.style.display="none"; empty.style.display="block"; return; }
      svg.style.display="block"; empty.style.display="none";
      const w=320,lw=92,cl=lw+12,cw=w-cl-16,bh=16,g=10,mx=Math.max(...items.map(i=>i.value),1),h=Math.max(160,items.length*(bh+g)+24);
      svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
      items.forEach((it,idx) => { const y=16+idx*(bh+g), bw=(it.value/mx)*cw, col=typeof color==="function"?color(it):color;
        const lab=document.createElementNS("http://www.w3.org/2000/svg","text"); lab.setAttribute("x","8"); lab.setAttribute("y",String(y+bh-4)); lab.setAttribute("class","corr-bar-chart-label"); lab.textContent=it.label.length>12?`${it.label.slice(0,11)}…`:it.label; svg.appendChild(lab);
        const tr=document.createElementNS("http://www.w3.org/2000/svg","rect"); tr.setAttribute("x",String(cl)); tr.setAttribute("y",String(y)); tr.setAttribute("width",String(cw)); tr.setAttribute("height",String(bh)); tr.setAttribute("rx","3"); tr.setAttribute("fill","rgba(255,255,255,0.06)"); svg.appendChild(tr);
        const bar=document.createElementNS("http://www.w3.org/2000/svg","rect"); bar.setAttribute("x",String(cl)); bar.setAttribute("y",String(y)); bar.setAttribute("width",String(Math.max(bw,2))); bar.setAttribute("height",String(bh)); bar.setAttribute("rx","3"); bar.setAttribute("fill",col); svg.appendChild(bar);
        const val=document.createElementNS("http://www.w3.org/2000/svg","text"); val.setAttribute("x",String(cl+cw+6)); val.setAttribute("y",String(y+bh-4)); val.setAttribute("class","corr-bar-chart-value"); val.textContent=String(it.value); svg.appendChild(val);
      });
    }
    function renderCorrHealthCard(a) {
      const s=a.healthStats; document.getElementById("corr-health-pass-rate").textContent=`${s.pass_rate}%`;
      document.getElementById("corr-health-fail-rate").textContent=`${s.fail_rate}%`; document.getElementById("corr-health-unknown-rate").textContent=`${s.unknown_rate}%`;
      document.getElementById("corr-health-issues-rate").textContent=`${s.issues_rate}%`; document.getElementById("corr-health-clean-rate").textContent=`${s.clean_rate}%`;
    }
    function renderCorrInsightsPanel(a) { const h=document.getElementById("corr-insights-list"); if(!h)return; h.innerHTML=""; a.insights.forEach(t=>{const d=document.createElement("div");d.className="corr-insight-item";d.textContent=t;h.appendChild(d);}); }
    function renderCorrelationAnalyticsDashboard(a) {
      renderCorrPassFailDonutChart(a); renderCorrHealthCard(a);
      renderCorrHorizontalBarChart("corr-top-chains-chart","corr-top-chains-empty", a.topFailingScanChains.map(c=>({label:c.scan_chain_id,value:c.fail_count})), "#f87171");
      renderCorrHorizontalBarChart("corr-top-patterns-chart","corr-top-patterns-empty", a.topFailingPatterns.map(p=>({label:p.pattern_id,value:Number(p.fail_count||0)})), "#fb923c");
      const dq = Array.from(a.dataQualityOverview.entries()).map(([label,value])=>({label,value,rawLabel:label})).sort((x,y)=>y.value-x.value||x.label.localeCompare(y.label));
      renderCorrHorizontalBarChart("corr-data-quality-chart","corr-data-quality-empty", dq, it => corrAnalyticsColor(it.rawLabel));
      renderCorrInsightsPanel(a);
    }
    function updateCorrelationAnalyticsVisibility(has) { const p=document.getElementById("corr-analytics-panel"); if(p)p.style.display=has?"block":"none"; }
    function refreshCorrelationAnalyticsDashboard() {
      if (!correlationOutcomeRecords.length) { updateCorrelationAnalyticsVisibility(false); return; }
      renderCorrelationAnalyticsDashboard(getOrComputeCorrelationAnalytics(correlationOutcomeRecords));
      updateCorrelationAnalyticsVisibility(true);
    }

    function runPatternOutcomeCorrelation() {
      const errorEl = document.getElementById("corr-error"), runBtn = document.getElementById("corr-run-btn");
      errorEl.style.display = "none"; runBtn.disabled = true; runBtn.textContent = "Running...";
      fetch("/api/correlate-pattern-outcomes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ input_stil: cpmReportData?.metadata?.stil_file || "" }) })
        .then(r => r.json().then(body => ({ ok: r.ok, body })))
        .then(({ ok, body }) => { if (!ok) throw new Error(body.detail || "Correlation failed."); lastCorrelationManifest = body.manifest || null; updateCorrelationSummaryPanel(lastCorrelationManifest); loadCorrelationOutcomeDataset(body); })
        .catch(err => { correlationOutcomeRecords = []; corrTableRenderToken++; corrPage = 0; invalidateCorrelationAnalyticsCache(); updateCorrelationAnalyticsVisibility(false); updateCorrelationExplorerVisibility(false); const tb=document.getElementById("corr-outcomes-table")?.querySelector("tbody"); if(tb)tb.innerHTML=""; closeCorrDetailDrawer(); errorEl.textContent=err.message||String(err); errorEl.style.display="block"; })
        .finally(() => { runBtn.disabled = false; runBtn.textContent = "Run Correlation"; });
    }
