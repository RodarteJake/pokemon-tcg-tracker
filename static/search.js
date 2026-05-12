import { createDropdown } from "/static/searchable-dropdown.js";
import { openAcquireModal } from "/static/edit-collection.js";
import { renderLoadError } from "/static/data-loaders.js";

// Each dropdown's selected value is tracked here, keyed by data-filter attribute.
const dropdownValues = {};

let searchState = {
  page: 1,
  pageSize: 12,
  totalCount: 0,
};

// Initialize all dropdowns on page load
export async function initDropdowns() {
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

export async function doSearch(resetPage = true) {
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
        <img src="${card.images.small}" alt="" width="240" height="330" loading="lazy" decoding="async">
        <div class="card-name">${card.name}</div>
        <div class="card-set">${card.set.name} · #${card.number}</div>
        <button class="add-button auth-required">Add to Collection</button>
      `;
      container.appendChild(div);
      div.querySelector(".add-button").addEventListener("click", () => openAcquireModal(card));
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

export function clearFilters() {
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