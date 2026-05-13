import { createDropdown } from "/static/searchable-dropdown.js";
import {
  initAuth,
  openLogin,
  closeLogin,
  apiFetch,
  handleLoginSubmit,
  handleLogoutClick,
} from "/static/auth.js";
import { refreshAll, refreshPrices, renderLoadError } from "/static/data-loaders.js";
import {
  openAcquireModal,
  closeAcquireModal,
  openDetail,
  closeDetail,
  handleAcquireSubmit,
  deleteOwnedRow,
  saveOwnedEdit,
} from "/static/edit-collection.js";
import { doSearch, clearFilters, initDropdowns } from "/static/search.js";

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

document.getElementById("modal-close").addEventListener("click", closeAcquireModal);

document.getElementById("modal-overlay").addEventListener("click", (e) => {
  if (e.target.id === "modal-overlay") closeAcquireModal();
});

document.getElementById("detail-overlay").addEventListener("click", (e) => {
  if (e.target.id === "detail-overlay") closeDetail();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if (document.getElementById("login-overlay").classList.contains("open")) {
      closeLogin();
    } else if (document.getElementById("detail-overlay").classList.contains("open")) {
      closeDetail();
    } else {
      closeAcquireModal();
    }
  }
});

document.getElementById("login-button").addEventListener("click", openLogin);

document.getElementById("login-close").addEventListener("click", closeLogin);

document.getElementById("login-overlay").addEventListener("click", (e) => {
  if (e.target.id === "login-overlay") closeLogin();
});

document.getElementById("login-form").addEventListener("submit", handleLoginSubmit);

document.getElementById("logout-button").addEventListener("click", handleLogoutClick);

document.getElementById("cards-container").addEventListener("click", (e) => {
  const cardDiv = e.target.closest(".card");
  if (!cardDiv) return;
  openDetail(cardDiv.dataset.cardId);
});

document.getElementById("detail-close").addEventListener("click", closeDetail);

document.getElementById("acquire-form").addEventListener("submit", handleAcquireSubmit);

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

initAuth();
initDropdowns();