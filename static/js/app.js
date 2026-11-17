/**
 * Scholarship Finder for Government College of Engineering, Kolhapur (GCOEK)
 * Client-Side Controller & Multi-Page Manager
 */

document.addEventListener("DOMContentLoaded", () => {
  // Session identifier for counseling chat
  let chatSessionId = "gcoek-" + Math.random().toString(36).substring(2, 9);

  // =========================================================================
  // UTILITY HELPERS
  // =========================================================================
  function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function showToast(message, type = "info") {
    let toastArea = document.getElementById("toastArea");
    if (!toastArea) {
      toastArea = document.createElement("div");
      toastArea.id = "toastArea";
      toastArea.className = "toast-area";
      document.body.appendChild(toastArea);
    }
    const toast = document.createElement("div");
    toast.className = "toast-item";
    const icon = type === "success" ? "fa-circle-check" : "fa-circle-info";
    toast.innerHTML = `<i class="fa-solid ${icon}"></i><span>${escapeHtml(message)}</span>`;
    toastArea.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      setTimeout(() => toast.remove(), 250);
    }, 3500);
  }

  function formatSimpleMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color: var(--primary); text-decoration: underline;">$1</a>');
    html = html.replace(/^\- (.*$)/gim, '<li style="margin-left: 1.25rem; margin-bottom: 0.25rem;">$1</li>');
    html = html.replace(/\n\n/g, '<br><br>');
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  // =========================================================================
  // MOBILE NAVIGATION DRAWER TOGGLE
  // =========================================================================
  const mobileMenuBtn = document.getElementById("mobileMenuBtn");
  const mainNavLinks = document.getElementById("mainNavLinks");

  if (mobileMenuBtn && mainNavLinks) {
    mobileMenuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = mainNavLinks.classList.toggle("open");
      mobileMenuBtn.setAttribute("aria-expanded", isOpen);
      const icon = mobileMenuBtn.querySelector("i");
      if (icon) {
        if (isOpen) {
          icon.classList.remove("fa-bars");
          icon.classList.add("fa-xmark");
        } else {
          icon.classList.remove("fa-xmark");
          icon.classList.add("fa-bars");
        }
      }
    });

    // Close when clicking outside
    document.addEventListener("click", (e) => {
      if (mainNavLinks.classList.contains("open") && !mainNavLinks.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
        mainNavLinks.classList.remove("open");
        mobileMenuBtn.setAttribute("aria-expanded", "false");
        const icon = mobileMenuBtn.querySelector("i");
        if (icon) {
          icon.classList.remove("fa-xmark");
          icon.classList.add("fa-bars");
        }
      }
    });

    // Close when clicking any nav item
    mainNavLinks.querySelectorAll(".nav-item").forEach(link => {
      link.addEventListener("click", () => {
        mainNavLinks.classList.remove("open");
        mobileMenuBtn.setAttribute("aria-expanded", "false");
        const icon = mobileMenuBtn.querySelector("i");
        if (icon) {
          icon.classList.remove("fa-xmark");
          icon.classList.add("fa-bars");
        }
      });
    });
  }

  // =========================================================================
  // PAGE 1: DIRECTORY & PROFILE MATCHER (/)
  // =========================================================================
  const filterForm = document.getElementById("filterForm");
  if (filterForm) {
    let allMatchedResults = [];
    let overBudgetResults = [];
    let currentFitFilter = "all";
    let activeViewMode = "grid";

    // Form inputs
    const keywordSearchInput = document.getElementById("keywordSearchInput");
    const mainSearchBtn = document.getElementById("mainSearchBtn");
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

    // Display elements
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

    // Budget slider and input sync
    function setBudgetValue(val) {
      const num = Math.max(0, parseInt(val) || 0);
      if (budgetRange) budgetRange.value = num;
      if (budgetInput) budgetInput.value = num;
      if (budgetLabel) budgetLabel.textContent = `$${num.toLocaleString()} / yr`;
    }

    if (budgetRange) {
      budgetRange.addEventListener("input", (e) => setBudgetValue(e.target.value));
    }
    if (budgetInput) {
      budgetInput.addEventListener("input", (e) => setBudgetValue(e.target.value));
    }

    quickPills.forEach(pill => {
      pill.addEventListener("click", () => {
        setBudgetValue(pill.dataset.budget);
        triggerSearch();
      });
    });

    // CGPA Conversion Text
    function updateCgpaNote() {
      if (!cgpaInput || !cgpaScale || !cgpaConversionText) return;
      const val = parseFloat(cgpaInput.value) || 0;
      const scale = parseFloat(cgpaScale.value) || 10.0;
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
      cgpaConversionText.textContent = `Approximate US Scale: ${converted.toFixed(2)} / 4.0 (GCOEK: ${val} / ${scale})`;
    }

    if (cgpaInput) cgpaInput.addEventListener("input", updateCgpaNote);
    if (cgpaScale) cgpaScale.addEventListener("change", updateCgpaNote);

    // Parse URL query parameters (e.g., from /countries or footer links)
    function applyUrlParams() {
      const urlParams = new URLSearchParams(window.location.search);
      const q = urlParams.get("q");
      const c = urlParams.get("country");
      const d = urlParams.get("degree");

      if (q && keywordSearchInput) keywordSearchInput.value = q;
      if (c && countryFilter) {
        countryFilter.value = c;
      }
      if (d) {
        const rad = document.querySelector(`input[name="degree"][value="${d}"]`);
        if (rad) rad.checked = true;
      }
    }

    // Trigger Search
    async function triggerSearch() {
      if (!resultsCountHeader) return;
      resultsCountHeader.textContent = "Matching GCOEK student profile...";
      if (resultsGrid) resultsGrid.innerHTML = "";
      if (resultsTableBody) resultsTableBody.innerHTML = "";
      if (overBudgetGrid) overBudgetGrid.innerHTML = "";
      if (overBudgetContainer) overBudgetContainer.style.display = "none";
      if (emptyResultsState) emptyResultsState.style.display = "none";

      const degreeEl = document.querySelector('input[name="degree"]:checked');
      const degree = degreeEl ? degreeEl.value : "master";
      const cgpa = cgpaInput ? (parseFloat(cgpaInput.value) || 8.0) : 8.0;
      const cgpaScaleVal = cgpaScale ? (parseFloat(cgpaScale.value) || 10.0) : 10.0;
      const budgetUsd = budgetInput ? (parseFloat(budgetInput.value) || 5000) : 5000;
      const nationality = nationalityInput ? nationalityInput.value.trim() : "India";
      const country = countryFilter ? countryFilter.value : "";
      const coverage = coverageFilter ? coverageFilter.value : "all";
      const keyword = keywordSearchInput ? keywordSearchInput.value.trim() : "";

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
          if (emptyResultsState) emptyResultsState.style.display = "block";
          resultsCountHeader.textContent = "0 scholarships found";
          return;
        }

        allMatchedResults = data.results || [];
        overBudgetResults = data.closest_but_over_budget || [];

        // Update Fit Tab Counts
        const counts = data.fit_counts || { target: 0, safer: 0, reach: 0 };
        if (countAll) countAll.textContent = allMatchedResults.length;
        if (countTarget) countTarget.textContent = counts.target;
        if (countSafer) countSafer.textContent = counts.safer;
        if (countReach) countReach.textContent = counts.reach;

        resultsCountHeader.textContent = `${allMatchedResults.length} Verified Scholarship${allMatchedResults.length === 1 ? '' : 's'} Matched`;

        renderCurrentFilteredResults();
      } catch (err) {
        console.error("Search error:", err);
        showToast("Error searching scholarships", "error");
        if (emptyResultsState) emptyResultsState.style.display = "block";
      }
    }

    function updateActiveFilterTags(params) {
      if (!activeFilterTags) return;
      activeFilterTags.innerHTML = "";
      const tags = [];
      if (params.degree) tags.push(`Degree: ${params.degree.toUpperCase()}`);
      if (params.cgpa) tags.push(`GCOEK CGPA: ${params.cgpa}`);
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

    // Fit Tabs
    fitTabs.forEach(tab => {
      tab.addEventListener("click", () => {
        fitTabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        currentFitFilter = tab.dataset.fit;
        renderCurrentFilteredResults();
      });
    });

    function renderCurrentFilteredResults() {
      if (!resultsGrid || !resultsTableBody) return;
      resultsGrid.innerHTML = "";
      resultsTableBody.innerHTML = "";

      let filtered = allMatchedResults;
      if (currentFitFilter !== "all") {
        filtered = allMatchedResults.filter(s => s.fit === currentFitFilter);
      }

      const hasResults = filtered && filtered.length > 0;

      if (hasResults) {
        if (emptyResultsState) emptyResultsState.style.display = "none";
        if (activeViewMode === "grid") {
          resultsGrid.style.display = "grid";
          if (resultsTableContainer) resultsTableContainer.style.display = "none";
          filtered.forEach(s => resultsGrid.appendChild(createCard(s)));
        } else {
          resultsGrid.style.display = "none";
          if (resultsTableContainer) resultsTableContainer.style.display = "block";
          filtered.forEach(s => resultsTableBody.appendChild(createTableRow(s)));
        }
      } else {
        if (resultsGrid) resultsGrid.style.display = "none";
        if (resultsTableContainer) resultsTableContainer.style.display = "none";
        if (emptyResultsState) emptyResultsState.style.display = "block";
      }

      // Over-budget section
      if (overBudgetResults.length > 0 && overBudgetContainer && overBudgetGrid) {
        overBudgetContainer.style.display = "block";
        overBudgetGrid.innerHTML = "";
        overBudgetResults.forEach(s => overBudgetGrid.appendChild(createCard(s, true)));
      } else if (overBudgetContainer) {
        overBudgetContainer.style.display = "none";
      }
    }

    // View Mode Toggles
    if (viewGridBtn && viewTableBtn) {
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
    }

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
            <i class="fa-solid fa-graduation-cap"></i>
            <span>${escapeHtml(s.gpa_requirement || 'Published minimum: Not specified — verify how your institution converts CGPA to percentage.')}</span>
          </li>
          <li>
            <i class="fa-solid fa-calendar"></i>
            <span><strong>Deadline:</strong> ${escapeHtml(s.deadline && s.deadline !== '0.0' && s.deadline !== '0' ? s.deadline : 'Not specified — verify on official site')}</span>
          </li>
          ${s.english_requirement ? `
          <li>
            <i class="fa-solid fa-language"></i>
            <span><strong>Language:</strong> ${escapeHtml(s.english_requirement)}</span>
          </li>` : ''}
        </ul>

        ${alertHtml}

        <div class="card-actions">
          <a href="/scholarship/${encodeURIComponent(s.name)}" class="btn btn-secondary btn-sm">Full Profile</a>
          <button type="button" class="btn btn-secondary btn-sm card-quick-view-btn">Quick View</button>
          <a href="${s.official_website || '#'}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm">
            Website <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.75rem;"></i>
          </a>
        </div>
      `;

      card.querySelector(".card-quick-view-btn").addEventListener("click", () => {
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
        <td>
          <a href="/scholarship/${encodeURIComponent(s.name)}" style="color: var(--navy-900); font-weight: 600;">
            ${escapeHtml(s.name)}
          </a>
        </td>
        <td>${escapeHtml(s.country)}</td>
        <td>${escapeHtml(s.degree_levels || 'All')}</td>
        <td><span class="badge-coverage-${s.coverage_level || 'partial'}">${(s.coverage_level || 'N/A').toUpperCase()}</span></td>
        <td><strong>${oopText}</strong></td>
        <td><span class="badge-fit ${fitClass}">${s.fit.toUpperCase()}</span></td>
        <td>${escapeHtml(s.deadline && s.deadline !== '0.0' && s.deadline !== '0' ? s.deadline : 'Not specified — verify on official site')}</td>
        <td>
          <div style="display: flex; gap: 0.4rem;">
            <a href="/scholarship/${encodeURIComponent(s.name)}" class="btn btn-secondary btn-sm" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;">Profile</a>
            <button class="btn btn-secondary btn-sm row-details-btn" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;">Modal</button>
          </div>
        </td>
      `;

      tr.querySelector(".row-details-btn").addEventListener("click", () => {
        openDetailModal(s);
      });

      return tr;
    }

    // Quick View Modal
    function openDetailModal(s) {
      if (!detailModal) return;
      if (detailCountryTag) detailCountryTag.textContent = s.country || "International";
      if (detailTitle) detailTitle.textContent = s.name;
      if (detailFunder) detailFunder.textContent = s.funder || s.country;
      if (detailOfficialLink) detailOfficialLink.href = s.official_website || "#";

      if (detailBody) {
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
            ${s.suggested_competitive_cgpa_4 ? `<div style="font-size: 0.8rem; color: var(--slate-500); margin-top: 0.25rem;">Suggested competitive CGPA: ~${s.suggested_competitive_cgpa_4} / 4.0 (Approx. ${(s.suggested_competitive_cgpa_4 / 4.0 * 10).toFixed(1)} / 10.0 GCOEK)</div>` : ''}
          </div>

          ${s.english_requirement ? `
          <div class="detail-item">
            <label>Language Requirement</label>
            <div class="detail-item-value">${escapeHtml(s.english_requirement)}</div>
          </div>` : ''}

          <div class="detail-item">
            <label>Eligible Nationalities</label>
            <div class="detail-item-value">${escapeHtml(s.eligible_nationalities || 'Open to Indian and international students')}</div>
          </div>

          <div class="detail-item">
            <label>Application Deadline</label>
            <div class="detail-item-value">${escapeHtml(s.deadline && s.deadline !== '0.0' && s.deadline !== '0' ? s.deadline : 'Not specified — verify on official site')}</div>
          </div>
        `;
      }

      detailModal.classList.add("active");
    }

    function closeDetailModal() {
      if (detailModal) detailModal.classList.remove("active");
    }

    if (closeDetailModalBtn) closeDetailModalBtn.addEventListener("click", closeDetailModal);
    if (closeDetailFooterBtn) closeDetailFooterBtn.addEventListener("click", closeDetailModal);
    if (detailModal) {
      detailModal.addEventListener("click", (e) => {
        if (e.target === detailModal) closeDetailModal();
      });
    }

    // Form Event Listeners
    filterForm.addEventListener("submit", (e) => {
      e.preventDefault();
      triggerSearch();
    });

    if (mainSearchBtn) mainSearchBtn.addEventListener("click", triggerSearch);
    if (keywordSearchInput) {
      keywordSearchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") triggerSearch();
      });
    }

    if (clearAllFiltersBtn) {
      clearAllFiltersBtn.addEventListener("click", () => {
        filterForm.reset();
        if (keywordSearchInput) keywordSearchInput.value = "";
        const masterRadio = document.querySelector('input[name="degree"][value="master"]');
        if (masterRadio) masterRadio.checked = true;
        setBudgetValue(5000);
        updateCgpaNote();
        triggerSearch();
      });
    }

    if (emptyResetBtn) {
      emptyResetBtn.addEventListener("click", () => {
        if (clearAllFiltersBtn) clearAllFiltersBtn.click();
      });
    }

    // Initialize search on Directory page
    updateCgpaNote();
    applyUrlParams();
    triggerSearch();
  }

  // =========================================================================
  // PAGE 2: DATASET CONTROLLER (/dataset)
  // =========================================================================
  const datasetFullTableBody = document.getElementById("datasetFullTableBody");
  if (datasetFullTableBody) {
    const datasetTableSearch = document.getElementById("datasetTableSearch");
    const csvDropZone = document.getElementById("csvDropZone");
    const csvFileInput = document.getElementById("csvFileInput");
    const uploadFeedback = document.getElementById("uploadFeedback");
    const revertDefaultDatasetBtn = document.getElementById("revertDefaultDatasetBtn");
    const activeDatasetNameDisplay = document.getElementById("activeDatasetNameDisplay");
    const totalScholarshipsDisplay = document.getElementById("totalScholarshipsDisplay");

    let loadedScholarships = [];

    async function loadDatasetTable() {
      datasetFullTableBody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 2rem;"><i class="fa-solid fa-spinner fa-spin"></i> Loading verified database records...</td></tr>`;

      try {
        const res = await fetch("/api/scholarships");
        const data = await res.json();
        loadedScholarships = data.scholarships || [];
        renderTableRows(loadedScholarships);

        if (totalScholarshipsDisplay) {
          totalScholarshipsDisplay.textContent = `${loadedScholarships.length} Programs`;
        }
      } catch (err) {
        console.error("Failed to load dataset records:", err);
        datasetFullTableBody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--danger); padding: 2rem;">Error loading dataset. Please refresh the page.</td></tr>`;
      }
    }

    function renderTableRows(records) {
      datasetFullTableBody.innerHTML = "";
      if (records.length === 0) {
        datasetFullTableBody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 2rem; color: var(--slate-500);">No matching scholarship records found.</td></tr>`;
        return;
      }

      records.forEach(s => {
        const tr = document.createElement("tr");
        const costStr = s.est_annual_cost_usd ? `$${s.est_annual_cost_usd.toLocaleString()}` : "N/A";
        const suppStr = s.est_annual_support_usd ? `$${s.est_annual_support_usd.toLocaleString()}` : "N/A";
        const oop = s.out_of_pocket_usd_per_year;
        const oopStr = oop === 0 ? "FREE" : (oop ? `$${oop.toLocaleString()}/yr` : "N/A");

        tr.innerHTML = `
          <td>
            <a href="/scholarship/${encodeURIComponent(s.name)}" style="font-weight: 600; color: var(--navy-900);">
              ${escapeHtml(s.name)}
            </a>
          </td>
          <td>${escapeHtml(s.country)}</td>
          <td>${escapeHtml(s.funder || s.country)}</td>
          <td>${escapeHtml(s.degree_levels || 'All')}</td>
          <td>
            <span class="badge-coverage-${s.coverage_level || 'partial'}">
              ${(s.coverage_level || 'PARTIAL').toUpperCase()}
            </span>
          </td>
          <td>${costStr}</td>
          <td>${suppStr}</td>
          <td><strong style="color: ${oop === 0 ? 'var(--success)' : 'inherit'}">${oopStr}</strong></td>
          <td>
            <a href="${s.official_website || '#'}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;">
              Portal <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.7rem;"></i>
            </a>
          </td>
        `;
        datasetFullTableBody.appendChild(tr);
      });
    }

    // Live search filter
    if (datasetTableSearch) {
      datasetTableSearch.addEventListener("input", (e) => {
        const q = e.target.value.toLowerCase().trim();
        if (!q) {
          renderTableRows(loadedScholarships);
          return;
        }
        const filtered = loadedScholarships.filter(s => {
          return (s.name && s.name.toLowerCase().includes(q)) ||
                 (s.country && s.country.toLowerCase().includes(q)) ||
                 (s.funder && s.funder.toLowerCase().includes(q)) ||
                 (s.degree_levels && s.degree_levels.toLowerCase().includes(q));
        });
        renderTableRows(filtered);
      });
    }

    // CSV Drag and drop upload
    if (csvDropZone && csvFileInput) {
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
    }

    async function uploadCustomCsv(file) {
      if (!file.name.toLowerCase().endsWith(".csv")) {
        showToast("Please provide a valid CSV file (.csv)", "error");
        return;
      }

      if (uploadFeedback) {
        uploadFeedback.className = "upload-feedback";
        uploadFeedback.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Parsing and normalizing ${escapeHtml(file.name)}...`;
      }

      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch("/api/upload-dataset", {
          method: "POST",
          body: formData
        });
        const data = await res.json();

        if (data.error) {
          if (uploadFeedback) {
            uploadFeedback.className = "upload-feedback error";
            uploadFeedback.textContent = data.error;
          }
          showToast(data.error, "error");
        } else {
          if (uploadFeedback) {
            uploadFeedback.className = "upload-feedback success";
            uploadFeedback.innerHTML = `<i class="fa-solid fa-check"></i> ${data.message}`;
          }
          if (activeDatasetNameDisplay) activeDatasetNameDisplay.textContent = file.name;
          showToast("Dataset updated successfully", "success");
          loadDatasetTable();
        }
      } catch (err) {
        if (uploadFeedback) {
          uploadFeedback.className = "upload-feedback error";
          uploadFeedback.textContent = "Upload failed. Please check the CSV format.";
        }
        showToast("Failed to upload dataset", "error");
      }
    }

    if (revertDefaultDatasetBtn) {
      revertDefaultDatasetBtn.addEventListener("click", async () => {
        try {
          const res = await fetch("/api/reset-dataset", { method: "POST" });
          const data = await res.json();
          if (data.error) {
            showToast(data.error, "error");
          } else {
            showToast("Reverted to standard verified dataset", "success");
            if (uploadFeedback) uploadFeedback.textContent = "";
            if (activeDatasetNameDisplay) activeDatasetNameDisplay.textContent = "europe_scholarships_matching.csv";
            loadDatasetTable();
          }
        } catch (err) {
          showToast("Failed to reset dataset", "error");
        }
      });
    }

    loadDatasetTable();
  }

  // =========================================================================
  // PAGE 3: ADVISOR DESK (/advisor)
  // =========================================================================
  const advisorFullChatForm = document.getElementById("advisorFullChatForm");
  if (advisorFullChatForm) {
    const advisorFullChatInput = document.getElementById("advisorFullChatInput");
    const advisorFullChatMessages = document.getElementById("advisorFullChatMessages");
    const resetAdvisorChatBtn = document.getElementById("resetAdvisorChatBtn");
    const quickPrompts = document.querySelectorAll(".advisor-quick-prompt");

    quickPrompts.forEach(btn => {
      btn.addEventListener("click", () => {
        const query = btn.dataset.text || btn.textContent.trim();
        if (advisorFullChatInput) advisorFullChatInput.value = query;
        sendAdvisorCounseling(query);
      });
    });

    advisorFullChatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const text = advisorFullChatInput.value.trim();
      if (!text) return;
      sendAdvisorCounseling(text);
    });

    if (resetAdvisorChatBtn) {
      resetAdvisorChatBtn.addEventListener("click", () => {
        chatSessionId = "gcoek-" + Math.random().toString(36).substring(2, 9);
        advisorFullChatMessages.innerHTML = `
          <div class="chat-msg system-msg">
            <div class="msg-bubble">
              <p><strong>Counseling session reset.</strong> 🎓</p>
              <p>Hello! I am ready to advise you on scholarships for students and alumni of <strong>Government College of Engineering, Kolhapur</strong>. Tell me your target branch, CGPA, or destination country.</p>
            </div>
          </div>
        `;
        showToast("Conversation cleared", "info");
      });
    }

    async function sendAdvisorCounseling(text) {
      appendChatMessage(text, "user");
      if (advisorFullChatInput) advisorFullChatInput.value = "";

      const loadingId = appendChatLoading();

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
        removeChatLoading(loadingId);

        if (data.error) {
          appendChatMessage(`⚠️ Advisory Notice: ${data.error}`, "system");
        } else {
          appendChatMessage(data.reply, "system");
        }
      } catch (err) {
        removeChatLoading(loadingId);
        appendChatMessage("Sorry, the counseling desk is temporarily unreachable. Please check your connection and try again.", "system");
      }
    }

    function appendChatMessage(text, sender) {
      const div = document.createElement("div");
      div.className = `chat-msg ${sender}-msg`;
      div.innerHTML = `<div class="msg-bubble">${formatSimpleMarkdown(text)}</div>`;
      advisorFullChatMessages.appendChild(div);
      advisorFullChatMessages.scrollTop = advisorFullChatMessages.scrollHeight;
    }

    function appendChatLoading() {
      const id = "load-" + Date.now();
      const div = document.createElement("div");
      div.id = id;
      div.className = "chat-msg system-msg";
      div.innerHTML = `<div class="msg-bubble"><i class="fa-solid fa-spinner fa-spin"></i> Consulting GCOEK scholarship database & AI advisor...</div>`;
      advisorFullChatMessages.appendChild(div);
      advisorFullChatMessages.scrollTop = advisorFullChatMessages.scrollHeight;
      return id;
    }

    function removeChatLoading(id) {
      const el = document.getElementById(id);
      if (el) el.remove();
    }
  }

  // =========================================================================
  // PAGE 4: INDIA CASTE & CATEGORY SCHEMES (/india)
  // =========================================================================
  const indiaFilterForm = document.getElementById("indiaFilterForm");
  if (indiaFilterForm) {
    let currentCategory = "All";
    let activeIndiaView = "grid";
    let allIndiaSchemes = [];

    const castePills = document.querySelectorAll(".caste-pill");
    const incomeRange = document.getElementById("incomeRange");
    const incomeInput = document.getElementById("incomeInput");
    const incomeBadge = document.getElementById("incomeBadge");
    const incomeQuickPills = document.querySelectorAll(".income-quick-pill");
    const authorityFilter = document.getElementById("authorityFilter");
    const degreeFilter = document.getElementById("degreeFilter");
    const indiaKeywordSearch = document.getElementById("indiaKeywordSearch");
    const indiaMainSearchBtn = document.getElementById("indiaMainSearchBtn");
    const resetIndiaFiltersBtn = document.getElementById("resetIndiaFiltersBtn");

    const indiaResultsCount = document.getElementById("indiaResultsCount");
    const indiaActiveTags = document.getElementById("indiaActiveTags");
    const indiaSchemesGrid = document.getElementById("indiaSchemesGrid");
    const indiaTableContainer = document.getElementById("indiaTableContainer");
    const indiaTableBody = document.getElementById("indiaTableBody");
    const indiaEmptyState = document.getElementById("indiaEmptyState");
    const indiaEmptyResetBtn = document.getElementById("indiaEmptyResetBtn");
    const indiaViewGridBtn = document.getElementById("indiaViewGridBtn");
    const indiaViewTableBtn = document.getElementById("indiaViewTableBtn");

    // Modal elements
    const indiaDocModal = document.getElementById("indiaDocModal");
    const closeIndiaDocModalBtn = document.getElementById("closeIndiaDocModalBtn");
    const closeIndiaDocFooterBtn = document.getElementById("closeIndiaDocFooterBtn");
    const modalSchemeAuth = document.getElementById("modalSchemeAuth");
    const modalSchemeTitle = document.getElementById("modalSchemeTitle");
    const modalSchemeDept = document.getElementById("modalSchemeDept");
    const modalSchemeCategory = document.getElementById("modalSchemeCategory");
    const modalSchemeBenefit = document.getElementById("modalSchemeBenefit");
    const modalSchemeDocsList = document.getElementById("modalSchemeDocsList");
    const modalSchemeLink = document.getElementById("modalSchemeLink");

    function setIncomeValue(val) {
      const num = Math.max(0, parseInt(val) || 0);
      if (incomeRange) incomeRange.value = num;
      if (incomeInput) incomeInput.value = num;
      if (incomeBadge) {
        incomeBadge.textContent = num === 0 ? "Any Income" : `₹${num.toLocaleString("en-IN")} / yr`;
      }
    }

    if (incomeRange) {
      incomeRange.addEventListener("input", (e) => setIncomeValue(e.target.value));
    }
    if (incomeInput) {
      incomeInput.addEventListener("input", (e) => setIncomeValue(e.target.value));
    }

    incomeQuickPills.forEach(pill => {
      pill.addEventListener("click", () => {
        setIncomeValue(pill.dataset.income);
        triggerIndiaSearch();
      });
    });

    castePills.forEach(pill => {
      pill.addEventListener("click", () => {
        castePills.forEach(p => p.classList.remove("active"));
        pill.classList.add("active");
        currentCategory = pill.dataset.category || "All";
        triggerIndiaSearch();
      });
    });

    async function triggerIndiaSearch() {
      if (indiaResultsCount) indiaResultsCount.textContent = "Filtering caste & government schemes...";
      if (indiaSchemesGrid) indiaSchemesGrid.innerHTML = "";
      if (indiaTableBody) indiaTableBody.innerHTML = "";
      if (indiaEmptyState) indiaEmptyState.style.display = "none";

      const incomeVal = incomeInput ? (parseFloat(incomeInput.value) || 0) : 0;
      const authorityVal = authorityFilter ? authorityFilter.value : "All";
      const degreeVal = degreeFilter ? degreeFilter.value : "All";
      const keywordVal = indiaKeywordSearch ? indiaKeywordSearch.value.trim() : "";

      updateIndiaTags({ currentCategory, incomeVal, authorityVal, degreeVal, keywordVal });

      try {
        const res = await fetch("/api/india/scholarships", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            category: currentCategory,
            max_income: incomeVal,
            authority: authorityVal,
            degree: degreeVal,
            keyword: keywordVal
          })
        });

        const data = await res.json();
        allIndiaSchemes = data.results || [];

        if (indiaResultsCount) {
          indiaResultsCount.textContent = `${allIndiaSchemes.length} Scheme${allIndiaSchemes.length === 1 ? '' : 's'} Available`;
        }

        renderIndiaResults();
      } catch (err) {
        console.error("India scheme search error:", err);
        showToast("Error filtering Indian schemes", "error");
        if (indiaEmptyState) indiaEmptyState.style.display = "block";
      }
    }

    function updateIndiaTags(params) {
      if (!indiaActiveTags) return;
      indiaActiveTags.innerHTML = "";
      const tags = [];
      if (params.currentCategory && params.currentCategory !== "All") {
        tags.push(`Category: ${params.currentCategory}`);
      }
      if (params.incomeVal > 0) {
        tags.push(`Income ≤ ₹${params.incomeVal.toLocaleString("en-IN")}`);
      }
      if (params.authorityVal && params.authorityVal !== "All") {
        tags.push(`Authority: ${params.authorityVal}`);
      }
      if (params.degreeVal && params.degreeVal !== "All") {
        tags.push(`Course: ${params.degreeVal}`);
      }
      if (params.keywordVal) {
        tags.push(`"${params.keywordVal}"`);
      }

      tags.forEach(t => {
        const span = document.createElement("span");
        span.className = "filter-tag";
        span.textContent = t;
        indiaActiveTags.appendChild(span);
      });
    }

    function renderIndiaResults() {
      if (!indiaSchemesGrid || !indiaTableBody) return;
      indiaSchemesGrid.innerHTML = "";
      indiaTableBody.innerHTML = "";

      if (allIndiaSchemes.length === 0) {
        if (indiaEmptyState) indiaEmptyState.style.display = "block";
        if (indiaSchemesGrid) indiaSchemesGrid.style.display = "none";
        if (indiaTableContainer) indiaTableContainer.style.display = "none";
        return;
      }

      if (indiaEmptyState) indiaEmptyState.style.display = "none";

      if (activeIndiaView === "grid") {
        indiaSchemesGrid.style.display = "grid";
        if (indiaTableContainer) indiaTableContainer.style.display = "none";
        allIndiaSchemes.forEach(s => indiaSchemesGrid.appendChild(createIndiaCard(s)));
      } else {
        indiaSchemesGrid.style.display = "none";
        if (indiaTableContainer) indiaTableContainer.style.display = "block";
        allIndiaSchemes.forEach(s => indiaTableBody.appendChild(createIndiaTableRow(s)));
      }
    }

    function createIndiaCard(s) {
      const card = document.createElement("div");
      card.className = "scholarship-card";

      const catClean = (s.caste_category || "All").toLowerCase().replace(/[\s\/]/g, "");
      const incomeStr = s.max_income_inr > 0 ? `Income ≤ ₹${s.max_income_inr.toLocaleString("en-IN")}` : "No Income Bar";

      card.innerHTML = `
        <div class="card-header-row">
          <div class="card-pills">
            <span class="badge-country"><i class="fa-solid fa-landmark"></i> ${escapeHtml(s.state_or_central)}</span>
            <span class="badge-caste badge-caste-${catClean}">${escapeHtml(s.caste_category)}</span>
          </div>
          <span class="badge-fit badge-fit-target">${incomeStr}</span>
        </div>

        <h3 class="card-title">${escapeHtml(s.scheme_name)}</h3>
        <div class="card-funder"><i class="fa-solid fa-building-columns"></i> ${escapeHtml(s.department)}</div>

        <div class="card-financials">
          <div class="financial-metric">
            <span class="metric-label">Financial Benefit:</span>
            <span class="metric-amount amount-free">${escapeHtml(s.benefit_summary)}</span>
          </div>
        </div>

        <ul class="card-criteria">
          <li>
            <i class="fa-solid fa-user-graduate"></i>
            <span><strong>Eligible:</strong> ${escapeHtml(s.eligibility_criteria)}</span>
          </li>
          <li>
            <i class="fa-solid fa-file-lines"></i>
            <span><strong>Documents:</strong> ${escapeHtml((s.required_documents || "").substring(0, 85))}...</span>
          </li>
        </ul>

        <div class="card-actions">
          <a href="/india/scheme/${s.id}" class="btn btn-secondary btn-sm">Full Dossier</a>
          <button type="button" class="btn btn-secondary btn-sm card-quick-docs-btn">Documents</button>
          <a href="${s.official_portal_url || '#'}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm">
            Portal <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.75rem;"></i>
          </a>
        </div>
      `;

      card.querySelector(".card-quick-docs-btn").addEventListener("click", () => {
        openIndiaDocModal(s);
      });

      return card;
    }

    function createIndiaTableRow(s) {
      const tr = document.createElement("tr");
      const catClean = (s.caste_category || "All").toLowerCase().replace(/[\s\/]/g, "");
      const incStr = s.max_income_inr > 0 ? `₹${s.max_income_inr.toLocaleString("en-IN")}` : "No Bar";

      tr.innerHTML = `
        <td>
          <a href="/india/scheme/${s.id}" style="font-weight: 600; color: var(--navy-900);">
            ${escapeHtml(s.scheme_name)}
          </a>
        </td>
        <td>
          <div>${escapeHtml(s.state_or_central)}</div>
          <small style="color: var(--slate-500);">${escapeHtml(s.department)}</small>
        </td>
        <td><span class="badge-caste badge-caste-${catClean}">${escapeHtml(s.caste_category)}</span></td>
        <td><strong>${incStr}</strong></td>
        <td>${escapeHtml(s.benefit_summary)}</td>
        <td>
          <div style="display: flex; gap: 0.35rem;">
            <a href="/india/scheme/${s.id}" class="btn btn-secondary btn-sm" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;">Dossier</a>
            <button class="btn btn-secondary btn-sm row-docs-btn" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;">Docs</button>
          </div>
        </td>
      `;

      tr.querySelector(".row-docs-btn").addEventListener("click", () => {
        openIndiaDocModal(s);
      });

      return tr;
    }

    function openIndiaDocModal(s) {
      if (!indiaDocModal) return;
      if (modalSchemeAuth) modalSchemeAuth.textContent = s.state_or_central;
      if (modalSchemeTitle) modalSchemeTitle.textContent = s.scheme_name;
      if (modalSchemeDept) modalSchemeDept.textContent = s.department;
      if (modalSchemeCategory) {
        const incText = s.max_income_inr > 0 ? `Income Limit: ≤ ₹${s.max_income_inr.toLocaleString("en-IN")} / yr` : "No Income Bar (Merit)";
        modalSchemeCategory.textContent = `Category: ${s.caste_category} • ${incText}`;
      }
      if (modalSchemeBenefit) modalSchemeBenefit.textContent = s.benefit_summary;
      if (modalSchemeLink) modalSchemeLink.href = s.official_portal_url || "#";

      if (modalSchemeDocsList) {
        modalSchemeDocsList.innerHTML = "";
        const rawDocs = s.required_documents || "";
        const docs = rawDocs.split(";").map(d => d.trim()).filter(Boolean);
        if (docs.length === 0) {
          modalSchemeDocsList.innerHTML = `<li>Standard MahaDBT verification documents required.</li>`;
        } else {
          docs.forEach(doc => {
            const li = document.createElement("li");
            li.innerHTML = `<i class="fa-solid fa-circle-check" style="color: var(--success); margin-right: 0.35rem;"></i> <strong>${escapeHtml(doc)}</strong>`;
            modalSchemeDocsList.appendChild(li);
          });
        }
      }

      indiaDocModal.classList.add("active");
    }

    function closeIndiaDocModal() {
      if (indiaDocModal) indiaDocModal.classList.remove("active");
    }

    if (closeIndiaDocModalBtn) closeIndiaDocModalBtn.addEventListener("click", closeIndiaDocModal);
    if (closeIndiaDocFooterBtn) closeIndiaDocFooterBtn.addEventListener("click", closeIndiaDocModal);
    if (indiaDocModal) {
      indiaDocModal.addEventListener("click", (e) => {
        if (e.target === indiaDocModal) closeIndiaDocModal();
      });
    }

    // View mode toggle
    if (indiaViewGridBtn && indiaViewTableBtn) {
      indiaViewGridBtn.addEventListener("click", () => {
        activeIndiaView = "grid";
        indiaViewGridBtn.classList.add("active");
        indiaViewTableBtn.classList.remove("active");
        renderIndiaResults();
      });

      indiaViewTableBtn.addEventListener("click", () => {
        activeIndiaView = "table";
        indiaViewTableBtn.classList.add("active");
        indiaViewGridBtn.classList.remove("active");
        renderIndiaResults();
      });
    }

    // Form submit
    indiaFilterForm.addEventListener("submit", (e) => {
      e.preventDefault();
      triggerIndiaSearch();
    });

    if (indiaMainSearchBtn) indiaMainSearchBtn.addEventListener("click", triggerIndiaSearch);
    if (indiaKeywordSearch) {
      indiaKeywordSearch.addEventListener("keydown", (e) => {
        if (e.key === "Enter") triggerIndiaSearch();
      });
    }

    if (resetIndiaFiltersBtn) {
      resetIndiaFiltersBtn.addEventListener("click", () => {
        indiaFilterForm.reset();
        castePills.forEach(p => p.classList.remove("active"));
        const allPill = document.querySelector('.caste-pill[data-category="All"]');
        if (allPill) allPill.classList.add("active");
        currentCategory = "All";
        setIncomeValue(0);
        if (authorityFilter) authorityFilter.value = "All";
        if (degreeFilter) degreeFilter.value = "All";
        if (indiaKeywordSearch) indiaKeywordSearch.value = "";
        triggerIndiaSearch();
      });
    }

    if (indiaEmptyResetBtn) {
      indiaEmptyResetBtn.addEventListener("click", () => {
        if (resetIndiaFiltersBtn) resetIndiaFiltersBtn.click();
      });
    }

    // Wire up initial quick docs buttons if pre-rendered
    document.querySelectorAll(".india-quick-docs-btn").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = parseInt(btn.dataset.id);
        if (allIndiaSchemes.length === 0) {
          const res = await fetch("/api/india/scholarships");
          const data = await res.json();
          allIndiaSchemes = data.results || [];
        }
        const s = allIndiaSchemes.find(item => item.id === id);
        if (s) openIndiaDocModal(s);
      });
    });

    // Initial search
    triggerIndiaSearch();
  }

  // =========================================================================
  // GLOBAL KEYBOARD SHORTCUTS
  // =========================================================================
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const detailModal = document.getElementById("detailModal");
      if (detailModal) detailModal.classList.remove("active");
      const indiaDocModal = document.getElementById("indiaDocModal");
      if (indiaDocModal) indiaDocModal.classList.remove("active");
    }
  });
});

