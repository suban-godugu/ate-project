    /* PA-UI-007 PHASE 7 UI */
    let clusteringNavigationAvailable = false;
    let redundancyNavigationAvailable = false;
    let redundancyCandidateRecords = [];
    let redPage = 0;
    const redPageSize = 100;
    let redundancyTableRenderToken = 0;
    let redSearchQuery = "";
    let redSearchDebounceTimer = null;
    const redSearchDebounceMs = 250;
    let redActiveFilters = {
      confidence: "All",
      reviewStatus: "All",
      label: "All",
      cluster: "All",
    };
    let redSortKey = "confidence_score";
    let redSortDirection = "desc";
    const RED_CONFIDENCE_MAX = 0.5;
    let globalAnalyticsRows = [];
    let filteredGlobalAnalyticsRows = [];
    let globalAnalyticsPage = 0;
    const globalAnalyticsPageSize = 25;
    let globalAnalyticsSortField = "pattern_id";
    let globalAnalyticsSortAsc = true;
    let globalAnalyticsLazyObserver = null;
    let globalAnalyticsPendingReport = null;
    let globalAnalyticsRenderedKey = null;

    let storedClusteringPayload = null;
    let phase6ContentRendered = false;
    let phase6RenderedPayloadKey = null;

    let storedRedundancyPayload = null;
    let phase7ContentRendered = false;
    let phase7RenderedPayloadKey = null;
    function getClusteringPayloadKey(clustering) {
      if (!clustering) return "";
      const summary = clustering.summary || {};
      return [
        summary.cluster_version,
        clustering.canonical_cluster_hash,
        summary.total_clusters,
        summary.similarity_threshold,
      ].join("|");
    }
    function buildGlobalAnalyticsPayloadKey(report) {
      if (!report) return "";
      const metadata = report.metadata || {};
      const clustering = report.pattern_clustering || {};
      const summary = clustering.summary || {};
      const redundancy = report.pattern_redundancy || {};
      const coverage = report.toggle_coverage || {};
      return [
        metadata.pattern_count,
        metadata.vector_count,
        metadata.chain_count,
        summary.cluster_version,
        clustering.canonical_cluster_hash,
        (coverage.pattern_level || []).length,
        redundancy.total_candidates,
        redundancy.cluster_version,
      ].join("|");
    }
    function syncClusteringRecordsFromPayload(clustering) {
      if (!clustering) {
        clusterSummaryRecords = [];
        clusterAssignmentRecords = [];
        clusterAssignmentsAvailable = false;
        filteredClusterAssignments = [];
        return;
      }
      clusterSummaryRecords = clustering.cluster_summary || [];
      clusterAssignmentRecords = Array.isArray(clustering.pattern_assignments)
        ? clustering.pattern_assignments
        : [];
      clusterAssignmentsAvailable = Array.isArray(clustering.pattern_assignments);
      filteredClusterAssignments = [...clusterAssignmentRecords];
      refreshSimTopNClusterEnrichment();
    }

    function updateClusteringKpiCards(clustering) {
      if (!clustering) {
        document.getElementById("dash-clusters-val").textContent = "-";
        document.getElementById("dash-clusters-badge").textContent = "N/A";
        document.getElementById("dash-clusters-desc").textContent = "Hierarchical similarity groups (PA-FR-006)";
        return;
      }
      const summary = clustering.summary || {};
      document.getElementById("dash-clusters-val").textContent = (summary.total_clusters || 0).toLocaleString();
      document.getElementById("dash-clusters-badge").textContent = `v${summary.cluster_version || 1}`;
      document.getElementById("dash-clusters-desc").textContent = `${summary.algorithm || "Agglomerative"} @ ${summary.similarity_threshold || 0}`;
    }

    function updateRedundancyKpiCards(redundancy) {
      if (!redundancy) {
        document.getElementById("dash-redundant-val").textContent = "-";
        document.getElementById("dash-redundant-badge").textContent = "N/A";
        document.getElementById("dash-redundant-desc").textContent = "Pattern Redundancy (PA-FR-007)";
        return;
      }
      document.getElementById("dash-redundant-val").textContent =
        redundancy.total_candidates != null ? redundancy.total_candidates.toLocaleString() : "-";
      document.getElementById("dash-redundant-badge").textContent =
        redundancy.validation_status || "N/A";
      document.getElementById("dash-redundant-desc").textContent =
        redundancy.similarity_threshold != null
          ? `Threshold @ ${redundancy.similarity_threshold} (PA-FR-007)`
          : "Pattern Redundancy (PA-FR-007)";
    }

    function ensurePhase6Rendered() {
      const payloadKey = getClusteringPayloadKey(storedClusteringPayload);
      if (phase6ContentRendered && phase6RenderedPayloadKey === payloadKey) {
        return;
      }
      displayPatternClustering(storedClusteringPayload);
      phase6ContentRendered = true;
      phase6RenderedPayloadKey = payloadKey;
    }

    function ensurePhase7Rendered() {
      const payloadKey = getRedundancyPayloadKey(storedRedundancyPayload);
      if (phase7ContentRendered && phase7RenderedPayloadKey === payloadKey) {
        return;
      }
      displayPatternRedundancy(storedRedundancyPayload);
      phase7ContentRendered = true;
      phase7RenderedPayloadKey = payloadKey;
    }

    function applyClusteringPayloadFromReport(report) {
      if (report.pattern_clustering && report.pattern_clustering.status !== "ABORTED") {
        storedClusteringPayload = report.pattern_clustering;
        clusteringNavigationAvailable = true;
      } else {
        storedClusteringPayload = null;
        clusteringNavigationAvailable = !!report.pattern_embeddings;
      }
      phase6ContentRendered = false;
      syncClusteringRecordsFromPayload(storedClusteringPayload);
      updateClusteringKpiCards(storedClusteringPayload);
      if (storedClusteringPayload) {
        setClusterThresholdControlValue(storedClusteringPayload.summary?.similarity_threshold);
      }
      updateClusteringNavigationVisibility();
      if (activePhaseNum === 6) {
        ensurePhase6Rendered();
      }
    }

    function applyRedundancyPayloadFromReport(report) {
      if (report.pattern_redundancy && report.pattern_redundancy.status !== "ABORTED") {
        storedRedundancyPayload = report.pattern_redundancy;
        redundancyNavigationAvailable = true;
      } else {
        storedRedundancyPayload = null;
        redundancyNavigationAvailable = false;
      }
      phase7ContentRendered = false;
      updateRedundancyKpiCards(storedRedundancyPayload);
      updateRedundancyNavigationVisibility();
      if (activePhaseNum === 7) {
        ensurePhase7Rendered();
      }
    }

    function resetJsonTabCache() {
      jsonTabMaterialized = false;
      jsonTabMaterializedReport = null;
      document.getElementById("json-code-block").textContent = "";
    }

    function ensureJsonTabRendered() {
      if (!cpmReportData) return;
      if (jsonTabMaterialized && jsonTabMaterializedReport === cpmReportData) {
        return;
      }
      document.getElementById("json-code-block").textContent = JSON.stringify(cpmReportData, null, 2);
      jsonTabMaterialized = true;
      jsonTabMaterializedReport = cpmReportData;
    }

    function applyClusteringPayloadFromRecluster(clustering, similarityThreshold) {
      storedClusteringPayload = clustering || null;
      phase6ContentRendered = false;
      clusteringNavigationAvailable = true;
      syncClusteringRecordsFromPayload(storedClusteringPayload);
      updateClusteringKpiCards(storedClusteringPayload);
      setClusterThresholdControlValue(similarityThreshold);
      updateClusteringNavigationVisibility();
      if (activePhaseNum === 6) {
        ensurePhase6Rendered();
      }
    }

    function applyRedundancyPayloadFromRecluster(redundancy) {
      if (redundancy && redundancy.status !== "ABORTED") {
        storedRedundancyPayload = redundancy;
        redundancyNavigationAvailable = true;
      } else {
        storedRedundancyPayload = null;
        redundancyNavigationAvailable = false;
      }
      phase7ContentRendered = false;
      updateRedundancyKpiCards(storedRedundancyPayload);
      updateRedundancyNavigationVisibility();
      if (activePhaseNum === 7) {
        ensurePhase7Rendered();
      }
    }
    function resetJsonTabCache() {
      jsonTabMaterialized = false;
      jsonTabMaterializedReport = null;
      document.getElementById("json-code-block").textContent = "";
    }

    function ensureJsonTabRendered() {
      if (!cpmReportData) return;
      if (jsonTabMaterialized && jsonTabMaterializedReport === cpmReportData) {
        return;
      }
      document.getElementById("json-code-block").textContent = JSON.stringify(cpmReportData, null, 2);
      jsonTabMaterialized = true;
      jsonTabMaterializedReport = cpmReportData;
    }
    function updateClusteringNavigationVisibility() {
      const tabClusters = document.getElementById("tab-clusters-btn");
      if (!tabClusters) return;
      tabClusters.style.display = (activePhaseNum === 6 && clusteringNavigationAvailable) ? "block" : "none";
    }

    function updateRedundancyNavigationVisibility() {
      const tabRedundancy = document.getElementById("tab-redundancy-btn");
      if (!tabRedundancy) return;
      tabRedundancy.style.display = (activePhaseNum === 7 && redundancyNavigationAvailable) ? "block" : "none";
    }
    function queueGlobalAnalyticsDashboard(report) {
      if (!report) return;
      globalAnalyticsPendingReport = report;
      const section = document.getElementById("global-analytics-section");
      if (!section) return;
      section.style.display = "block";

      const tryRenderGlobalAnalytics = () => {
        if (!globalAnalyticsPendingReport) return;
        const pendingKey = buildGlobalAnalyticsPayloadKey(globalAnalyticsPendingReport);
        if (globalAnalyticsRenderedKey === pendingKey) {
          globalAnalyticsPendingReport = null;
          return;
        }
        renderGlobalAnalyticsDashboard(globalAnalyticsPendingReport);
        globalAnalyticsRenderedKey = pendingKey;
        globalAnalyticsPendingReport = null;
      };

      if (!globalAnalyticsLazyObserver) {
        globalAnalyticsLazyObserver = new IntersectionObserver(entries => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              tryRenderGlobalAnalytics();
            }
          });
        }, { rootMargin: "120px 0px" });
        globalAnalyticsLazyObserver.observe(section);
      }

      if (section.getBoundingClientRect().top < window.innerHeight + 120) {
        tryRenderGlobalAnalytics();
      }
    }
    function getConfidenceCategory(confidenceScore) {
      const score = Number(confidenceScore) || 0;
      if (score >= 0.45) return "Very High";
      if (score >= 0.40) return "High";
      if (score >= 0.30) return "Medium";
      return "Low";
    }

    function renderConfidenceBarDisplay(confidenceScore) {
      const score = Number(confidenceScore) || 0;
      const category = getConfidenceCategory(score);
      const pct = (score * 100).toFixed(1);
      const normalizedFill = Math.min(1, Math.max(0, score / RED_CONFIDENCE_MAX));
      const filledBlocks = Math.round(normalizedFill * 20);
      const bar = "█".repeat(filledBlocks) + "░".repeat(20 - filledBlocks);
      return { pct, category, bar, text: `${pct}%  ${category}  ${bar}` };
    }

    function buildRedundancySearchIndex(candidates) {
      candidates.forEach(candidate => {
        candidate._redSearchPatternA = String(candidate.pattern_a || "").toLowerCase();
        candidate._redSearchPatternB = String(candidate.pattern_b || "").toLowerCase();
        candidate._redSearchClusterId = String(candidate.cluster_id || "").toLowerCase();
      });
    }

    function matchesRedSearch(candidate, query) {
      if (!query) return true;
      const q = query.toLowerCase();
      return (
        candidate._redSearchPatternA.includes(q) ||
        candidate._redSearchPatternB.includes(q) ||
        candidate._redSearchClusterId.includes(q)
      );
    }

    function getDistinctClusterIds(candidates) {
      const clusterIds = new Set(candidates.map(candidate => String(candidate.cluster_id)));
      return Array.from(clusterIds).sort();
    }

    function readRedActiveFiltersFromUi() {
      return {
        confidence: document.getElementById("red-filter-confidence")?.value || "All",
        reviewStatus: document.getElementById("red-filter-review-status")?.value || "All",
        label: document.getElementById("red-filter-label")?.value || "All",
        cluster: document.getElementById("red-filter-cluster")?.value || "All",
      };
    }

    function applyRedFilters(rows, filters) {
      return rows.filter(candidate => {
        if (filters.confidence !== "All" && getConfidenceCategory(candidate.confidence_score) !== filters.confidence) {
          return false;
        }
        if (filters.reviewStatus !== "All" && candidate.review_status !== filters.reviewStatus) {
          return false;
        }
        if (filters.label !== "All" && candidate.label !== filters.label) {
          return false;
        }
        if (filters.cluster !== "All" && String(candidate.cluster_id) !== filters.cluster) {
          return false;
        }
        return true;
      });
    }

    function sortRedCandidates(rows, sortKey, sortDirection) {
      const sorted = rows.slice();
      const direction = sortDirection === "asc" ? 1 : -1;
      sorted.sort((left, right) => {
        let comparison = 0;
        if (sortKey === "pattern_a" || sortKey === "pattern_b") {
          comparison = comparePatternSortKey(left[sortKey], right[sortKey]);
        } else if (sortKey === "cluster_id") {
          comparison = String(left.cluster_id).localeCompare(String(right.cluster_id));
        } else if (sortKey === "raw_similarity" || sortKey === "confidence_score") {
          comparison = Number(left[sortKey]) - Number(right[sortKey]);
        } else if (sortKey === "review_status") {
          comparison = String(left.review_status || "").localeCompare(String(right.review_status || ""));
        }
        return comparison * direction;
      });
      return sorted;
    }

    function buildRedundancyVisibleDataset() {
      let rows = redundancyCandidateRecords.filter(candidate => matchesRedSearch(candidate, redSearchQuery));
      rows = applyRedFilters(rows, redActiveFilters);
      rows = sortRedCandidates(rows, redSortKey, redSortDirection);
      return rows;
    }

    function buildVisibleRedRows() {
      const filteredRows = buildRedundancyVisibleDataset();
      const start = redPage * redPageSize;
      const pageRows = filteredRows.slice(start, start + redPageSize);
      return {
        pageRows,
        filteredCount: filteredRows.length,
        filteredRows,
      };
    }

    function renderRedStatsLine(filteredCount, totalCount, pageStart, pageSize) {
      const shown = Math.min(pageSize, Math.max(0, filteredCount - pageStart));
      return `Showing ${shown.toLocaleString()} of ${filteredCount.toLocaleString()} filtered candidates (${totalCount.toLocaleString()} total)`;
    }

    function populateRedClusterFilterOptions() {
      const select = document.getElementById("red-filter-cluster");
      if (!select) return;
      const selected = select.value || "All";
      select.innerHTML = "";
      const allOption = document.createElement("option");
      allOption.value = "All";
      allOption.textContent = "All";
      select.appendChild(allOption);
      getDistinctClusterIds(redundancyCandidateRecords).forEach(clusterId => {
        const option = document.createElement("option");
        option.value = clusterId;
        option.textContent = clusterId;
        select.appendChild(option);
      });
      select.value = Array.from(select.options).some(option => option.value === selected) ? selected : "All";
    }

    function resetRedExplorerUiState() {
      redSearchQuery = "";
      redPage = 0;
      redSortKey = "confidence_score";
      redSortDirection = "desc";
      redActiveFilters = {
        confidence: "All",
        reviewStatus: "All",
        label: "All",
        cluster: "All",
      };
      const searchInput = document.getElementById("red-search-input");
      if (searchInput) searchInput.value = "";
      ["red-filter-confidence", "red-filter-review-status", "red-filter-label"].forEach(id => {
        const element = document.getElementById(id);
        if (element) element.value = "All";
      });
      updateRedSortIndicators();
    }

    function updateRedSortIndicators() {
      document.querySelectorAll("[data-red-sort-indicator]").forEach(element => {
        const key = element.getAttribute("data-red-sort-indicator");
        element.textContent = key === redSortKey ? (redSortDirection === "asc" ? "▲" : "▼") : "";
      });
    }

    function onRedSearchInput(event) {
      clearTimeout(redSearchDebounceTimer);
      redSearchDebounceTimer = setTimeout(() => {
        redSearchQuery = String(event.target.value || "").trim();
        redPage = 0;
        scheduleRedundancyCandidatesTableRender();
      }, redSearchDebounceMs);
    }

    function onRedFilterChange() {
      redActiveFilters = readRedActiveFiltersFromUi();
      redPage = 0;
      scheduleRedundancyCandidatesTableRender();
    }

    function onRedSortHeaderClick(sortKey) {
      if (redSortKey === sortKey) {
        redSortDirection = redSortDirection === "asc" ? "desc" : "asc";
      } else {
        redSortKey = sortKey;
        redSortDirection = sortKey === "pattern_a" || sortKey === "pattern_b" || sortKey === "cluster_id" || sortKey === "review_status" ? "asc" : "desc";
      }
      redPage = 0;
      updateRedSortIndicators();
      scheduleRedundancyCandidatesTableRender();
    }

    function openRedCandidateDrawer(candidate) {
      const drawer = document.getElementById("red-candidate-drawer");
      if (!drawer || !candidate) return;
      const confidenceDisplay = renderConfidenceBarDisplay(candidate.confidence_score);
      document.getElementById("red-drawer-pattern-a").textContent = candidate.pattern_a || "-";
      document.getElementById("red-drawer-pattern-b").textContent = candidate.pattern_b || "-";
      document.getElementById("red-drawer-cluster").textContent = candidate.cluster_id || "-";
      document.getElementById("red-drawer-raw-similarity").textContent = candidate.raw_similarity != null ? candidate.raw_similarity : "-";
      document.getElementById("red-drawer-confidence").textContent = confidenceDisplay.text;
      document.getElementById("red-drawer-confidence-category").textContent = confidenceDisplay.category;
      document.getElementById("red-drawer-embedding-version").textContent =
        storedRedundancyPayload?.embedding_version || "-";
      document.getElementById("red-drawer-validation-status").textContent =
        storedRedundancyPayload?.validation_status || "-";
      document.getElementById("red-drawer-review-status").textContent = candidate.review_status || "-";
      document.getElementById("red-drawer-label").textContent = candidate.label || "-";
      drawer.style.display = "flex";
    }

    function closeRedCandidateDrawer() {
      const drawer = document.getElementById("red-candidate-drawer");
      if (drawer) drawer.style.display = "none";
    }

    function closeRedCandidateDrawerOnBackdrop(event) {
      if (event.target && event.target.id === "red-candidate-drawer") {
        closeRedCandidateDrawer();
      }
    }

    function downloadRedBlob(content, filename, mimeType) {
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    }

    function escapeRedCsvValue(value) {
      const text = value == null ? "" : String(value);
      if (/[",\n]/.test(text)) {
        return `"${text.replace(/"/g, '""')}"`;
      }
      return text;
    }

    function getRedExportFieldNames(rows) {
      if (!rows.length) return [];
      return Object.keys(rows[0]).filter(key => !key.startsWith("_redSearch"));
    }

    async function buildRedExportCsvChunked(rows) {
      const fields = getRedExportFieldNames(rows);
      if (!fields.length) return "";
      const chunkSize = 5000;
      const lines = [fields.join(",")];
      for (let index = 0; index < rows.length; index += chunkSize) {
        const chunk = rows.slice(index, index + chunkSize);
        chunk.forEach(row => {
          lines.push(fields.map(field => escapeRedCsvValue(row[field])).join(","));
        });
        await new Promise(resolve => requestAnimationFrame(resolve));
      }
      return lines.join("\n");
    }

    async function buildRedExportJsonChunked(rows) {
      const chunkSize = 5000;
      let parts = ["["];
      for (let index = 0; index < rows.length; index += chunkSize) {
        const chunk = rows.slice(index, index + chunkSize).map(row => {
          const exportRow = {};
          getRedExportFieldNames([row]).forEach(field => {
            exportRow[field] = row[field];
          });
          return exportRow;
        });
        const serialized = chunk.map(item => JSON.stringify(item)).join(",");
        if (index > 0) parts.push(",");
        parts.push(serialized);
        await new Promise(resolve => requestAnimationFrame(resolve));
      }
      parts.push("]");
      return parts.join("");
    }

    async function exportRedRows(rows, format, filenamePrefix) {
      if (!rows.length) return;
      if (format === "csv") {
        const csv = await buildRedExportCsvChunked(rows);
        downloadRedBlob(csv, `${filenamePrefix}.csv`, "text/csv");
        return;
      }
      const json = await buildRedExportJsonChunked(rows);
      downloadRedBlob(json, `${filenamePrefix}.json`, "application/json");
    }

    function exportRedCurrentView(format) {
      if (format === "pdf") {
        exportRedundancyPdf(true);
        return;
      }
      const rows = buildRedundancyVisibleDataset();
      exportRedRows(rows, format, "redundancy_current_view");
    }

    function exportRedAll(format) {
      if (format === "pdf") {
        exportRedundancyPdf(false);
        return;
      }
      exportRedRows(redundancyCandidateRecords, format, "redundancy_all_candidates");
    }
    /* ========== PA-UI-007.4 / PA-UI-008.2 PDF Export (Isolated Module) ========== */

    function formatPdfTimestamp(date) {
      const value = date instanceof Date ? date : new Date();
      return value.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    }

    function formatPdfFilterSummary(filters, labels) {
      const parts = [];
      Object.entries(filters).forEach(([key, value]) => {
        if (value && value !== "All") {
          parts.push(`${labels[key] || key}: ${value}`);
        }
      });
      return parts.length ? parts.join("; ") : "None";
    }

    function formatPdfSortSummary(sortKey, sortDirection) {
      return `${sortKey} (${sortDirection})`;
    }

    async function buildPdfTableBodyRows(rows, columns, chunkSize) {
      const body = [];
      const size = chunkSize || 5000;
      for (let index = 0; index < rows.length; index += size) {
        const chunk = rows.slice(index, index + size);
        chunk.forEach(row => {
          body.push(columns.map(column => {
            const value = column.getValue ? column.getValue(row) : row[column.key];
            return value == null ? "" : String(value);
          }));
        });
        if (index + size < rows.length) {
          await new Promise(resolve => requestAnimationFrame(resolve));
        }
      }
      return body;
    }

    async function generatePdfReport(options) {
      if (!window.jspdf || !window.jspdf.jsPDF) {
        console.error("PDF library not loaded.");
        return;
      }
      const rows = options.rows || [];
      if (!rows.length) return;

      await new Promise(resolve => requestAnimationFrame(resolve));

      const { jsPDF } = window.jspdf;
      const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: "a4" });
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 14;
      const generatedAt = options.generatedAt || new Date();
      const totalPagesExp = "{total_pages_count_string}";

      let y = 16;
      doc.setFontSize(10);
      doc.setFont(undefined, "bold");
      doc.text("SCAN CHAIN PATTERN ANALYSIS AGENT", pageWidth / 2, y, { align: "center" });
      y += 7;
      doc.setFontSize(16);
      doc.text(options.reportTitle || "Analysis Report", pageWidth / 2, y, { align: "center" });
      y += 10;

      doc.setDrawColor(120);
      doc.setLineWidth(0.3);
      doc.line(margin, y, pageWidth - margin, y);
      y += 6;

      doc.setFontSize(9);
      doc.setFont(undefined, "bold");
      doc.text("Report Metadata", margin, y);
      y += 5;
      doc.setFont(undefined, "normal");
      (options.metadata || []).forEach(([label, value]) => {
        doc.text(`${label}: ${value == null ? "" : String(value)}`, margin, y);
        y += 4.5;
      });
      y += 3;

      doc.setFont(undefined, "bold");
      doc.text("Summary", margin, y);
      y += 5;
      doc.setFont(undefined, "normal");
      (options.summary || []).forEach(([label, value]) => {
        doc.text(`${label}: ${value == null ? "" : String(value)}`, margin, y);
        y += 4.5;
      });
      y += 4;

      const columns = options.columns || [];
      const head = [columns.map(column => column.label)];
      const body = await buildPdfTableBodyRows(rows, columns);

      doc.autoTable({
        startY: y,
        head,
        body,
        theme: "grid",
        styles: { fontSize: 7, cellPadding: 1.5, overflow: "linebreak" },
        headStyles: { fillColor: [55, 65, 81], textColor: 255, fontStyle: "bold", fontSize: 7 },
        margin: { left: margin, right: margin, top: margin, bottom: 16 },
        showHead: "everyPage",
        rowPageBreak: "avoid",
        didDrawPage: () => {
          const pageNum = doc.internal.getCurrentPageInfo().pageNumber;
          const footerY = pageHeight - 8;
          doc.setFontSize(7);
          doc.setFont(undefined, "normal");
          doc.text("Generated by SCAN CHAIN PATTERN ANALYSIS AGENT", margin, footerY);
          doc.text(formatPdfTimestamp(generatedAt), pageWidth / 2, footerY, { align: "center" });
          doc.text(`Page ${pageNum} of ${totalPagesExp}`, pageWidth - margin, footerY, { align: "right" });
        },
      });

      if (typeof doc.putTotalPages === "function") {
        doc.putTotalPages(totalPagesExp);
      }

      doc.save(options.filename || "report.pdf");
    }

    function buildRedundancyConfidenceDistribution(rows) {
      const distribution = { "Very High": 0, "High": 0, "Medium": 0, "Low": 0 };
      rows.forEach(row => {
        const category = getConfidenceCategory(row.confidence_score);
        distribution[category] = (distribution[category] || 0) + 1;
      });
      return Object.entries(distribution)
        .map(([category, count]) => `${category}: ${count}`)
        .join("; ");
    }

    function getRedundancyPdfColumns() {
      const validationStatus = storedRedundancyPayload?.validation_status || "-";
      return [
        { label: "Pattern A", key: "pattern_a" },
        { label: "Pattern B", key: "pattern_b" },
        { label: "Cluster", key: "cluster_id" },
        { label: "Similarity", getValue: row => row.raw_similarity != null ? row.raw_similarity : "" },
        { label: "Confidence", getValue: row => row.confidence_score != null ? row.confidence_score : "" },
        { label: "Confidence Category", getValue: row => getConfidenceCategory(row.confidence_score) },
        { label: "Validation Status", getValue: () => validationStatus },
        { label: "Review Status", key: "review_status" },
        { label: "Label", key: "label" },
      ];
    }

    async function exportRedundancyPdf(isCurrentView) {
      const exportType = isCurrentView ? "Current View" : "Export All";
      const rows = isCurrentView
        ? buildRedundancyVisibleDataset()
        : sortRedCandidates(redundancyCandidateRecords, redSortKey, redSortDirection);
      if (!rows.length) return;

      const generatedAt = new Date();
      const filteredCount = isCurrentView ? rows.length : buildRedundancyVisibleDataset().length;
      const clusterCount = new Set(rows.map(row => String(row.cluster_id))).size;
      const metadata = [
        ["Generation Date", generatedAt.toLocaleDateString()],
        ["Generation Time", generatedAt.toLocaleTimeString()],
        ["Export Type", exportType],
        ["Search Term", redSearchQuery || "None"],
        ["Applied Filters", formatPdfFilterSummary(redActiveFilters, {
          confidence: "Confidence",
          reviewStatus: "Review Status",
          label: "Label",
          cluster: "Cluster",
        })],
        ["Applied Sorting", formatPdfSortSummary(redSortKey, redSortDirection)],
        ["Embedding Version", storedRedundancyPayload?.embedding_version || "-"],
        ["Dataset Version", storedRedundancyPayload?.cluster_version || "-"],
      ];
      const summary = [
        ["Total Candidates", redundancyCandidateRecords.length.toLocaleString()],
        ["Filtered Candidates", isCurrentView ? filteredCount.toLocaleString() : "N/A (Export All)"],
        ["Visible Rows", rows.length.toLocaleString()],
        ["Cluster Count", clusterCount.toLocaleString()],
        ["Confidence Distribution", buildRedundancyConfidenceDistribution(rows)],
        ["Current Page", isCurrentView ? String(redPage + 1) : "All"],
      ];

      await generatePdfReport({
        reportTitle: "Pattern Redundancy Report",
        exportType,
        generatedAt,
        metadata,
        summary,
        columns: getRedundancyPdfColumns(),
        rows,
        filename: isCurrentView ? "pattern_redundancy_current_view.pdf" : "pattern_redundancy_all.pdf",
      });
    }

    function getSimTopNPdfColumns() {
      return [
        { label: "Rank", key: "rank" },
        { label: "Pattern ID", key: "pattern_id" },
        { label: "Similarity", getValue: row => row.similarity != null && typeof row.similarity === "number" ? row.similarity.toFixed(3) : (row.similarity ?? "") },
        { label: "Category", key: "category" },
        { label: "Cluster", getValue: row => row.cluster_id || "—" },
        { label: "Embedding Version", getValue: row => row.embedding_version || "—" },
        { label: "Latest Outcome", getValue: () => "Reserved for PA-FR-009" },
      ];
    }

    async function exportSimTopNPdf(isCurrentView) {
      const exportType = isCurrentView ? "Current View" : "Export All";
      const rows = isCurrentView
        ? buildSimTopNVisibleDataset()
        : sortSimTopNRows(simTopNRecords, simTopNSortKey, simTopNSortDirection);
      if (!rows.length) return;

      const generatedAt = new Date();
      const referencePattern = rows[0]?.reference_pattern || document.getElementById("sim-reference-pattern")?.value?.trim() || "-";
      const embeddingVersion = rows[0]?.embedding_version || "-";
      const clusterCount = new Set(rows.map(row => String(row.cluster_id)).filter(Boolean)).size;
      const metadata = [
        ["Generation Date", generatedAt.toLocaleDateString()],
        ["Generation Time", generatedAt.toLocaleTimeString()],
        ["Export Type", exportType],
        ["Search Term", simTopNSearchQuery || "None"],
        ["Applied Filters", formatPdfFilterSummary(simTopNActiveFilters, {
          category: "Category",
          range: "Range",
          cluster: "Cluster",
          embeddingVersion: "Embedding Version",
        })],
        ["Applied Sorting", formatPdfSortSummary(simTopNSortKey, simTopNSortDirection)],
        ["Embedding Version", embeddingVersion],
        ["Dataset Version", storedClusteringPayload?.summary?.cluster_version || "-"],
      ];
      const summary = [
        ["Reference Pattern", referencePattern],
        ["Requested Top-N", lastSimTopNResponseMeta.requested_top_n != null ? String(lastSimTopNResponseMeta.requested_top_n) : "-"],
        ["Returned Candidates", isCurrentView ? rows.length.toLocaleString() : (lastSimTopNResponseMeta.returned_count ?? rows.length).toLocaleString()],
        ["Embedding Version", embeddingVersion],
        ["Cluster Count", clusterCount.toLocaleString()],
        ["Current Page", isCurrentView ? String(simTopNPage + 1) : "All"],
      ];

      await generatePdfReport({
        reportTitle: "Pattern Similarity Report",
        exportType,
        generatedAt,
        metadata,
        summary,
        columns: getSimTopNPdfColumns(),
        rows,
        filename: isCurrentView ? "pattern_similarity_current_view.pdf" : "pattern_similarity_all.pdf",
      });
    }

    /* ========== End PDF Export Module ========== */
    function displayPatternRedundancy(redundancy) {
      if (!redundancy) {
        redundancyCandidateRecords = [];
        redPage = 0;
        redundancyTableRenderToken += 1;
        document.getElementById("dash-redundant-val").textContent = "-";
        document.getElementById("dash-redundant-badge").textContent = "N/A";
        document.getElementById("dash-redundant-desc").textContent = "Pattern Redundancy (PA-FR-007)";
        document.getElementById("red-total-candidates").textContent = "-";
        document.getElementById("red-clusters-evaluated").textContent = "-";
        document.getElementById("red-similarity-threshold").textContent = "-";
        document.getElementById("red-validation-status").textContent = "-";
        document.getElementById("red-embedding-version").textContent = "-";
        document.getElementById("red-cluster-version").textContent = "-";
        document.getElementById("red-candidates-per-cluster-avg").textContent = "-";
        document.getElementById("red-val-total-checks").textContent = "0";
        document.getElementById("red-val-passed").textContent = "0";
        document.getElementById("red-val-warnings").textContent = "0";
        document.getElementById("red-val-failed").textContent = "0";
        document.getElementById("red-candidates-table").querySelector("tbody").innerHTML = "";
        document.getElementById("red-validation-table").querySelector("tbody").innerHTML = "";
        document.getElementById("red-manifest-list").innerHTML = "";
        document.getElementById("red-candidates-empty").style.display = "none";
        updateRedundancyPaginationControls(0, 0, 0);
        closeRedCandidateDrawer();
        return;
      }

      const rollup = redundancy.file_rollup || {};
      document.getElementById("dash-redundant-val").textContent =
        redundancy.total_candidates != null ? redundancy.total_candidates.toLocaleString() : "-";
      document.getElementById("dash-redundant-badge").textContent =
        redundancy.validation_status || "N/A";
      document.getElementById("dash-redundant-desc").textContent =
        redundancy.similarity_threshold != null
          ? `Threshold @ ${redundancy.similarity_threshold} (PA-FR-007)`
          : "Pattern Redundancy (PA-FR-007)";

      document.getElementById("red-total-candidates").textContent =
        redundancy.total_candidates != null ? redundancy.total_candidates.toLocaleString() : "-";
      document.getElementById("red-clusters-evaluated").textContent =
        redundancy.clusters_evaluated != null ? redundancy.clusters_evaluated.toLocaleString() : "-";
      document.getElementById("red-similarity-threshold").textContent =
        redundancy.similarity_threshold != null ? redundancy.similarity_threshold : "-";
      document.getElementById("red-validation-status").textContent =
        redundancy.validation_status || "-";
      document.getElementById("red-embedding-version").textContent =
        redundancy.embedding_version || "-";
      document.getElementById("red-cluster-version").textContent =
        redundancy.cluster_version != null ? redundancy.cluster_version : "-";
      document.getElementById("red-candidates-per-cluster-avg").textContent =
        rollup.candidates_per_cluster_avg != null ? rollup.candidates_per_cluster_avg : "-";

      redundancyCandidateRecords = Array.isArray(redundancy.candidates) ? redundancy.candidates : [];
      buildRedundancySearchIndex(redundancyCandidateRecords);
      resetRedExplorerUiState();
      populateRedClusterFilterOptions();
      redPage = 0;
      scheduleRedundancyCandidatesTableRender();

      const validation = redundancy.validation_report || {};
      document.getElementById("red-val-total-checks").textContent =
        validation.total_checks != null ? validation.total_checks : 0;
      document.getElementById("red-val-passed").textContent =
        validation.passed != null ? validation.passed : 0;
      document.getElementById("red-val-warnings").textContent =
        validation.warnings != null ? validation.warnings : 0;
      document.getElementById("red-val-failed").textContent =
        validation.failed != null ? validation.failed : 0;

      const validationBody = document.getElementById("red-validation-table").querySelector("tbody");
      validationBody.innerHTML = "";
      (validation.checks || []).forEach(check => {
        const tr = document.createElement("tr");
        const tdRule = document.createElement("td");
        tdRule.textContent = check.rule || "";
        tr.appendChild(tdRule);
        const tdStatus = document.createElement("td");
        tdStatus.appendChild(renderDiagnosticBadge(check.status || "FAIL"));
        tr.appendChild(tdStatus);
        const tdDetails = document.createElement("td");
        tdDetails.textContent = check.details || "";
        tr.appendChild(tdDetails);
        validationBody.appendChild(tr);
      });

      const manifest = redundancy.manifest || {};
      const manifestList = document.getElementById("red-manifest-list");
      manifestList.innerHTML = "";
      [
        ["FR ID", manifest.fr_id],
        ["Generated Timestamp", manifest.generated_timestamp],
        ["Embedding Version", manifest.embedding_version],
        ["Cluster Version", manifest.cluster_version],
        ["Similarity Threshold", manifest.similarity_threshold],
        ["Total Candidates", manifest.total_candidates],
        ["Validation Status", manifest.validation_status],
        ["Manifest Version", manifest.manifest_version],
      ].forEach(([key, value]) => {
        const row = document.createElement("div");
        row.className = "diag-manifest-row";
        row.innerHTML = `<span class="diag-manifest-key">${key}</span><span class="diag-manifest-value">${value != null ? value : "-"}</span>`;
        manifestList.appendChild(row);
      });
    }

    function updateRedundancyPaginationControls(filteredCount, pageStart, pageEnd) {
      const total = redundancyCandidateRecords.length;
      const info = document.getElementById("red-pagination-info");
      const prevBtn = document.getElementById("btn-red-prev");
      const nextBtn = document.getElementById("btn-red-next");
      if (info) {
        info.textContent = renderRedStatsLine(filteredCount, total, pageStart, redPageSize);
      }
      if (prevBtn) prevBtn.disabled = redPage === 0;
      if (nextBtn) nextBtn.disabled = pageEnd >= filteredCount;
    }

    function scheduleRedundancyCandidatesTableRender() {
      const token = ++redundancyTableRenderToken;
      requestAnimationFrame(() => {
        if (token !== redundancyTableRenderToken) return;
        renderRedundancyCandidatesTable();
      });
    }

    function renderRedundancyCandidatesTable() {
      const tbody = document.getElementById("red-candidates-table").querySelector("tbody");
      const emptyState = document.getElementById("red-candidates-empty");
      tbody.innerHTML = "";

      if (!redundancyCandidateRecords.length) {
        emptyState.style.display = "block";
        emptyState.textContent = "No redundancy candidates were exported by PA-FR-007.";
        updateRedundancyPaginationControls(0, 0, 0);
        updateRedSortIndicators();
        return;
      }

      const { pageRows, filteredCount } = buildVisibleRedRows();
      const start = redPage * redPageSize;
      const end = Math.min(start + redPageSize, filteredCount);

      if (!filteredCount) {
        emptyState.style.display = "block";
        emptyState.textContent = "No candidates match the current search and filter criteria.";
        updateRedundancyPaginationControls(0, 0, 0);
        updateRedSortIndicators();
        return;
      }

      emptyState.style.display = "none";
      const fragment = document.createDocumentFragment();
      const confidenceDisplay = renderConfidenceBarDisplay;

      pageRows.forEach(candidate => {
        const tr = document.createElement("tr");
        tr.addEventListener("click", () => openRedCandidateDrawer(candidate));

        const appendCell = (value, className) => {
          const td = document.createElement("td");
          if (className) td.className = className;
          td.textContent = value != null ? value : "";
          tr.appendChild(td);
        };

        appendCell(candidate.pattern_a);
        appendCell(candidate.pattern_b);
        appendCell(candidate.cluster_id);
        appendCell(candidate.raw_similarity);
        appendCell(confidenceDisplay(candidate.confidence_score).text, "red-confidence-cell");
        appendCell(candidate.confidence_source);
        appendCell(candidate.review_status);
        appendCell(candidate.label);
        fragment.appendChild(tr);
      });
      tbody.appendChild(fragment);
      updateRedundancyPaginationControls(filteredCount, start, end);
      updateRedSortIndicators();
    }

    window.prevRedPage = function() {
      if (redPage > 0) {
        redPage -= 1;
        renderRedundancyCandidatesTable();
      }
    };

    window.nextRedPage = function() {
      const { filteredCount } = buildVisibleRedRows();
      if ((redPage + 1) * redPageSize < filteredCount) {
        redPage += 1;
        renderRedundancyCandidatesTable();
      }
    };
