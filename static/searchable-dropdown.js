/**
 * Build a searchable dropdown inside the given container element.
 * options: array of { value, label } objects.
 * onChange: callback invoked when selection changes (receives the new value, or null).
 */
export function createDropdown(container, options, placeholder, onChange) {
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