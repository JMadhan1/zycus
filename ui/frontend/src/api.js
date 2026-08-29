// VITE_API_BASE_URL is the correct way to point this at a backend and
// should be set in Vercel's project settings. But Vite only bakes env vars
// in at BUILD time — if it's missing or the build ran before it was set,
// "/api" silently resolves to nothing on a static host (no dev proxy exists
// in production) and every request 405s against Vercel's own SPA rewrite.
// So the fallback branches on dev vs. prod instead of always being "/api":
// dev falls back to the vite.config.js proxy (-> localhost:8000), a
// production build with no env var set falls back to the known deployed
// backend directly, so a missed Vercel env var degrades to "still works"
// instead of "silently broken".
const BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? "/api" : "https://zycus-support-ai-api.onrender.com");

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
