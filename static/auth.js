import { refreshAll } from './data-loaders.js';

let currentUser = null;

export const getCurrentUser = () => currentUser ? { ...currentUser } : null;

export function setCurrentUser(user) {
  if (user === null) {
    currentUser = null;
  } else {
    currentUser = { ...user };
  }
  renderAuthState();
}

function renderAuthState() {
  document.body.classList.toggle('authed', currentUser !== null);
  renderAuthBar();
  if (currentUser) refreshAll();
}

function renderAuthBar() {
  const el = document.getElementById('auth-username');
  if (currentUser) el.textContent = `Hi, ${currentUser.username}`;
}

export async function initAuth() {
  try {
    const response = await fetch("/auth/status");
    if (!response.ok) throw new Error("status fetch failed");
    const { user } = await response.json();
    setCurrentUser(user);
  } catch {
    setCurrentUser(null);
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
    setCurrentUser(null);
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
    setCurrentUser({ username: "temp" });
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
  setCurrentUser(null);
}