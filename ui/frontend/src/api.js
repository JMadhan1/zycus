// Local dev: no env var set, falls back to "/api" which vite.config.js proxies
// to localhost:8000 (stripping the /api prefix). Production (Vercel): set
// VITE_API_BASE_URL to the deployed backend's origin (e.g. Render), no
// trailing slash — requests go straight to it, no proxy involved.
const BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.detail || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export function triageTicket(payload) {
  return request("/triage", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function listAccounts() {
  return request("/accounts");
}

export function getAccountBrief(accountId) {
  return request(`/accounts/${encodeURIComponent(accountId)}/brief`);
}

export function getStats() {
  return request("/stats");
}
