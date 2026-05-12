export function setAuthed(authed) {
  document.body.classList.toggle("authed", authed);
}

export async function initAuth() {
  try {
    const response = await fetch("/auth/status");
    if (!response.ok) throw new Error("status fetch failed");
    const { authed } = await response.json();
    setAuthed(authed);
  } catch {
    setAuthed(false);
  }
}

export function openLogin() {
  document.getElementById("login-error").textContent = "";
  document.getElementById("login-password").value = "";
  document.getElementById("login-overlay").classList.add("open");
  setTimeout(() => document.getElementById("login-password").focus(), 0);
}

export function closeLogin() {
  document.getElementById("login-overlay").classList.remove("open");
}

export async function apiFetch(url, options = {}) {
  const response = await fetch(url, options);
  if (response.status === 401) {
    setAuthed(false);
    openLogin();
    const err = new Error("Login required");
    err.status = 401;
    throw err;
  }
  return response;
}

export async function handleLoginSubmit(e) {
  e.preventDefault();
  const submitBtn = document.getElementById("login-submit");
  const errorEl = document.getElementById("login-error");
  const password = document.getElementById("login-password").value;

  errorEl.textContent = "";
  submitBtn.disabled = true;
  submitBtn.textContent = "Logging in…";

  try {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    if (response.status === 401) {
      errorEl.textContent = "Wrong password.";
      return;
    }
    if (response.status === 503) {
      errorEl.textContent = "Editing is not configured on this server.";
      return;
    }
    if (!response.ok) throw new Error("Server error");
    setAuthed(true);
    closeLogin();
  } catch (err) {
    errorEl.textContent = "Couldn't log in. Try again.";
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Log in";
  }
}

export async function handleLogoutClick() {
  try {
    await fetch("/auth/logout", { method: "POST" });
  } catch {}
  setAuthed(false);
}