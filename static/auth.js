import { refreshAll } from './data-loaders.js';

const AUTH_MODAL_MODES = {
  login: {
    title: "Log in",
    subtitle: "Welcome back.",
    footerPrompt: "No account?",
    toggleText: "Register",
    visibleForm: "login-form",
    hiddenForm: "register-form",
    firstField: "login-identifier",  
  },
  register: {
    title: "Create an account",
    subtitle: "Start tracking them all.",
    footerPrompt: "Have an account?",
    toggleText: "Log in",
    visibleForm: "register-form",
    hiddenForm: "login-form",
    firstField: "register-username",  
  },
};

function setAuthModalMode(mode) {
  const config = AUTH_MODAL_MODES[mode];
  document.getElementById("auth-modal-title").textContent = config.title;
  document.getElementById("auth-modal-subtitle").textContent = config.subtitle;
  document.getElementById("auth-modal-footer-prompt").textContent = config.footerPrompt;      
  document.getElementById("auth-modal-toggle").textContent = config.toggleText;
  document.getElementById(config.visibleForm).style.display = "";
  document.getElementById(config.hiddenForm).style.display = "none";
}

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

export function openLogin(mode = "login") {
  setAuthModalMode(mode);
  document.getElementById("login-error").textContent = "";
  document.getElementById("login-overlay").classList.add("open");
  const firstField = AUTH_MODAL_MODES[mode].firstField;
  setTimeout(() => document.getElementById(firstField).focus(), 0);
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
  const identifier = document.getElementById("login-identifier").value;
  const password = document.getElementById("login-password").value;

  errorEl.textContent = "";
  submitBtn.disabled = true;
  submitBtn.textContent = "Logging in…";

  try {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier, password }),
    });
    if (response.status === 401) {
      errorEl.textContent = "Invalid username or email or password.";
      return;
    }
    if (!response.ok) throw new Error("Server error");
    const user = await response.json();
    setCurrentUser(user);
    closeLogin();
  } catch (err) {
    errorEl.textContent = "Couldn't log in. Try again.";
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Log in";
  }
}

export async function handleRegisterSubmit(e) {
  e.preventDefault();
  const submitBtn = document.getElementById("register-submit");
  const errorEl = document.getElementById("login-error");
  const username = document.getElementById("register-username").value;
  const email = document.getElementById("register-email").value;
  const password = document.getElementById("register-password").value;

  errorEl.textContent = "";
  submitBtn.disabled = true;
  submitBtn.textContent = "Registering…";

  try {
    const response = await fetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    });
    if (response.status === 409) {
      errorEl.textContent = "Username or email already taken.";
      return;
    }
    if (response.status === 422) {
      errorEl.textContent = "Check your username, email, and password.";
      return;
    }
    if (!response.ok) throw new Error("Server error");
    const user = await response.json();
    setCurrentUser(user);
    closeLogin();
  } catch (err) {
    errorEl.textContent = "Couldn't register. Try again.";
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Register";
  }
}

export function handleAuthModalToggle() {
  const newMode = document.getElementById("login-form").style.display === "none" ? "login" : "register";
  document.getElementById("login-error").textContent = "";
  setAuthModalMode(newMode);
}

export async function handleLogoutClick() {
  try {
    await fetch("/auth/logout", { method: "POST" });
  } catch {}
  setCurrentUser(null);
}