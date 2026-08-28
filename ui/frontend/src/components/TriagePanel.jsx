import { AlertTriangle, BookOpen, Check, Copy, Loader2, Send, Target, Users } from "lucide-react";
import { useState } from "react";
import { triageTicket } from "../api";
import { Pill, UrgencyBadge } from "./Badge";
import { ConfidenceGauge } from "./ConfidenceGauge";

const PRESETS = [
  {
    label: "SSO outage",
    subject: "SAML SSO login failing for all users after IdP metadata update",
    body: "We updated our IdP's SAML metadata yesterday and now no one in our org can log in via SSO. Getting 'invalid_signature' errors. This is blocking our entire team.",
    product: "SecureVault",
    plan_tier: "Enterprise",
  },
  {
    label: "Billing question",
    subject: "Question about seat billing on Business plan",
    body: "We're on the Business plan and want to understand how seat overages are billed mid-cycle before we add 15 more users. Can you clarify the proration policy?",
    product: "DataBridge Pro",
    plan_tier: "Business",
  },
  {
    label: "Vague ticket",
    subject: "not working",
    body: "it broke, please fix",
    product: "",
    plan_tier: "",
  },
];

export function TriagePanel() {
  const [form, setForm] = useState(PRESETS[0]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = {
        subject: form.subject,
        body: form.body,
        product: form.product || null,
        plan_tier: form.plan_tier || null,
      };
      setResult(await triageTicket(payload));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function copyDraft() {
    if (!result) return;
    navigator.clipboard.writeText(result.draft_first_response).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    });
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <form onSubmit={handleSubmit} className="bracket animate-fade-up rounded-lg border border-border bg-surface">
        <span className="bracket-bl" /><span className="bracket-br" />
        <div className="flex items-center justify-between border-b border-border px-5 py-3.5">
          <span className="flex items-center gap-2">
            <span className="text-[13px] font-medium text-ink-0">New ticket</span>
            <span className="font-mono-tight text-[10px] text-ink-4">CH.01</span>
          </span>
          <div className="flex gap-1">
            {PRESETS.map((p) => (
              <button
                type="button"
                key={p.label}
                onClick={() => setForm(p)}
                className="rounded border border-border px-2 py-1 text-[11px] text-ink-3 transition hover:border-border-hover hover:text-ink-1"
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4 p-5">
          <Field label="Subject">
            <input
              value={form.subject}
              onChange={set("subject")}
              required
              className="w-full rounded-md border border-border bg-canvas px-3 py-2 text-sm text-ink-0 outline-none transition placeholder:text-ink-4 focus:border-signal-dim"
            />
          </Field>

          <Field label="Body">
            <textarea
              value={form.body}
              onChange={set("body")}
              required
              rows={6}
              className="w-full resize-none rounded-md border border-border bg-canvas px-3 py-2 text-sm leading-relaxed text-ink-0 outline-none transition placeholder:text-ink-4 focus:border-signal-dim"
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Product">
              <input
                value={form.product}
                onChange={set("product")}
                placeholder="optional"
                className="w-full rounded-md border border-border bg-canvas px-3 py-2 text-sm text-ink-0 outline-none transition placeholder:text-ink-4 focus:border-signal-dim"
              />
            </Field>
            <Field label="Plan tier">
              <select
                value={form.plan_tier}
                onChange={set("plan_tier")}
                className="w-full rounded-md border border-border bg-canvas px-3 py-2 text-sm text-ink-0 outline-none transition focus:border-signal-dim"
              >
                <option value="">optional</option>
                <option>Starter</option>
                <option>Professional</option>
                <option>Business</option>
                <option>Enterprise</option>
              </select>
            </Field>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-signal py-2.5 text-[13px] font-semibold text-canvas transition hover:brightness-110 disabled:opacity-50"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={13} />}
            {loading ? "Classifying…" : "Triage ticket"}
          </button>
          {error && <p className="text-xs text-p1">{error}</p>}
        </div>
      </form>

      <div className="min-h-[440px]">
        {!result && !loading && (
          <EmptyState icon={<Target size={20} />} text="Submit a ticket to see the classification, KB match, and draft response." />
        )}
        {loading && (
          <EmptyState icon={<Loader2 size={20} className="animate-spin" />} text="Classifying against the knowledge base…" />
        )}
        {result && (
          <div className="bracket animate-fade-up space-y-4 rounded-lg border border-border bg-surface">
            <span className="bracket-bl" /><span className="bracket-br" />
            <div className="flex items-start justify-between gap-4 border-b border-border px-5 py-4">
              <div>
                <div className="mb-2 flex items-center gap-2">
                  <UrgencyBadge value={result.urgency} />
                  <Pill>{result.issue_category}</Pill>
                </div>
                <h3 className="text-[15px] font-semibold text-ink-0">{result.product_area}</h3>
                <p className="mt-1 max-w-md text-[13px] leading-relaxed text-ink-2">{result.urgency_reasoning}</p>
              </div>
              <ConfidenceGauge value={result.confidence} />
            </div>

            <div className="space-y-4 px-5 pb-5">
              <Row icon={<Users size={13} />} label="Responder team">
                <span className="text-[13px] font-medium text-ink-0">{result.recommended_responder_team}</span>
              </Row>

              {result.kb_match ? (
                <div className="rounded-md border border-radar/30 bg-radar/[0.06] px-3.5 py-3">
                  <div className="mb-1 flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-radar">
                      <BookOpen size={12} /> knowledge-base match
                    </span>
                    <span className="font-mono-tight text-[11px] text-ink-4">
                      {Math.round(result.kb_match.relevance_score * 100)}% relevance
                    </span>
                  </div>
                  <p className="font-mono-tight text-[13px] text-ink-0">{result.kb_match.doc_path}</p>
                  <p className="text-[12px] text-ink-3">{result.kb_match.section}</p>
                </div>
              ) : (
                <div className="flex items-center gap-2 rounded-md border border-border bg-canvas px-3.5 py-3 text-[12px] text-ink-3">
                  <AlertTriangle size={13} /> No relevant knowledge-base doc found.
                </div>
              )}

              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <span className="text-[11px] uppercase tracking-wide text-ink-3">Draft first response</span>
                  <button onClick={copyDraft} className="flex items-center gap-1 text-[11px] text-signal transition hover:brightness-110">
                    {copied ? <Check size={12} /> : <Copy size={12} />}
                    {copied ? "Copied" : "Copy"}
                  </button>
                </div>
                <p className="whitespace-pre-wrap rounded-md border border-border bg-canvas px-3.5 py-3 text-[13px] leading-relaxed text-ink-1">
                  {result.draft_first_response}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div className="space-y-1.5">
      <label className="text-[11px] font-medium uppercase tracking-wide text-ink-3">{label}</label>
      {children}
    </div>
  );
}

function Row({ icon, label, children }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-border bg-canvas px-3.5 py-3">
      <span className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-ink-3">
        {icon} {label}
      </span>
      {children}
    </div>
  );
}

function EmptyState({ icon, text }) {
  return (
    <div className="flex h-full min-h-[440px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border p-8 text-center">
      <span className="text-ink-4">{icon}</span>
      <p className="max-w-[220px] text-[13px] text-ink-3">{text}</p>
    </div>
  );
}
