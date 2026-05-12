import { apiFetch } from "/static/auth.js";

export function refreshAll() {
  loadStats();
  loadBySet();
  loadCards();
  loadLastUpdated();
}

export async function refreshPrices() {
  const button = document.getElementById("refresh-prices-button");
  button.disabled = true;
  button.textContent = "Refreshing…";

  try {
    const response = await apiFetch("/collection/refresh-prices", { method: "POST" });
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
      <img src="${card.image_url}" alt="" width="240" height="330" loading="lazy" decoding="async">
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

async function loadLastUpdated() {
  const response = await fetch("/stats/last-updated");
  if (!response.ok) throw new Error("Failed to fetch");
  const { last_updated } = await response.json();
  const el = document.getElementById("price-status-date");
  el.textContent = last_updated || "never";
}
