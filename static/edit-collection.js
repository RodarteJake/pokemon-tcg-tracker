import { apiFetch } from "/static/auth.js";
import { refreshAll } from "/static/data-loaders.js";

let currentDetailCardId = null;
let currentAcquireCard = null;

export function openAcquireModal(card) {
  currentAcquireCard = card;
  document.getElementById("modal-card-preview").innerHTML = `
    <img src="${card.images.small}" alt="" width="240" height="330" loading="lazy" decoding="async">
    <div>
      <div class="preview-name">${card.name}</div>
      <div class="preview-set">${card.set.name} · #${card.number}</div>
    </div>
  `;
  document.getElementById("acquire-form").reset();
  document.getElementById("form-date").value = new Date().toISOString().slice(0, 10);
  document.getElementById("modal-overlay").classList.add("open");
}

export function closeAcquireModal() {
  document.getElementById("modal-overlay").classList.remove("open");
  currentAcquireCard = null;
}


export async function openDetail(cardId) {
  currentDetailCardId = cardId;
  const [card, ownership] = await Promise.all([
    fetch(`/cards/${cardId}`).then(r => r.json()),
    fetch(`/cards/${cardId}/ownership`).then(r => r.json())
  ]);
  document.getElementById("detail-card-info").innerHTML = `
    <img src="${card.image_url}" alt="" width="240" height="330" loading="lazy" decoding="async">
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
        <div class="actions auth-required">
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

export function closeDetail() {
  document.getElementById("detail-overlay").classList.remove("open");
}

export async function deleteOwnedRow(ownedId) {
  try {
    const response = await apiFetch(`/collection/owned/${ownedId}`, {
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

export async function saveOwnedEdit(row, ownedId) {
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

    const response = await apiFetch(`/collection/owned/${ownedId}`, {
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

export async function handleAcquireSubmit(e) {
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
    const response = await apiFetch("/collection/acquire", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error("Server error");
    closeAcquireModal();
    refreshAll();
  } catch (err) {
    alert("Failed to add card: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Add to Collection";
  }
}
  
