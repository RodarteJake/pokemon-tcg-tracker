   // -------- Data loaders --------

    async function loadStats() {
      const [valueRes, spentRes] = await Promise.all([
        fetch("/stats/total-value"),
        fetch("/stats/total-spent")
      ]);
      const { total_value } = await valueRes.json();
      const { total_spent } = await spentRes.json();
      const gain = total_value - total_spent;
      const gainClass = gain >= 0 ? "positive" : "negative";
      const gainSign = gain >= 0 ? "+" : "";

      document.getElementById("stats-bar").innerHTML = `
        <div class="stat-card">
          <div class="stat-label">Total Value</div>
          <div class="stat-value positive">$${total_value.toFixed(2)}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Spent</div>
          <div class="stat-value">$${total_spent.toFixed(2)}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Gain / Loss</div>
          <div class="stat-value ${gainClass}">${gainSign}$${gain.toFixed(2)}</div>
        </div>
      `;
    }

    async function loadBySet() {
      const response = await fetch("/stats/by-set");
      const sets = await response.json();
      const container = document.getElementById("by-set");
      container.innerHTML = "";
      for (const row of sets) {
        const div = document.createElement("div");
        div.className = "by-set-row";
        div.innerHTML = `
          <span class="set-name">${row.set_name}</span>
          <span class="value">$${row.set_value.toFixed(2)}</span>
        `;
        container.appendChild(div);
      }
    }

    async function loadCards() {
      const response = await fetch("/cards");
      const cards = await response.json();
      const container = document.getElementById("cards-container");
      container.innerHTML = "";
      for (const card of cards) {
        const div = document.createElement("div");
        div.className = "card";
        div.innerHTML = `
          <img src="${card.image_url}" alt="${card.name}">
          <div class="card-name">${card.name}</div>
          <div class="card-set">${card.set_name}</div>
          <div class="card-price">$${card.market_price.toFixed(2)}</div>
        `;
        container.appendChild(div);
      }
    }

    function refreshAll() {
      loadStats();
      loadBySet();
      loadCards();
    }

// -------- Search & pagination --------

let searchState = {
  query: "",
  page: 1,
  pageSize: 12,
  totalCount: 0,
};

async function doSearch(resetPage = true) {
  const input = document.getElementById("search-input");
  const query = input.value.trim();
  if (!query) return;

  if (resetPage) {
    searchState.query = query;
    searchState.page = 1;
    searchState.pageSize = parseInt(document.getElementById("page-size-select").value, 10);
  }

  const container = document.getElementById("search-results");
  const pagination = document.getElementById("pagination");
  container.innerHTML = "Searching...";
  pagination.classList.remove("visible");

  try {
    const url = `/api/search?name=${encodeURIComponent(searchState.query)}&page=${searchState.page}&page_size=${searchState.pageSize}`;
    const response = await fetch(url);
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
    container.textContent = "Search failed: " + e.message;
  }
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

    // -------- Event wiring --------

    document.getElementById("search-button").addEventListener("click", doSearch);
    document.getElementById("search-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter") doSearch();
    });

    document.getElementById("modal-close").addEventListener("click", closeModal);
    document.getElementById("modal-overlay").addEventListener("click", (e) => {
      if (e.target.id === "modal-overlay") closeModal();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModal();
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

    // -------- Initial load --------
    refreshAll();