// -------- Data loaders --------

function renderLoadError(container, retryFn) {
  container.innerHTML = `
    <div class="load-error">
      <div class="load-error-message">
        <span class="load-error-icon">⚠</span>
        <span>Couldn't load. Check your connection or try again.</span>
      </div>
      <button class="load-error-retry">Retry</button>
    </div>
  `;
  container.querySelector(".load-error-retry").addEventListener("click", retryFn);
}

async function loadStats() {
  const statsBar = document.getElementById("stats-bar");
  statsBar.innerHTML = `
    <div class="skeleton-stat-card">
      <div class="skeleton skeleton-label"></div>
      <div class="skeleton skeleton-value"></div>
    </div>
    <div class="skeleton-stat-card">
      <div class="skeleton skeleton-label"></div>
      <div class="skeleton skeleton-value"></div>
    </div>
    <div class="skeleton-stat-card">
      <div class="skeleton skeleton-label"></div>
      <div class="skeleton skeleton-value"></div>
    </div>
  `;

  try {
    const [valueRes, spentRes] = await Promise.all([
      fetch("/stats/total-value"),
      fetch("/stats/total-spent")
    ]);
    if (!valueRes.ok || !spentRes.ok) throw new Error("Failed to fetch stats");
    const { total_value } = await valueRes.json();
    const { total_spent } = await spentRes.json();
    const gain = total_value - total_spent;
    const gainClass = gain >= 0 ? "positive" : "negative";
    const gainSign = gain >= 0 ? "+" : "";

    statsBar.innerHTML = `
      <div class="stat-card">
        <div class="stat-label">Total Value</div>
        <div class="stat-value positive">$${total_value !== null ? total_value.toFixed(2) : "—"}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Spent</div>
        <div class="stat-value">$${total_spent !== null ? total_spent.toFixed(2) : "—"}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Gain / Loss</div>
        <div class="stat-value ${gainClass}">${gainSign}$${gain.toFixed(2)}</div>
      </div>
    `;
  } catch (err) {
    renderLoadError(statsBar, loadStats);
  }
}

async function loadBySet() {
  const container = document.getElementById("by-set");
  container.innerHTML = `
    <div class="skeleton-row">
      <div class="skeleton skeleton-text-l"></div>
      <div class="skeleton skeleton-text-r"></div>
    </div>
    <div class="skeleton-row">
      <div class="skeleton skeleton-text-l"></div>
      <div class="skeleton skeleton-text-r"></div>
    </div>
    <div class="skeleton-row">
      <div class="skeleton skeleton-text-l"></div>
      <div class="skeleton skeleton-text-r"></div>
    </div>
    <div class="skeleton-row">
      <div class="skeleton skeleton-text-l"></div>
      <div class="skeleton skeleton-text-r"></div>
    </div>
  `;
  try {
  const response = await fetch("/stats/by-set");
  if (!response.ok) throw new Error("Failed to fetch");
  const sets = await response.json();
  container.innerHTML = "";
  for (const row of sets) {
    const div = document.createElement("div");
    div.className = "by-set-row";
    div.innerHTML = `
      <span class="set-name">${row.set_name}</span>
      <span class="value">$${(row.set_value ?? 0).toFixed(2)}</span>
    `;
    container.appendChild(div);
  }  
  } catch (err) {
    renderLoadError(container, loadBySet);
  }
}

function setDashboardVisibility(visible) {
  [
    "price-status",
    "stats-bar",
    "by-set-header",
    "by-set",
    "cards-header",
    "cards-container"
  ].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = visible ? "" : "none";
  });
}

function setEmptyStateVisible(visible) {
  const emptyState = document.getElementById("empty-state");
  if (emptyState) {
    emptyState.classList.toggle("visible", visible);
  }
  setDashboardVisibility(!visible);
}

async function loadCards() {
  const container = document.getElementById("cards-container");
  // 6 skeleton cards while loading
  container.innerHTML = Array.from({ length: 6 }).map(() => `
    <div class="skeleton-card">
      <div class="skeleton skeleton-image"></div>
      <div class="skeleton skeleton-name"></div>
      <div class="skeleton skeleton-set"></div>
      <div class="skeleton skeleton-price"></div>
    </div>
  `).join("");
  try {
  const response = await fetch("/cards");
  if (!response.ok) throw new Error("Failed to fetch");
  const cards = await response.json();
  container.innerHTML = "";

  const isEmpty = cards.length === 0;
  setEmptyStateVisible(isEmpty);
  if (isEmpty) return;

  for (const card of cards) {
    const div = document.createElement("div");
    div.className = "card";
    div.dataset.cardId = card.id;
    div.innerHTML = `
      <img src="${card.image_url}" alt="${card.name}">
      <div class="card-name">${card.name}</div>
      <div class="card-set">${card.set_name}</div>
      <div class="card-price">$${(card.market_price ?? 0).toFixed(2)}</div>
    `;
    container.appendChild(div);
  }
  } catch (err) {
    renderLoadError(container, loadCards);
  }
}

function refreshAll() {
  loadStats();
  loadBySet();
  loadCards();
  loadLastUpdated();
}

async function loadLastUpdated() {
  const response = await fetch("/stats/last-updated");
  if (!response.ok) throw new Error("Failed to fetch");
  const { last_updated } = await response.json();
  const el = document.getElementById("price-status-date");
  el.textContent = last_updated || "never";
}

async function refreshPrices() {
  const button = document.getElementById("refresh-prices-button");
  button.disabled = true;
  button.textContent = "Refreshing…";

  try {
    const response = await fetch("/collection/refresh-prices", { method: "POST" });
    if (!response.ok) throw new Error("Server error");
    // Reload everything that depends on prices
    refreshAll();
    loadLastUpdated();
  } catch (err) {
    alert("Failed to refresh prices: " + err.message);
  } finally {
    button.disabled = false;
    button.textContent = "Refresh prices";
  }
}

// -------- Searchable dropdown component --------

// Each dropdown's selected value is tracked here, keyed by data-filter attribute.
const dropdownValues = {};

/**
 * Build a searchable dropdown inside the given container element.
 * options: array of { value, label } objects.
 * onChange: callback invoked when selection changes (receives the new value, or null).
 */
function createDropdown(container, options, placeholder, onChange) {
  const input = document.createElement("input");
  input.type = "text";
  input.className = "dropdown-input";
  input.placeholder = placeholder;
  input.readOnly = true;  // we'll toggle this when user starts typing

  const panel = document.createElement("div");
  panel.className = "dropdown-panel";

  container.appendChild(input);
  container.appendChild(panel);

  let allOptions = options;
  let isOpen = false;

  function renderOptions(filter = "") {
    panel.innerHTML = "";

    // "Clear selection" row at the top
    const clearRow = document.createElement("div");
    clearRow.className = "dropdown-clear";
    clearRow.textContent = "✕ Clear selection";
    clearRow.addEventListener("click", () => {
      input.value = "";
      onChange(null);
      closePanel();
    });
    panel.appendChild(clearRow);

    const lower = filter.toLowerCase();
    const filtered = allOptions.filter(opt => opt.label.toLowerCase().includes(lower));

    if (filtered.length === 0) {
      const empty = document.createElement("div");
      empty.className = "dropdown-option empty";
      empty.textContent = "No matches";
      panel.appendChild(empty);
      return;
    }

    for (const opt of filtered) {
      const row = document.createElement("div");
      row.className = "dropdown-option";
      row.textContent = opt.label;
      row.addEventListener("click", () => {
        input.value = opt.label;
        input.readOnly = true;
        onChange(opt.value);
        closePanel();
      });
      panel.appendChild(row);
    }
  }

  function openPanel() {
    isOpen = true;
    panel.classList.add("open");
    input.readOnly = false;
    input.select();  // highlight any existing text so typing replaces it
    renderOptions(input.value === input.dataset.label ? "" : input.value);
  }

  function closePanel() {
    isOpen = false;
    panel.classList.remove("open");
    input.readOnly = true;
  }

  input.addEventListener("click", () => {
    if (isOpen) closePanel(); else openPanel();
  });

  input.addEventListener("input", () => {
  if (isOpen) renderOptions(input.value);

  // If user is typing/erasing, invalidate the current selection.
  // It only becomes valid again when they explicitly click an option.
  const typedValue = input.value.trim();
  const exactMatch = allOptions.find(opt => opt.label === typedValue);
  if (exactMatch) {
    onChange(exactMatch.value);
  } else {
    onChange(null);
  }
  });

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (!container.contains(e.target)) closePanel();
  });

  return {
    setOptions(newOptions) {
      allOptions = newOptions;
      if (isOpen) renderOptions(input.value);
    }
  };
}

// Initialize all dropdowns on page load
async function initDropdowns() {
  // Fetch all five lists in parallel
  const [setsRes, raritiesRes, typesRes, supertypesRes, subtypesRes] = await Promise.all([
    fetch("/api/filters/sets").then(r => r.json()),
    fetch("/api/filters/rarities").then(r => r.json()),
    fetch("/api/filters/types").then(r => r.json()),
    fetch("/api/filters/supertypes").then(r => r.json()),
    fetch("/api/filters/subtypes").then(r => r.json()),
  ]);

  // Sets are objects (need id + name); the rest are plain strings.
  const setOptions = setsRes.map(s => ({
    value: s.id,
    label: `${s.name} (${s.series})`
  }));
  const stringOptions = (list) => list.map(s => ({ value: s, label: s }));

  setupDropdown("set", setOptions, "Any set");
  setupDropdown("rarity", stringOptions(raritiesRes), "Any rarity");
  setupDropdown("type", stringOptions(typesRes), "Any type");
  setupDropdown("supertype", stringOptions(supertypesRes), "Any supertype");
  setupDropdown("subtype", stringOptions(subtypesRes), "Any subtype");
}

function setupDropdown(filterKey, options, placeholder) {
  const container = document.querySelector(`.searchable-dropdown[data-filter="${filterKey}"]`);
  if (!container) return;

  createDropdown(container, options, placeholder, (newValue) => {
    if (newValue === null) {
      delete dropdownValues[filterKey];
    } else {
      dropdownValues[filterKey] = newValue;
    }
  });
}

// -------- Search & pagination --------

let currentDetailCardId = null;
let currentAcquireCard = null;

let searchState = {
  page: 1,
  pageSize: 12,
  totalCount: 0,
};

async function doSearch(resetPage = true) {
  if (resetPage) {
    searchState.page = 1;
    searchState.pageSize = parseInt(document.getElementById("page-size-select").value, 10);
  }

  const filters = collectFilters();

  const container = document.getElementById("search-results");
  const pagination = document.getElementById("pagination");
  container.innerHTML = "Searching...";
  pagination.classList.remove("visible");

  try {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== null && value !== "" && value !== undefined) {
        params.append(key, value);
      }
    }
    params.append("page", searchState.page);
    params.append("page_size", searchState.pageSize);

    const response = await fetch(`/api/search?${params.toString()}`);
    if (!response.ok) throw new Error("Failed to fetch");
    const envelope = await response.json();

    searchState.totalCount = envelope.totalCount;
    const results = envelope.data;

    container.innerHTML = "";

    if (results.length === 0) {
      container.textContent = "No cards found.";
      return;
    }

    for (const card of results) {
      const div = document.createElement("div");
      div.className = "search-result";
      div.innerHTML = `
        <img src="${card.images.small}" alt="${card.name}">
        <div class="card-name">${card.name}</div>
        <div class="card-set">${card.set.name} · #${card.number}</div>
        <button class="add-button">Add to Collection</button>
      `;
      container.appendChild(div);
      div.querySelector(".add-button").addEventListener("click", () => openModal(card));
    }

    renderPagination();
  } catch (e) {
    renderLoadError(container, () => doSearch(false));
  }
}

function collectFilters() {
  return {
    name: document.getElementById("filter-name").value.trim(),
    series: document.getElementById("filter-series").value.trim(),
    artist: document.getElementById("filter-artist").value.trim(),
    hp_min: document.getElementById("filter-hp-min").value || null,
    hp_max: document.getElementById("filter-hp-max").value || null,
    set_id: dropdownValues.set || null,
    rarity: dropdownValues.rarity || null,
    types: dropdownValues.type || null,
    supertype: dropdownValues.supertype || null,
    subtype: dropdownValues.subtype || null,
  };
}

function clearFilters() {
  document.getElementById("filter-name").value = "";
  document.getElementById("filter-series").value = "";
  document.getElementById("filter-artist").value = "";
  document.getElementById("filter-hp-min").value = "";
  document.getElementById("filter-hp-max").value = "";

  // Reset all dropdown displays and clear stored values
  document.querySelectorAll(".searchable-dropdown .dropdown-input").forEach(input => {
    input.value = "";
  });
  for (const key in dropdownValues) delete dropdownValues[key];
}

function renderPagination() {
  const pagination = document.getElementById("pagination");
  const totalPages = Math.max(1, Math.ceil(searchState.totalCount / searchState.pageSize));

  if (searchState.totalCount <= searchState.pageSize) {
    pagination.classList.remove("visible");
    return;
  }

  pagination.innerHTML = `
    <button id="prev-page" ${searchState.page === 1 ? "disabled" : ""}>← Previous</button>
    <span class="page-info">Page ${searchState.page} of ${totalPages} (${searchState.totalCount} results)</span>
    <button id="next-page" ${searchState.page >= totalPages ? "disabled" : ""}>Next →</button>
  `;
  pagination.classList.add("visible");

  document.getElementById("prev-page").addEventListener("click", () => {
    if (searchState.page > 1) {
      searchState.page -= 1;
      doSearch(false);
    }
  });

  document.getElementById("next-page").addEventListener("click", () => {
    searchState.page += 1;
    doSearch(false);
  });
}

// -------- Modal --------

function openModal(card) {
  currentAcquireCard = card;
  document.getElementById("modal-card-preview").innerHTML = `
    <img src="${card.images.small}" alt="${card.name}">
    <div>
      <div class="preview-name">${card.name}</div>
      <div class="preview-set">${card.set.name} · #${card.number}</div>
    </div>
  `;
  document.getElementById("form-date").value = new Date().toISOString().slice(0, 10);
  document.getElementById("modal-overlay").classList.add("open");
}

function closeModal() {
  document.getElementById("modal-overlay").classList.remove("open");
  currentAcquireCard = null;
}


async function openDetail(cardId) {
  currentDetailCardId = cardId;
  const [card, ownership] = await Promise.all([
    fetch(`/cards/${cardId}`).then(r => r.json()),
    fetch(`/cards/${cardId}/ownership`).then(r => r.json())
  ]);
  document.getElementById("detail-card-info").innerHTML = `
    <img src="${card.image_url}" alt="${card.name}">
    <div class="info">
      <div class="name">${card.name}</div>
      <div class="set">${card.set_name} · #${card.number}</div>
      <div class="market-label">Current Market Value</div>
      <div class="market-value">$${(card.market_price ?? 0).toFixed(2)}</div>
      </div>
  `;

  const ownershipList = document.getElementById("detail-ownership-list");
  ownershipList.innerHTML = "";

  if (ownership.length === 0) {
    document.getElementById("detail-ownership-header").textContent =
      "You don't own any copies of this card.";
  } else {
    document.getElementById("detail-ownership-header").textContent =
      `You own ${ownership.length} ${ownership.length === 1 ? "copy" : "copies"} of this card:`;

    for (const row of ownership) {
      const div = document.createElement("div");
      div.className = "ownership-row";
      div.innerHTML = `
        <div class="left">
          <div class="condition">${row.condition} × ${row.quantity}</div>
          <div class="meta">Acquired ${row.acquired_date || "unknown date"}</div>
        </div>
        <div class="price">${row.purchase_price !== null ? `$${row.purchase_price.toFixed(2)}` : "—"}</div>
        <div class="actions">
          <button class="icon-btn" data-owned-id="${row.id}" data-action="edit">Edit</button>
          <button class="icon-btn danger" data-owned-id="${row.id}" data-action="delete">Delete</button>
        </div>
        <div class="confirm-delete">
          <span class="confirm-text">Delete this row?</span>
          <button class="icon-btn danger" data-owned-id="${row.id}" data-action="confirm-delete">Confirm</button>
          <button class="icon-btn" data-owned-id="${row.id}" data-action="cancel-delete">Cancel</button>
        </div>
        <div class="edit-form">
          <input type="number" class="edit-quantity" min="1" value="${row.quantity}">
          <select class="edit-condition">
            <option ${row.condition === "Near Mint" ? "selected" : ""}>Near Mint</option>
            <option ${row.condition === "Lightly Played" ? "selected" : ""}>Lightly Played</option>
            <option ${row.condition === "Moderately Played" ? "selected" : ""}>Moderately Played</option>
            <option ${row.condition === "Heavily Played" ? "selected" : ""}>Heavily Played</option>
            <option ${row.condition === "Damaged" ? "selected" : ""}>Damaged</option>
          </select>
          <input type="number" class="edit-price" step="0.01" min="0" value="${row.purchase_price ?? ''}" placeholder="Price">
          <input type="date" class="edit-date" value="${row.acquired_date ?? ''}">
          <button class="icon-btn" data-owned-id="${row.id}" data-action="save-edit">Save</button>
          <button class="icon-btn" data-owned-id="${row.id}" data-action="cancel-edit">Cancel</button>
        </div>
      `;
      ownershipList.appendChild(div);
    }
  }

  document.getElementById("detail-overlay").classList.add("open");
}

function closeDetail() {
  document.getElementById("detail-overlay").classList.remove("open");
}

async function deleteOwnedRow(ownedId) {
  try {
    const response = await fetch(`/collection/owned/${ownedId}`, {
      method: "DELETE",
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || "Failed to delete owned row.");
    }

    if (data.cascade_deleted_card) {
      closeDetail();
    } else {
      openDetail(currentDetailCardId);
    }
  } catch (err) {
    alert("Unable to delete owned row: " + err.message);
  } finally {
    refreshAll();
  }
}

// -------- Event wiring --------

async function saveOwnedEdit(row, ownedId) {
  try {
    const quantityInput = row.querySelector(".edit-quantity");
    const conditionInput = row.querySelector(".edit-condition");
    const priceInput = row.querySelector(".edit-price");
    const dateInput = row.querySelector(".edit-date");

    const quantity = parseInt(quantityInput.value, 10);
    const condition = conditionInput.value;
    const purchase_price = priceInput.value !== "" ? parseFloat(priceInput.value) : null;
    const acquired_date = dateInput.value || null;

    if (Number.isNaN(quantity) || quantity < 1) {
      throw new Error("Quantity must be at least 1.");
    }

    const body = {
      quantity,
      condition,
      purchase_price,
      acquired_date,
    };

    const response = await fetch(`/collection/owned/${ownedId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || "Failed to update owned row.");
    }

    openDetail(currentDetailCardId);
  } catch (err) {
    alert("Unable to save owned row: " + err.message);
  } finally {
    refreshAll();
  }
}

document.getElementById("search-button").addEventListener("click", () => doSearch(true));
document.getElementById("clear-filters").addEventListener("click", clearFilters);

document.getElementById("advanced-toggle").addEventListener("click", () => {
  document.getElementById("advanced-filters").classList.toggle("open");
  document.getElementById("advanced-toggle-icon").classList.toggle("open");
});

// Press Enter in any text input to trigger search
document.querySelectorAll(".filter input").forEach(input => {
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") doSearch(true);
  });
});

document.getElementById("modal-close").addEventListener("click", closeModal);

document.getElementById("modal-overlay").addEventListener("click", (e) => {
  if (e.target.id === "modal-overlay") closeModal();
});

document.getElementById("detail-overlay").addEventListener("click", (e) => {
  if (e.target.id === "detail-overlay") closeDetail();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if (document.getElementById("detail-overlay").classList.contains("open")) {
      closeDetail();
    } else {
      closeModal();
    }
  }
});

document.getElementById("acquire-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!currentAcquireCard) return;

  const submitBtn = document.getElementById("form-submit");
  submitBtn.disabled = true;
  submitBtn.textContent = "Adding...";

  const body = {
    card_id: currentAcquireCard.id,
    quantity: parseInt(document.getElementById("form-quantity").value, 10),
    purchase_price: parseFloat(document.getElementById("form-price").value) || null,
    condition: document.getElementById("form-condition").value,
    acquired_date: document.getElementById("form-date").value || null,
  };

  try {
    const response = await fetch("/collection/acquire", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error("Server error");
    closeModal();
    refreshAll();
  } catch (err) {
    alert("Failed to add card: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Add to Collection";
  }
});

document.getElementById("cards-container").addEventListener("click", (e) => {
  const cardDiv = e.target.closest(".card");
  if (!cardDiv) return;
  openDetail(cardDiv.dataset.cardId);
});

document.getElementById("detail-close").addEventListener("click", closeDetail);

document.getElementById("refresh-prices-button").addEventListener("click", refreshPrices);

document.getElementById("detail-ownership-list").addEventListener("click", (e) => {
  const button = e.target.closest(".icon-btn");
  if (!button) return;
  const ownedId = button.dataset.ownedId;
  const action = button.dataset.action;
  const row = button.closest(".ownership-row");

  switch (action) {
    case "delete":
      row.classList.add("confirming");
      break;
    case "cancel-delete":
      row.classList.remove("confirming");
      break;
    case "confirm-delete":
      deleteOwnedRow(ownedId);
      break;
    case "edit":
      row.classList.add("editing");
      break;
    case "cancel-edit":
      row.classList.remove("editing");
      break;
    case "save-edit":
      saveOwnedEdit(row, ownedId);
     break;
  }
});

// -------- Initial load --------

refreshAll();
initDropdowns();