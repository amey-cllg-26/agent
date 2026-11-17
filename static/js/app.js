/**
 * ScholarshipFinder - Client Application Logic
 * Professional Academic Directory & Dataset Matching Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  // Application State
  let currentDatasetStats = null;
  let allMatchedResults = [];
  let overBudgetResults = [];
  let currentFitFilter = "all";
  let activeViewMode = "grid"; // 'grid' | 'table'
  let chatSessionId = "session-" + Math.random().toString(36).substring(2, 9);

  // DOM Elements - Navigation & Dataset
  const activeDatasetName = document.getElementById("activeDatasetName");
  const activeDatasetCount = document.getElementById("activeDatasetCount");
  const openDatasetModalBtn = document.getElementById("openDatasetModalBtn");
  const datasetModal = document.getElementById("datasetModal");
  const closeDatasetModalBtn = document.getElementById("closeDatasetModalBtn");

  // Modal dataset stats
  const modalDatasetFilename = document.getElementById("modalDatasetFilename");
  const modalDatasetCount = document.getElementById("modalDatasetCount");
  const modalDatasetCountries = document.getElementById("modalDatasetCountries");
  const modalDatasetFunding = document.getElementById("modalDatasetFunding");
  const csvDropZone = document.getElementById("csvDropZone");
  const csvFileInput = document.getElementById("csvFileInput");
  const uploadFeedback = document.getElementById("uploadFeedback");
  const revertDefaultDatasetBtn = document.getElementById("revertDefaultDatasetBtn");

  // Search & Filter Elements
  const keywordSearchInput = document.getElementById("keywordSearchInput");
  const mainSearchBtn = document.getElementById("mainSearchBtn");
  const filterForm = document.getElementById("filterForm");
  const clearAllFiltersBtn = document.getElementById("clearAllFiltersBtn");
  const cgpaInput = document.getElementById("cgpaInput");
  const cgpaScale = document.getElementById("cgpaScale");
  const cgpaConversionText = document.getElementById("cgpaConversionText");
  const budgetRange = document.getElementById("budgetRange");
  const budgetInput = document.getElementById("budgetInput");
  const budgetLabel = document.getElementById("budgetLabel");
  const quickPills = document.querySelectorAll(".quick-pill");
  const countryFilter = document.getElementById("countryFilter");
  const coverageFilter = document.getElementById("coverageFilter");
  const nationalityInput = document.getElementById("nationalityInput");

  // Results Elements
  const resultsCountHeader = document.getElementById("resultsCountHeader");
  const activeFilterTags = document.getElementById("activeFilterTags");
  const resultsGrid = document.getElementById("resultsGrid");
  const resultsTableContainer = document.getElementById("resultsTableContainer");
  const resultsTableBody = document.getElementById("resultsTableBody");
  const overBudgetContainer = document.getElementById("overBudgetContainer");
  const overBudgetGrid = document.getElementById("overBudgetGrid");
  const emptyResultsState = document.getElementById("emptyResultsState");
  const emptyResetBtn = document.getElementById("emptyResetBtn");
  const viewGridBtn = document.getElementById("viewGridBtn");
  const viewTableBtn = document.getElementById("viewTableBtn");

  // Fit tab counts
  const countAll = document.getElementById("countAll");
  const countTarget = document.getElementById("countTarget");
  const countSafer = document.getElementById("countSafer");
  const countReach = document.getElementById("countReach");
  const fitTabs = document.querySelectorAll(".fit-tab");

  // Detail Modal Elements
  const detailModal = document.getElementById("detailModal");
  const closeDetailModalBtn = document.getElementById("closeDetailModalBtn");
  const closeDetailFooterBtn = document.getElementById("closeDetailFooterBtn");
  const detailCountryTag = document.getElementById("detailCountryTag");
  const detailTitle = document.getElementById("detailTitle");
  const detailFunder = document.getElementById("detailFunder");
  const detailBody = document.getElementById("detailBody");
  const detailOfficialLink = document.getElementById("detailOfficialLink");

  // Advisor Drawer Elements
  const toggleAdvisorDrawerBtn = document.getElementById("toggleAdvisorDrawerBtn");
  const advisorDrawer = document.getElementById("advisorDrawer");
  const advisorDrawerOverlay = document.getElementById("advisorDrawerOverlay");
  const closeAdvisorDrawerBtn = document.getElementById("closeAdvisorDrawerBtn");
  const advisorForm = document.getElementById("advisorForm");
  const advisorInput = document.getElementById("advisorInput");
  const advisorMessages = document.getElementById("advisorMessages");
  const promptChips = document.querySelectorAll(".prompt-chip");

  // Toast Area
  const toastArea = document.getElementById("toastArea");

  // ================= 1. BUDGET CONTROLS & GPA SCALE =================
  function setBudgetValue(val) {
    const num = Math.max(0, parseInt(val) || 0);
    budgetRange.value = num;
    budgetInput.value = num;
    budgetLabel.textContent = `$${num.toLocaleString()} / yr`;
  }

  budgetRange.addEventListener("input", (e) => setBudgetValue(e.target.value));
  budgetInput.addEventListener("input", (e) => setBudgetValue(e.target.value));

  quickPills.forEach(pill => {
    pill.addEventListener("click", () => {
      setBudgetValue(pill.dataset.budget);
      triggerSearch();
    });
  });

  function updateCgpaNote() {
    const val = parseFloat(cgpaInput.value) || 0;
    const scale = parseFloat(cgpaScale.value) || 4.0;
    let converted = val;
    if (scale === 100) {
      if (val >= 85) converted = 4.0;
      else if (val >= 80) converted = 3.7;
      else if (val >= 75) converted = 3.3;
      else if (val >= 70) converted = 3.0;
      else converted = 2.5;
    } else if (scale !== 4) {
      converted = Math.round((val / scale) * 4 * 100) / 100;
    }
    cgpaConversionText.textContent = `Approximate US Scale: ${converted.toFixed(2)} / 4.0`;
  }

  cgpaInput.addEventListener("input", updateCgpaNote);
  cgpaScale.addEventListener("change", updateCgpaNote);

  // ================= 2. DATASET CONTROLLER =================
  async function fetchDatasetInfo() {
    try {
      const res = await fetch("/api/dataset-info");
      const data = await res.json();
      currentDatasetStats = data;

      // Header Bar
      activeDatasetName.textContent = data.filename;
      activeDatasetCount.textContent = `${data.total_scholarships} scholarships`;

      // Modal Stats
      modalDatasetFilename.textContent = data.filename;
      modalDatasetCount.textContent = data.total_scholarships;
      modalDatasetCountries.textContent = data.countries_count;

      const fullCount = data.coverage_counts["full"] || 0;
      const partCount = data.coverage_counts["partial"] || 0;
      modalDatasetFunding.textContent = `${fullCount} Full / ${partCount} Partial`;

      // Populate Destination Countries
      populateCountryFilter(data.countries || []);
    } catch (err) {
      console.error("Error loading dataset metadata:", err);
      showToast("Unable to load dataset metadata", "error");
    }
  }

  function populateCountryFilter(countries) {
    const currentVal = countryFilter.value;
    countryFilter.innerHTML = `<option value="">Any Country (All Destinations)</option>`;
    countries.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      countryFilter.appendChild(opt);
    });
    countryFilter.value = currentVal;
  }

  // Dataset Modal Toggle
  openDatasetModalBtn.addEventListener("click", () => {
    uploadFeedback.textContent = "";
    datasetModal.classList.add("active");
  });

  closeDatasetModalBtn.addEventListener("click", () => {
    datasetModal.classList.remove("active");
  });

  datasetModal.addEventListener("click", (e) => {
    if (e.target === datasetModal) datasetModal.classList.remove("active");
  });

  // CSV Drag and Drop Upload
  csvDropZone.addEventListener("click", () => csvFileInput.click());

  csvDropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    csvDropZone.classList.add("dragover");
  });

  csvDropZone.addEventListener("dragleave", () => {
    csvDropZone.classList.remove("dragover");
  });

  csvDropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    csvDropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      uploadCustomCsv(e.dataTransfer.files[0]);
    }
  });

  csvFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      uploadCustomCsv(e.target.files[0]);
    }
  });

  async function uploadCustomCsv(file) {
    if (!file.name.toLowerCase().endsWith(".csv")) {
      showToast("Please upload a CSV file (.csv)", "error");
      return;
    }

    uploadFeedback.className = "upload-feedback";
    uploadFeedback.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Parsing and validating ${escapeHtml(file.name)}...`;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload-dataset", {
        method: "POST",
        body: formData
      });
      const data = await res.json();

      if (data.error) {
        uploadFeedback.className = "upload-feedback error";
        uploadFeedback.textContent = data.error;
        showToast(data.error, "error");
      } else {
        uploadFeedback.className = "upload-feedback success";
        uploadFeedback.innerHTML = `<i class="fa-solid fa-check"></i> ${data.message}`;
        showToast("Dataset updated successfully", "success");
        await fetchDatasetInfo();
        triggerSearch();
      }
    } catch (err) {
      uploadFeedback.className = "upload-feedback error";
      uploadFeedback.textContent = "Upload failed. Please check file format.";
      showToast("Failed to upload dataset", "error");
    }
  }

  revertDefaultDatasetBtn.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/reset-dataset", { method: "POST" });
      const data = await res.json();
      if (data.error) {
        showToast(data.error, "error");
      } else {
        showToast("Reverted to standard European scholarships dataset", "success");
        uploadFeedback.textContent = "";
        await fetchDatasetInfo();
        triggerSearch();
      }
    } catch (err) {
      showToast("Failed to reset dataset", "error");
    }
  });

  // ================= 3. SCHOLARSHIP SEARCH & MATCHING =================
  filterForm.addEventListener("submit", (e) => {
    e.preventDefault();
    triggerSearch();
  });

  mainSearchBtn.addEventListener("click", () => {
    triggerSearch();
  });

  keywordSearchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      triggerSearch();
    }
  });

  clearAllFiltersBtn.addEventListener("click", () => {
    filterForm.reset();
    keywordSearchInput.value = "";
    document.querySelector('input[name="degree"][value="master"]').checked = true;
    setBudgetValue(5000);
    updateCgpaNote();
    triggerSearch();
  });

  emptyResetBtn.addEventListener("click", () => {
    clearAllFiltersBtn.click();
  });

  async function triggerSearch() {
    resultsCountHeader.textContent = "Searching opportunities...";
    resultsGrid.innerHTML = "";
    resultsTableBody.innerHTML = "";
    overBudgetGrid.innerHTML = "";
    overBudgetContainer.style.display = "none";
    emptyResultsState.style.display = "none";

    const degree = document.querySelector('input[name="degree"]:checked').value;
    const cgpa = parseFloat(cgpaInput.value) || 3.0;
    const cgpaScaleVal = parseFloat(cgpaScale.value) || 4.0;
    const budgetUsd = parseFloat(budgetInput.value) || 5000;
    const nationality = nationalityInput.value.trim();
    const country = countryFilter.value;
    const coverage = coverageFilter.value;
    const keyword = keywordSearchInput.value.trim();

    updateActiveFilterTags({ degree, cgpa, cgpaScaleVal, budgetUsd, nationality, country, keyword });

    try {
      const res = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          degree,
          cgpa,
          cgpa_scale: cgpaScaleVal,
          budget_usd: budgetUsd,
          nationality,
          country,
          coverage,
          keyword
        })
      });

      const data = await res.json();
      if (data.error) {
        showToast(data.error, "error");
        emptyResultsState.style.display = "block";
        resultsCountHeader.textContent = "0 scholarships found";
        return;
      }

      allMatchedResults = data.results || [];
      overBudgetResults = data.closest_but_over_budget || [];

      // Update Fit Tab Counts
      const counts = data.fit_counts || { target: 0, safer: 0, reach: 0 };
      countAll.textContent = allMatchedResults.length;
      countTarget.textContent = counts.target;
      countSafer.textContent = counts.safer;
      countReach.textContent = counts.reach;

      resultsCountHeader.textContent = `${allMatchedResults.length} Scholarship${allMatchedResults.length === 1 ? '' : 's'} Matched`;

      renderCurrentFilteredResults();
    } catch (err) {
      console.error("Search execution error:", err);
      showToast("Error searching scholarships", "error");
      emptyResultsState.style.display = "block";
    }
  }

  function updateActiveFilterTags(params) {
    activeFilterTags.innerHTML = "";
    const tags = [];
    if (params.degree) tags.push(`Degree: ${params.degree.toUpperCase()}`);
    if (params.cgpa) tags.push(`GPA: ${params.cgpa}`);
    tags.push(`Budget ≤ $${params.budgetUsd.toLocaleString()}`);
    if (params.country) tags.push(`Country: ${params.country}`);
    if (params.nationality) tags.push(`Citizen: ${params.nationality}`);
    if (params.keyword) tags.push(`"${params.keyword}"`);

    tags.forEach(t => {
      const span = document.createElement("span");
      span.className = "filter-tag";
      span.textContent = t;
      activeFilterTags.appendChild(span);
    });
  }

  // Fit Filter Tabs
  fitTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      fitTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentFitFilter = tab.dataset.fit;
      renderCurrentFilteredResults();
    });
  });

  function renderCurrentFilteredResults() {
    resultsGrid.innerHTML = "";
    resultsTableBody.innerHTML = "";

    let filtered = allMatchedResults;
    if (currentFitFilter !== "all") {
      filtered = allMatchedResults.filter(s => s.fit === currentFitFilter);
    }

    if (filtered.length === 0 && overBudgetResults.length === 0) {
      emptyResultsState.style.display = "block";
      resultsGrid.style.display = "none";
      resultsTableContainer.style.display = "none";
      return;
    }

    emptyResultsState.style.display = "none";

    if (activeViewMode === "grid") {
      resultsGrid.style.display = "grid";
      resultsTableContainer.style.display = "none";
      filtered.forEach(s => resultsGrid.appendChild(createCard(s)));
    } else {
      resultsGrid.style.display = "none";
      resultsTableContainer.style.display = "block";
      filtered.forEach(s => resultsTableBody.appendChild(createTableRow(s)));
    }

    // Over-budget section
    if (overBudgetResults.length > 0) {
      overBudgetContainer.style.display = "block";
      overBudgetGrid.innerHTML = "";
      overBudgetResults.forEach(s => overBudgetGrid.appendChild(createCard(s, true)));
    } else {
      overBudgetContainer.style.display = "none";
    }
  }

  // View Mode Toggles
  viewGridBtn.addEventListener("click", () => {
    activeViewMode = "grid";
    viewGridBtn.classList.add("active");
    viewTableBtn.classList.remove("active");
    renderCurrentFilteredResults();
  });

  viewTableBtn.addEventListener("click", () => {
    activeViewMode = "table";
    viewTableBtn.classList.add("active");
    viewGridBtn.classList.remove("active");
    renderCurrentFilteredResults();
  });

  // Card Generator
  function createCard(s, isOverBudget = false) {
    const card = document.createElement("div");
    card.className = "scholarship-card";

    const outOfPocket = s.out_of_pocket_usd_per_year;
    const isFree = outOfPocket === 0;
    const oopDisplay = isFree ? "FREE (100% Covered)" : `$${outOfPocket.toLocaleString()} / year`;

    const fitClass = `badge-fit-${s.fit}`;
    const fitLabel = s.fit.charAt(0).toUpperCase() + s.fit.slice(1);

    const coverageBadge = s.coverage_level === "full"
      ? `<span class="badge-coverage-full">Fully Funded</span>`
      : `<span class="badge-coverage-partial">Partial Funding</span>`;

    let alertHtml = "";
    if (s.warnings && s.warnings.length > 0) {
      alertHtml = `
        <div class="card-alert">
          <i class="fa-solid fa-triangle-exclamation"></i>
          <div>${s.warnings.join("<br>")}</div>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="card-header-row">
        <div class="card-pills">
          <span class="badge-country"><i class="fa-solid fa-location-dot"></i> ${escapeHtml(s.country || 'International')}</span>
          ${coverageBadge}
        </div>
        <span class="badge-fit ${fitClass}">${fitLabel}</span>
      </div>

      <h3 class="card-title">${escapeHtml(s.name)}</h3>
      <div class="card-funder"><i class="fa-solid fa-building-columns"></i> ${escapeHtml(s.funder || s.country)}</div>

      <div class="card-financials">
        <div class="financial-metric">
          <span class="metric-label">Estimated Out-of-Pocket:</span>
          <span class="metric-amount ${isFree ? 'amount-free' : ''}">${oopDisplay}</span>
        </div>
        <p class="financial-desc">${escapeHtml(s.coverage_summary || 'Tuition waiver and stipend support')}</p>
      </div>

      <ul class="card-criteria">
        <li>
          <i class="fa-solid fa-award"></i>
          <span><strong>Academics:</strong> ${escapeHtml(s.academic_note || 'Strong academic record')}</span>
        </li>
        <li>
          <i class="fa-solid fa-calendar"></i>
          <span><strong>Deadline:</strong> ${escapeHtml(s.deadline || 'Check official site')}</span>
        </li>
        ${s.english_requirement ? `
        <li>
          <i class="fa-solid fa-language"></i>
          <span><strong>Language:</strong> ${escapeHtml(s.english_requirement)}</span>
        </li>` : ''}
      </ul>

      ${alertHtml}

      <div class="card-actions">
        <button class="btn btn-secondary btn-sm card-details-btn">Details</button>
        <a href="${s.official_website || '#'}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm">
          Website <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.75rem;"></i>
        </a>
      </div>
    `;

    card.querySelector(".card-details-btn").addEventListener("click", () => {
      openDetailModal(s);
    });

    return card;
  }

  // Table Row Generator
  function createTableRow(s) {
    const tr = document.createElement("tr");
    const outOfPocket = s.out_of_pocket_usd_per_year;
    const oopText = outOfPocket === 0 ? "FREE" : `$${outOfPocket.toLocaleString()}/yr`;
    const fitClass = `badge-fit-${s.fit}`;

    tr.innerHTML = `
      <td><strong>${escapeHtml(s.name)}</strong></td>
      <td>${escapeHtml(s.country)}</td>
      <td>${escapeHtml(s.degree_levels || 'All')}</td>
      <td><span class="badge-coverage-${s.coverage_level || 'partial'}">${(s.coverage_level || 'N/A').toUpperCase()}</span></td>
      <td><strong>${oopText}</strong></td>
      <td><span class="badge-fit ${fitClass}">${s.fit.toUpperCase()}</span></td>
      <td>${escapeHtml(s.deadline || '-')}</td>
      <td>
        <button class="btn btn-secondary btn-sm row-details-btn">View</button>
      </td>
    `;

    tr.querySelector(".row-details-btn").addEventListener("click", () => {
      openDetailModal(s);
    });

    return tr;
  }

  // ================= 4. SCHOLARSHIP DETAIL MODAL =================
  function openDetailModal(s) {
    detailCountryTag.textContent = s.country || "International";
    detailTitle.textContent = s.name;
    detailFunder.textContent = s.funder || s.country;
    detailOfficialLink.href = s.official_website || "#";

    detailBody.innerHTML = `
      <div class="detail-item">
        <label>Coverage Details</label>
        <div class="detail-item-value">${escapeHtml(s.coverage_summary || 'Tuition and living allowance')}</div>
      </div>

      <div class="detail-item" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; background: var(--slate-50); padding: 0.75rem; border-radius: var(--radius-sm); border: 1px solid var(--slate-200);">
        <div>
          <label>Estimated Total Cost</label>
          <div style="font-weight: 600;">${s.est_annual_cost_usd ? '$' + s.est_annual_cost_usd.toLocaleString() : 'N/A'}</div>
        </div>
        <div>
          <label>Annual Support</label>
          <div style="font-weight: 600;">${s.est_annual_support_usd ? '$' + s.est_annual_support_usd.toLocaleString() : 'N/A'}</div>
        </div>
        <div>
          <label>Out of Pocket</label>
          <div style="font-weight: 700; color: ${s.out_of_pocket_usd_per_year === 0 ? 'var(--success)' : 'var(--navy-900)'}">
            ${s.out_of_pocket_usd_per_year === 0 ? 'FREE' : '$' + s.out_of_pocket_usd_per_year.toLocaleString()}
          </div>
        </div>
      </div>

      <div class="detail-item">
        <label>Academic & Eligibility Criteria</label>
        <div class="detail-item-value">${escapeHtml(s.academic_note || 'Merit-based admission')}</div>
        ${s.suggested_competitive_cgpa_4 ? `<div style="font-size: 0.8rem; color: var(--slate-500); margin-top: 0.25rem;">Suggested competitive CGPA: ~${s.suggested_competitive_cgpa_4} / 4.0</div>` : ''}
      </div>

      ${s.english_requirement ? `
      <div class="detail-item">
        <label>Language Requirement</label>
        <div class="detail-item-value">${escapeHtml(s.english_requirement)}</div>
      </div>` : ''}

      ${s.work_experience ? `
      <div class="detail-item">
        <label>Work Experience</label>
        <div class="detail-item-value">${escapeHtml(s.work_experience)}</div>
      </div>` : ''}

      <div class="detail-item">
        <label>Eligible Nationalities</label>
        <div class="detail-item-value">${escapeHtml(s.eligible_nationalities || 'Open to all nationalities or see official website')}</div>
      </div>

      <div class="detail-item">
        <label>Application Deadline</label>
        <div class="detail-item-value">${escapeHtml(s.deadline || 'Check official website')}</div>
      </div>
    `;

    detailModal.classList.add("active");
  }

  function closeDetailModal() {
    detailModal.classList.remove("active");
  }

  closeDetailModalBtn.addEventListener("click", closeDetailModal);
  closeDetailFooterBtn.addEventListener("click", closeDetailModal);
  detailModal.addEventListener("click", (e) => {
    if (e.target === detailModal) closeDetailModal();
  });

  // ================= 5. ADVISOR DRAWER =================
  toggleAdvisorDrawerBtn.addEventListener("click", () => {
    advisorDrawer.classList.toggle("active");
    advisorDrawerOverlay.classList.toggle("active");
  });

  closeAdvisorDrawerBtn.addEventListener("click", closeAdvisorDrawer);
  advisorDrawerOverlay.addEventListener("click", closeAdvisorDrawer);

  function closeAdvisorDrawer() {
    advisorDrawer.classList.remove("active");
    advisorDrawerOverlay.classList.remove("active");
  }

  promptChips.forEach(chip => {
    chip.addEventListener("click", () => {
      sendAdvisorMessage(chip.dataset.query);
    });
  });

  advisorForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = advisorInput.value.trim();
    if (!query) return;
    sendAdvisorMessage(query);
  });

  async function sendAdvisorMessage(text) {
    appendAdvisorMessage(text, "user");
    advisorInput.value = "";

    const loadingId = appendAdvisorLoading();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          session_id: chatSessionId
        })
      });
      const data = await res.json();
      removeAdvisorLoading(loadingId);

      if (data.error) {
        appendAdvisorMessage(`Error: ${data.error}`, "system");
      } else {
        appendAdvisorMessage(data.reply, "system");
      }
    } catch (err) {
      removeAdvisorLoading(loadingId);
      appendAdvisorMessage("Sorry, unable to process query. Please try again.", "system");
    }
  }

  function appendAdvisorMessage(text, sender) {
    const div = document.createElement("div");
    div.className = `chat-msg ${sender}-msg`;
    div.innerHTML = `<div class="msg-bubble">${formatSimpleMarkdown(text)}</div>`;
    advisorMessages.appendChild(div);
    advisorMessages.scrollTop = advisorMessages.scrollHeight;
  }

  function appendAdvisorLoading() {
    const id = "load-" + Date.now();
    const div = document.createElement("div");
    div.id = id;
    div.className = "chat-msg system-msg";
    div.innerHTML = `<div class="msg-bubble"><i class="fa-solid fa-spinner fa-spin"></i> Consulting scholarship records...</div>`;
    advisorMessages.appendChild(div);
    advisorMessages.scrollTop = advisorMessages.scrollHeight;
    return id;
  }

  function removeAdvisorLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function formatSimpleMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color: var(--primary); text-decoration: underline;">$1</a>');
    html = html.replace(/^\- (.*$)/gim, '<li style="margin-left: 1rem; margin-bottom: 0.2rem;">$1</li>');
    html = html.replace(/\n\n/g, '<br><br>');
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  // ================= 6. UTILITIES =================
  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = "toast-item";
    const icon = type === "success" ? "fa-circle-check" : "fa-circle-info";
    toast.innerHTML = `<i class="fa-solid ${icon}"></i><span>${escapeHtml(message)}</span>`;
    toastArea.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      setTimeout(() => toast.remove(), 200);
    }, 3500);
  }

  function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // ESC closes modals and drawers
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      datasetModal.classList.remove("active");
      closeDetailModal();
      closeAdvisorDrawer();
    }
  });

  // ================= 7. INITIAL BOOTSTRAP =================
  fetchDatasetInfo();
  triggerSearch();
});
