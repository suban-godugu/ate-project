    /* PA-UI-008 PHASE 8 UI */
    let similarityNavigationAvailable = false;
    let phase8ContentInitialized = false;
    let similarityPatternIds = [];
    let similarityComboboxes = [];
    let simTopNRecords = [];
    let simTopNPage = 0;
    const simTopNPageSize = 100;
    let simTopNRenderToken = 0;
    let simTopNSearchQuery = "";
    let simTopNSearchDebounceTimer = null;
    const simTopNSearchDebounceMs = 250;
    let simTopNActiveFilters = {
      category: "All",
      range: "All",
      cluster: "All",
      embeddingVersion: "All",
    };
    let simTopNSortKey = "rank";
    let simTopNSortDirection = "asc";
    let simTopNSelectedRank = null;
    let lastSimTopNResponseMeta = {};
    function updateSimilarityKpiCards() {
      if (!similarityNavigationAvailable || !embeddingRecords.length) {
        document.getElementById("dash-similarity-val").textContent = "-";
        document.getElementById("dash-similarity-badge").textContent = "N/A";
        document.getElementById("dash-similarity-desc").textContent = "Pattern Similarity (PA-FR-008)";
        return;
      }
      document.getElementById("dash-similarity-val").textContent = embeddingRecords.length.toLocaleString();
      document.getElementById("dash-similarity-badge").textContent = "Ready";
      document.getElementById("dash-similarity-desc").textContent = "Global cosine similarity search (PA-FR-008)";
    }

    function updateSimilarityNavigationVisibility() {
      const tabSimilarity = document.getElementById("tab-similarity-btn");
      const tabCorrelation = document.getElementById("tab-correlation-btn");
      if (!tabSimilarity) return;
      tabSimilarity.style.display = (activePhaseNum === 8 && similarityNavigationAvailable) ? "block" : "none";
    }
    function applySimilarityNavigationFromReport(report) {
      similarityNavigationAvailable = !!(report.pattern_embeddings && report.pattern_embeddings.records && report.pattern_embeddings.records.length);
      phase8ContentInitialized = false;
      updateSimilarityKpiCards();
      updateSimilarityNavigationVisibility();
      if (activePhaseNum === 8) {
        ensurePhase8Initialized();
      }
    }

    function ensurePhase8Initialized() {
      if (phase8ContentInitialized) return;
      populateSimilarityPatternOptions();
      phase8ContentInitialized = true;
    }

    function patternSortKey(patternId) {
      return String(patternId)
        .split(/(\d+)/)
        .filter(part => part.length > 0)
        .map(part => (/^\d+$/.test(part) ? parseInt(part, 10) : part.toLowerCase()));
    }

    function comparePatternSortKey(a, b) {
      const left = patternSortKey(a);
      const right = patternSortKey(b);
      const length = Math.max(left.length, right.length);
      for (let index = 0; index < length; index += 1) {
        const leftPart = left[index];
        const rightPart = right[index];
        if (leftPart === undefined) return -1;
        if (rightPart === undefined) return 1;
        if (leftPart < rightPart) return -1;
        if (leftPart > rightPart) return 1;
      }
      return 0;
    }

    function filterSimilarityPatternIds(patternIds, query) {
      const normalized = String(query || "").trim().toUpperCase();
      if (!normalized) return patternIds;
      return patternIds.filter(patternId => String(patternId).toUpperCase().includes(normalized));
    }

    function closeAllSimilarityComboboxes(exceptCombobox) {
      similarityComboboxes.forEach(combobox => {
        if (combobox !== exceptCombobox) {
          combobox.close();
        }
      });
    }

    class SimilarityPatternCombobox {
      constructor(root, input, listbox) {
        this.root = root;
        this.input = input;
        this.listbox = listbox;
        this.patternIds = [];
        this.filteredIds = [];
        this.activeIndex = -1;
        this.isOpen = false;
        this.lastRenderSignature = "";
        this.renderScheduled = false;

        this.input.addEventListener("focus", () => {
          closeAllSimilarityComboboxes(this);
          this.open();
          this.scheduleRender();
        });
        this.input.addEventListener("input", () => {
          this.open();
          this.scheduleRender();
        });
        this.input.addEventListener("keydown", event => this.onKeyDown(event));
        this.listbox.addEventListener("mousedown", event => event.preventDefault());
        this.listbox.addEventListener("click", event => {
          const option = event.target.closest("[data-pattern-id]");
          if (!option) return;
          this.selectPattern(option.dataset.patternId);
        });
      }

      setPatternIds(patternIds) {
        this.patternIds = patternIds;
        if (this.isOpen) {
          this.scheduleRender();
        }
      }

      getFilterQuery() {
        return this.input.value;
      }

      open() {
        this.isOpen = true;
        this.input.setAttribute("aria-expanded", "true");
        this.listbox.classList.add("open");
      }

      close() {
        this.isOpen = false;
        this.activeIndex = -1;
        this.input.setAttribute("aria-expanded", "false");
        this.listbox.classList.remove("open");
      }

      selectPattern(patternId) {
        this.input.value = patternId;
        this.close();
        this.input.focus();
      }

      scheduleRender() {
        if (this.renderScheduled) return;
        this.renderScheduled = true;
        requestAnimationFrame(() => {
          this.renderScheduled = false;
          this.renderOptions();
        });
      }

      renderOptions() {
        const query = this.getFilterQuery();
        this.filteredIds = filterSimilarityPatternIds(this.patternIds, query);
        const signature = `${query}::${this.filteredIds.length}::${this.filteredIds[0] || ""}::${this.filteredIds[this.filteredIds.length - 1] || ""}`;
        if (signature === this.lastRenderSignature) {
          this.syncActiveOption();
          return;
        }
        this.lastRenderSignature = signature;
        this.listbox.innerHTML = "";

        if (!this.filteredIds.length) {
          const empty = document.createElement("li");
          empty.className = "sim-combobox-empty";
          empty.textContent = "No matching patterns.";
          empty.setAttribute("role", "presentation");
          this.listbox.appendChild(empty);
          this.activeIndex = -1;
          return;
        }

        if (this.activeIndex >= this.filteredIds.length) {
          this.activeIndex = this.filteredIds.length - 1;
        }
        if (this.activeIndex < 0 && this.isOpen) {
          this.activeIndex = 0;
        }

        const fragment = document.createDocumentFragment();
        this.filteredIds.forEach((patternId, index) => {
          const option = document.createElement("li");
          option.className = "sim-combobox-option";
          option.setAttribute("role", "option");
          option.dataset.patternId = patternId;
          option.textContent = patternId;
          option.id = `${this.input.id}-option-${index}`;
          if (index === this.activeIndex) {
            option.classList.add("active");
            option.setAttribute("aria-selected", "true");
            this.input.setAttribute("aria-activedescendant", option.id);
          } else {
            option.setAttribute("aria-selected", "false");
          }
          fragment.appendChild(option);
        });
        this.listbox.appendChild(fragment);
      }

      syncActiveOption() {
        const options = this.listbox.querySelectorAll(".sim-combobox-option");
        options.forEach((option, index) => {
          const isActive = index === this.activeIndex;
          option.classList.toggle("active", isActive);
          option.setAttribute("aria-selected", isActive ? "true" : "false");
          if (isActive) {
            this.input.setAttribute("aria-activedescendant", option.id);
            option.scrollIntoView({ block: "nearest" });
          }
        });
      }

      onKeyDown(event) {
        if (!this.isOpen && (event.key === "ArrowDown" || event.key === "ArrowUp")) {
          closeAllSimilarityComboboxes(this);
          this.open();
          this.scheduleRender();
          event.preventDefault();
          return;
        }
        if (!this.isOpen) return;

        if (event.key === "ArrowDown") {
          event.preventDefault();
          if (!this.filteredIds.length) return;
          this.activeIndex = Math.min(this.activeIndex + 1, this.filteredIds.length - 1);
          this.syncActiveOption();
        } else if (event.key === "ArrowUp") {
          event.preventDefault();
          if (!this.filteredIds.length) return;
          this.activeIndex = Math.max(this.activeIndex - 1, 0);
          this.syncActiveOption();
        } else if (event.key === "Enter") {
          if (this.activeIndex >= 0 && this.filteredIds[this.activeIndex]) {
            event.preventDefault();
            this.selectPattern(this.filteredIds[this.activeIndex]);
          }
        } else if (event.key === "Escape") {
          event.preventDefault();
          this.close();
          this.input.removeAttribute("aria-activedescendant");
        }
      }
    }

    function initSimilarityPatternComboboxes() {
      if (similarityComboboxes.length) return;
      const configs = [
        ["sim-combobox-a", "sim-pattern-a", "sim-pattern-a-listbox"],
        ["sim-combobox-b", "sim-pattern-b", "sim-pattern-b-listbox"],
        ["sim-combobox-ref", "sim-reference-pattern", "sim-reference-pattern-listbox"],
      ];
      similarityComboboxes = configs.map(([rootId, inputId, listboxId]) => {
        return new SimilarityPatternCombobox(
          document.getElementById(rootId),
          document.getElementById(inputId),
          document.getElementById(listboxId),
        );
      });
      if (!window.__similarityComboboxOutsideListenerBound) {
        document.addEventListener("mousedown", event => {
          const clickedInside = similarityComboboxes.some(combobox => combobox.root.contains(event.target));
          if (!clickedInside) {
            closeAllSimilarityComboboxes();
          }
        });
        window.__similarityComboboxOutsideListenerBound = true;
      }
    }

    function populateSimilarityPatternOptions() {
      similarityPatternIds = embeddingRecords
        .map(record => record && record.pattern_id)
        .filter(Boolean)
        .sort(comparePatternSortKey);
      initSimilarityPatternComboboxes();
      similarityComboboxes.forEach(combobox => combobox.setPatternIds(similarityPatternIds));
    }

    function clearSimilarityPairError() {
      const errorEl = document.getElementById("sim-pair-error");
      if (errorEl) {
        errorEl.style.display = "none";
        errorEl.textContent = "";
      }
    }

    function showSimilarityPairError(message) {
      const errorEl = document.getElementById("sim-pair-error");
      if (!errorEl) return;
      errorEl.textContent = message;
      errorEl.style.display = "block";
    }

    function clearSimilarityTopNError() {
      const errorEl = document.getElementById("sim-topn-error");
      if (errorEl) {
        errorEl.style.display = "none";
        errorEl.textContent = "";
      }
    }

    function showSimilarityTopNError(message) {
      const errorEl = document.getElementById("sim-topn-error");
      if (!errorEl) return;
      errorEl.textContent = message;
      errorEl.style.display = "block";
    }

    function renderPairwiseSimilarityResult(data) {
      document.getElementById("sim-pair-score").textContent =
        data.similarity_score != null ? data.similarity_score.toFixed(3) : "-";
      document.getElementById("sim-pair-category").textContent = data.category || "-";
      document.getElementById("sim-pair-latency").textContent =
        data.engine_latency_ms != null ? `${data.engine_latency_ms} ms` : "-";
      document.getElementById("sim-pair-sla").textContent =
        data.budget_exceeded ? "Budget Exceeded" : "Within Budget";
      document.getElementById("sim-pair-sla").style.color = data.budget_exceeded ? "#fbbf24" : "#34d399";
    }

    function buildPatternClusterLookupMap() {
      const map = {};
      (clusterAssignmentRecords || []).forEach(record => {
        if (record?.pattern_id != null && record?.cluster_id != null) {
          map[String(record.pattern_id).toUpperCase()] = String(record.cluster_id);
        }
      });
      return map;
    }

    function enrichSimTopNRecords(apiData) {
      const clusterMap = buildPatternClusterLookupMap();
      const referencePattern = apiData.reference_pattern || "";
      const embeddingVersion = apiData.embedding_version || "";
      return (apiData.results || []).map(row => ({
        ...row,
        reference_pattern: referencePattern,
        embedding_version: embeddingVersion,
        cluster_id: clusterMap[String(row.pattern_id || "").toUpperCase()] || "",
      }));
    }

    function buildSimTopNSearchIndex(rows) {
      rows.forEach(row => {
        row._simSearchReference = String(row.reference_pattern || "").toLowerCase();
        row._simSearchPatternId = String(row.pattern_id || "").toLowerCase();
        row._simSearchClusterId = String(row.cluster_id || "").toLowerCase();
      });
    }

    function refreshSimTopNClusterEnrichment() {
      if (!simTopNRecords.length) return;
      const clusterMap = buildPatternClusterLookupMap();
      simTopNRecords.forEach(row => {
        row.cluster_id = clusterMap[String(row.pattern_id || "").toUpperCase()] || "";
        row._simSearchClusterId = String(row.cluster_id || "").toLowerCase();
      });
      populateSimTopNClusterFilterOptions();
      scheduleSimilarityTopNTableRender();
    }

    function getSimSimilarityRangeBucket(score) {
      const value = Number(score) || 0;
      if (value >= 0.99) return "99–100%";
      if (value >= 0.95) return "95–99%";
      if (value >= 0.90) return "90–95%";
      if (value >= 0.80) return "80–90%";
      return "Below 80%";
    }

    function matchesSimSimilarityRange(row, rangeFilter) {
      if (!rangeFilter || rangeFilter === "All") return true;
      return getSimSimilarityRangeBucket(row.similarity) === rangeFilter;
    }

    function matchesSimTopNSearch(row, query) {
      if (!query) return true;
      const normalized = query.toLowerCase();
      return (
        row._simSearchReference.includes(normalized) ||
        row._simSearchPatternId.includes(normalized) ||
        row._simSearchClusterId.includes(normalized)
      );
    }

    function readSimTopNActiveFiltersFromUi() {
      return {
        category: document.getElementById("sim-filter-category")?.value || "All",
        range: document.getElementById("sim-filter-range")?.value || "All",
        cluster: document.getElementById("sim-filter-cluster")?.value || "All",
        embeddingVersion: document.getElementById("sim-filter-embedding-version")?.value || "All",
      };
    }

    function applySimTopNFilters(rows, filters) {
      return rows.filter(row => {
        if (filters.category !== "All" && row.category !== filters.category) {
          return false;
        }
        if (!matchesSimSimilarityRange(row, filters.range)) {
          return false;
        }
        if (filters.cluster !== "All" && String(row.cluster_id) !== filters.cluster) {
          return false;
        }
        if (filters.embeddingVersion !== "All" && row.embedding_version !== filters.embeddingVersion) {
          return false;
        }
        return true;
      });
    }

    function sortSimTopNRows(rows, sortKey, sortDirection) {
      const sorted = rows.slice();
      const direction = sortDirection === "asc" ? 1 : -1;
      sorted.sort((left, right) => {
        let comparison = 0;
        if (sortKey === "rank") {
          comparison = Number(left.rank) - Number(right.rank);
        } else if (sortKey === "pattern_id") {
          comparison = comparePatternSortKey(left.pattern_id, right.pattern_id);
        } else if (sortKey === "similarity") {
          comparison = Number(left.similarity) - Number(right.similarity);
        } else if (sortKey === "category") {
          comparison = String(left.category || "").localeCompare(String(right.category || ""));
        } else if (sortKey === "cluster_id") {
          comparison = String(left.cluster_id || "").localeCompare(String(right.cluster_id || ""));
        } else if (sortKey === "embedding_version") {
          comparison = String(left.embedding_version || "").localeCompare(String(right.embedding_version || ""));
        }
        return comparison * direction;
      });
      return sorted;
    }

    function buildSimTopNVisibleDataset() {
      let rows = simTopNRecords.filter(row => matchesSimTopNSearch(row, simTopNSearchQuery));
      rows = applySimTopNFilters(rows, simTopNActiveFilters);
      rows = sortSimTopNRows(rows, simTopNSortKey, simTopNSortDirection);
      return rows;
    }

    function buildVisibleSimTopRows() {
      const filteredRows = buildSimTopNVisibleDataset();
      const start = simTopNPage * simTopNPageSize;
      const pageRows = filteredRows.slice(start, start + simTopNPageSize);
      return {
        pageRows,
        filteredCount: filteredRows.length,
        filteredRows,
      };
    }

    function renderSimTopNStatsLine(filteredCount, totalCount, pageStart, pageSize) {
      const shown = Math.min(pageSize, Math.max(0, filteredCount - pageStart));
      return `Showing ${shown.toLocaleString()} of ${filteredCount.toLocaleString()} filtered results (${totalCount.toLocaleString()} total)`;
    }

    function getDistinctSimClusterIds(rows) {
      const clusterIds = new Set();
      rows.forEach(row => {
        if (row.cluster_id) clusterIds.add(String(row.cluster_id));
      });
      return Array.from(clusterIds).sort();
    }

    function populateSimTopNClusterFilterOptions() {
      const select = document.getElementById("sim-filter-cluster");
      if (!select) return;
      const selected = select.value || "All";
      select.innerHTML = "";
      const allOption = document.createElement("option");
      allOption.value = "All";
      allOption.textContent = "All";
      select.appendChild(allOption);
      getDistinctSimClusterIds(simTopNRecords).forEach(clusterId => {
        const option = document.createElement("option");
        option.value = clusterId;
        option.textContent = clusterId;
        select.appendChild(option);
      });
      select.value = Array.from(select.options).some(option => option.value === selected) ? selected : "All";
    }

    function populateSimTopNEmbeddingVersionFilterOptions() {
      const select = document.getElementById("sim-filter-embedding-version");
      if (!select) return;
      const selected = select.value || "All";
      const versions = new Set();
      simTopNRecords.forEach(row => {
        if (row.embedding_version) versions.add(String(row.embedding_version));
      });
      select.innerHTML = "";
      const allOption = document.createElement("option");
      allOption.value = "All";
      allOption.textContent = "All";
      select.appendChild(allOption);
      Array.from(versions).sort().forEach(version => {
        const option = document.createElement("option");
        option.value = version;
        option.textContent = version;
        select.appendChild(option);
      });
      select.value = Array.from(select.options).some(option => option.value === selected) ? selected : "All";
    }

    function resetSimExplorerUiState() {
      simTopNSearchQuery = "";
      simTopNPage = 0;
      simTopNSortKey = "rank";
      simTopNSortDirection = "asc";
      simTopNSelectedRank = null;
      simTopNActiveFilters = {
        category: "All",
        range: "All",
        cluster: "All",
        embeddingVersion: "All",
      };
      const searchInput = document.getElementById("sim-topn-search-input");
      if (searchInput) searchInput.value = "";
      ["sim-filter-category", "sim-filter-range", "sim-filter-cluster", "sim-filter-embedding-version"].forEach(id => {
        const element = document.getElementById(id);
        if (element) element.value = "All";
      });
      updateSimTopNSortIndicators();
    }

    function updateSimTopNSortIndicators() {
      document.querySelectorAll("[data-sim-sort-indicator]").forEach(element => {
        const key = element.getAttribute("data-sim-sort-indicator");
        element.textContent = key === simTopNSortKey ? (simTopNSortDirection === "asc" ? "▲" : "▼") : "";
      });
    }

    function onSimTopNSearchInput(event) {
      clearTimeout(simTopNSearchDebounceTimer);
      simTopNSearchDebounceTimer = setTimeout(() => {
        simTopNSearchQuery = String(event.target.value || "").trim();
        simTopNPage = 0;
        scheduleSimilarityTopNTableRender();
      }, simTopNSearchDebounceMs);
    }

    function onSimTopNFilterChange() {
      simTopNActiveFilters = readSimTopNActiveFiltersFromUi();
      simTopNPage = 0;
      scheduleSimilarityTopNTableRender();
    }

    function onSimTopNSortHeaderClick(sortKey) {
      if (simTopNSortKey === sortKey) {
        simTopNSortDirection = simTopNSortDirection === "asc" ? "desc" : "asc";
      } else {
        simTopNSortKey = sortKey;
        simTopNSortDirection = sortKey === "rank" || sortKey === "pattern_id" || sortKey === "category" || sortKey === "cluster_id" || sortKey === "embedding_version" ? "asc" : "desc";
      }
      simTopNPage = 0;
      updateSimTopNSortIndicators();
      scheduleSimilarityTopNTableRender();
    }

    function renderSimilarityBarDisplay(similarityScore) {
      const score = Number(similarityScore) || 0;
      const pct = (score * 100).toFixed(1);
      const filledBlocks = Math.round(Math.min(1, Math.max(0, score)) * 20);
      const bar = "█".repeat(filledBlocks) + "░".repeat(20 - filledBlocks);
      return { pct, bar, text: `${pct}%  ${bar}` };
    }

    function getSimDrawerValidationStatus() {
      const clustering = storedClusteringPayload || cpmReportData?.pattern_clustering;
      return clustering?.diagnostics?.validation_status
        || clustering?.validation_status
        || "-";
    }

    function openSimSimilarityDrawer(row) {
      const drawer = document.getElementById("sim-similarity-drawer");
      if (!drawer || !row) return;
      simTopNSelectedRank = row.rank;
      const similarityDisplay = renderSimilarityBarDisplay(row.similarity);
      document.getElementById("sim-drawer-reference").textContent = row.reference_pattern || "-";
      document.getElementById("sim-drawer-pattern").textContent = row.pattern_id || "-";
      document.getElementById("sim-drawer-score").textContent = row.similarity != null ? Number(row.similarity).toFixed(6) : "-";
      document.getElementById("sim-drawer-percentage").textContent = `${similarityDisplay.pct}%`;
      document.getElementById("sim-drawer-category").textContent = row.category || "-";
      document.getElementById("sim-drawer-rank").textContent = row.rank != null ? row.rank : "-";
      document.getElementById("sim-drawer-cluster").textContent = row.cluster_id || "-";
      document.getElementById("sim-drawer-embedding-version").textContent = row.embedding_version || "-";
      document.getElementById("sim-drawer-validation-status").textContent = getSimDrawerValidationStatus();
      drawer.style.display = "flex";
      scheduleSimilarityTopNTableRender();
    }

    function closeSimSimilarityDrawer() {
      const drawer = document.getElementById("sim-similarity-drawer");
      if (drawer) drawer.style.display = "none";
    }

    function closeSimSimilarityDrawerOnBackdrop(event) {
      if (event.target && event.target.id === "sim-similarity-drawer") {
        closeSimSimilarityDrawer();
      }
    }

    function escapeSimCsvValue(value) {
      const text = value == null ? "" : String(value);
      if (/[",\n]/.test(text)) {
        return `"${text.replace(/"/g, '""')}"`;
      }
      return text;
    }

    function getSimExportFieldNames(rows) {
      if (!rows.length) return [];
      return Object.keys(rows[0]).filter(key => !key.startsWith("_simSearch"));
    }

    async function buildSimExportCsvChunked(rows) {
      const fields = getSimExportFieldNames(rows);
      if (!fields.length) return "";
      const chunkSize = 5000;
      const lines = [fields.join(",")];
      for (let index = 0; index < rows.length; index += chunkSize) {
        const chunk = rows.slice(index, index + chunkSize);
        chunk.forEach(row => {
          lines.push(fields.map(field => escapeSimCsvValue(row[field])).join(","));
        });
        await new Promise(resolve => requestAnimationFrame(resolve));
      }
      return lines.join("\n");
    }

    async function buildSimExportJsonChunked(rows) {
      const chunkSize = 5000;
      let parts = ["["];
      for (let index = 0; index < rows.length; index += chunkSize) {
        const chunk = rows.slice(index, index + chunkSize).map(row => {
          const exportRow = {};
          getSimExportFieldNames([row]).forEach(field => {
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

    function downloadSimBlob(content, filename, mimeType) {
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

    async function exportSimRows(rows, format, filenamePrefix) {
      if (!rows.length) return;
      if (format === "csv") {
        const csv = await buildSimExportCsvChunked(rows);
        downloadSimBlob(csv, `${filenamePrefix}.csv`, "text/csv;charset=utf-8");
      } else {
        const json = await buildSimExportJsonChunked(rows);
        downloadSimBlob(json, `${filenamePrefix}.json`, "application/json;charset=utf-8");
      }
    }

    function exportSimTopNCurrentView(format) {
      if (format === "pdf") {
        exportSimTopNPdf(true);
        return;
      }
      const rows = buildSimTopNVisibleDataset();
      exportSimRows(rows, format, "similarity_topn_current_view");
    }

    function exportSimTopNAll(format) {
      if (format === "pdf") {
        exportSimTopNPdf(false);
        return;
      }
      exportSimRows(simTopNRecords, format, "similarity_topn_all");
    }

    function updateSimilarityTopNPaginationControls(filteredCount, totalCount, pageStart, pageEnd) {
      const rangeStart = filteredCount === 0 ? 0 : pageStart + 1;
      const info = document.getElementById("sim-topn-pagination-info");
      const prevBtn = document.getElementById("btn-sim-topn-prev");
      const nextBtn = document.getElementById("btn-sim-topn-next");
      if (info) {
        info.textContent = renderSimTopNStatsLine(filteredCount, totalCount, pageStart, pageEnd - pageStart);
      }
      if (prevBtn) prevBtn.disabled = simTopNPage === 0;
      if (nextBtn) nextBtn.disabled = pageEnd >= filteredCount;
    }

    function scheduleSimilarityTopNTableRender() {
      const token = ++simTopNRenderToken;
      requestAnimationFrame(() => {
        if (token !== simTopNRenderToken) return;
        renderSimilarityTopNTable();
      });
    }

    function renderSimilarityTopNTable() {
      const tbody = document.getElementById("sim-topn-table").querySelector("tbody");
      const emptyState = document.getElementById("sim-topn-empty");
      tbody.innerHTML = "";

      if (!simTopNRecords.length) {
        emptyState.style.display = "block";
        emptyState.textContent = "No similarity results to display.";
        updateSimilarityTopNPaginationControls(0, 0, 0, 0);
        updateSimTopNSortIndicators();
        return;
      }

      const { pageRows, filteredCount } = buildVisibleSimTopRows();
      const totalCount = simTopNRecords.length;
      const start = simTopNPage * simTopNPageSize;
      const end = start + pageRows.length;

      if (!filteredCount) {
        emptyState.style.display = "block";
        emptyState.textContent = "No results match the current search and filter criteria.";
        updateSimilarityTopNPaginationControls(0, totalCount, 0, 0);
        updateSimTopNSortIndicators();
        return;
      }

      emptyState.style.display = "none";
      const fragment = document.createDocumentFragment();

      pageRows.forEach(row => {
        const tr = document.createElement("tr");
        if (simTopNSelectedRank != null && row.rank === simTopNSelectedRank) {
          tr.classList.add("sim-topn-row-selected");
        }
        tr.addEventListener("click", () => openSimSimilarityDrawer(row));

        const rankTd = document.createElement("td");
        rankTd.textContent = row.rank != null ? row.rank : "";
        tr.appendChild(rankTd);

        const patternTd = document.createElement("td");
        patternTd.textContent = row.pattern_id != null ? row.pattern_id : "";
        patternTd.style.fontFamily = "var(--font-mono)";
        tr.appendChild(patternTd);

        const similarityTd = document.createElement("td");
        similarityTd.className = "sim-similarity-cell";
        similarityTd.textContent = row.similarity != null && typeof row.similarity === "number"
          ? row.similarity.toFixed(3)
          : (row.similarity != null ? row.similarity : "");
        tr.appendChild(similarityTd);

        const barTd = document.createElement("td");
        barTd.className = "sim-similarity-cell";
        barTd.textContent = renderSimilarityBarDisplay(row.similarity).text;
        tr.appendChild(barTd);

        const categoryTd = document.createElement("td");
        categoryTd.textContent = row.category != null ? row.category : "";
        tr.appendChild(categoryTd);

        const clusterTd = document.createElement("td");
        clusterTd.textContent = row.cluster_id || "—";
        tr.appendChild(clusterTd);

        const embeddingTd = document.createElement("td");
        embeddingTd.textContent = row.embedding_version || "—";
        tr.appendChild(embeddingTd);

        const outcomeTd = document.createElement("td");
        outcomeTd.className = "sim-placeholder-cell";
        outcomeTd.textContent = "Reserved for PA-FR-009";
        tr.appendChild(outcomeTd);

        const actionsTd = document.createElement("td");
        actionsTd.className = "sim-placeholder-cell";
        actionsTd.textContent = "Row click for details";
        tr.appendChild(actionsTd);

        fragment.appendChild(tr);
      });
      tbody.appendChild(fragment);
      updateSimilarityTopNPaginationControls(filteredCount, totalCount, start, end);
      updateSimTopNSortIndicators();
    }

    window.prevSimTopNPage = function() {
      if (simTopNPage > 0) {
        simTopNPage -= 1;
        scheduleSimilarityTopNTableRender();
      }
    };

    window.nextSimTopNPage = function() {
      const { filteredCount } = buildVisibleSimTopRows();
      if ((simTopNPage + 1) * simTopNPageSize < filteredCount) {
        simTopNPage += 1;
        scheduleSimilarityTopNTableRender();
      }
    };

    window.runPairwiseSimilarity = function() {
      clearSimilarityPairError();
      const patternA = document.getElementById("sim-pattern-a").value.trim();
      const patternB = document.getElementById("sim-pattern-b").value.trim();
      if (!patternA || !patternB) {
        showSimilarityPairError("Select Pattern A and Pattern B to compare.");
        return;
      }
      const btn = document.getElementById("sim-pair-btn");
      btn.disabled = true;
      fetch("/api/similarity/pair", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pattern_a: patternA, pattern_b: patternB }),
      })
        .then(async response => {
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.detail || "Unable to compute similarity.");
          }
          return data;
        })
        .then(data => {
          renderPairwiseSimilarityResult(data);
        })
        .catch(error => {
          showSimilarityPairError(error.message || "Unable to compute similarity — pattern embedding not found.");
        })
        .finally(() => {
          btn.disabled = false;
        });
    };

    window.runTopNSimilarity = function() {
      clearSimilarityTopNError();
      const referencePattern = document.getElementById("sim-reference-pattern").value.trim();
      const topN = parseInt(document.getElementById("sim-top-n").value, 10);
      if (!referencePattern) {
        showSimilarityTopNError("Select a reference pattern to analyze.");
        return;
      }
      if (Number.isNaN(topN) || topN < 1) {
        showSimilarityTopNError("Top N must be at least 1.");
        return;
      }
      const btn = document.getElementById("sim-topn-btn");
      btn.disabled = true;
      fetch("/api/similarity/top-n", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reference_pattern: referencePattern, top_n: topN }),
      })
        .then(async response => {
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.detail || "Unable to compute Top-N similarity.");
          }
          return data;
        })
        .then(data => {
          lastSimTopNResponseMeta = {
            requested_top_n: data.requested_top_n,
            returned_count: data.returned_count,
            available_count: data.available_count,
            partial_result: data.partial_result,
            budget_exceeded: data.budget_exceeded,
          };
          resetSimExplorerUiState();
          simTopNRecords = enrichSimTopNRecords(data);
          buildSimTopNSearchIndex(simTopNRecords);
          populateSimTopNClusterFilterOptions();
          populateSimTopNEmbeddingVersionFilterOptions();
          const meta = document.getElementById("sim-topn-meta");
          if (meta) {
            meta.style.display = "block";
            meta.textContent = `Requested ${data.requested_top_n}, returned ${data.returned_count} of ${data.available_count} available candidates.` +
              (data.partial_result ? " Partial result." : "") +
              (data.budget_exceeded ? " Engine response exceeded configured budget." : "");
          }
          scheduleSimilarityTopNTableRender();
        })
        .catch(error => {
          simTopNRecords = [];
          simTopNPage = 0;
          simTopNRenderToken += 1;
          lastSimTopNResponseMeta = {};
          resetSimExplorerUiState();
          document.getElementById("sim-topn-table").querySelector("tbody").innerHTML = "";
          document.getElementById("sim-topn-meta").style.display = "none";
          updateSimilarityTopNPaginationControls(0, 0, 0, 0);
          showSimilarityTopNError(error.message || "Unable to compute similarity — pattern embedding not found.");
        })
        .finally(() => {
          btn.disabled = false;
        });
    };
