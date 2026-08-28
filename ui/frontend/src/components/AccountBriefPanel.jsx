import { AlertCircle, ArrowRight, ClipboardList, Loader2, Search, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getAccountBrief, listAccounts } from "../api";
import { Pill, SeverityBadge } from "./Badge";

export function AccountBriefPanel() {
  const [accounts, setAccounts] = useState([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    listAccounts().then(setAccounts).catch((e) => setError(e.message));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return accounts;
    return accounts.filter((a) => a.company.toLowerCase().includes(q) || a.account_id.toLowerCase().includes(q));
  }, [accounts, query]);

  async function select(account) {
    setSelected(account);
    setBrief(null);
    setError(null);
    setLoading(true);
    try {
      setBrief(await getAccountBrief(account.account_id));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[260px_minmax(0,1fr)]">
      <div className="animate-fade-up flex max-h-[640px] flex-col rounded-lg border border-border bg-surface">
        <div className="border-b border-border px-4 py-3.5">
          <p className="mb-2.5 text-[13px] font-medium text-ink-0">Accounts</p>
          <div className="relative">
            <Search size={13} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-4" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search…"
              className="w-full rounded-md border border-border bg-canvas py-1.5 pl-8 pr-2.5 text-[13px] text-ink-0 outline-none transition placeholder:text-ink-4 focus:border-signal-dim"
            />
          </div>
        </div>
        <div className="scrollbar-thin flex-1 space-y-0.5 overflow-y-auto p-2">
          {filtered.map((a) => (
            <button
              key={a.account_id}
              onClick={() => select(a)}
              className={`flex w-full items-center justify-between rounded-md px-2.5 py-2 text-left text-[13px] transition ${
                selected?.account_id === a.account_id ? "bg-surface-raised text-ink-0" : "text-ink-2 hover:bg-surface-raised/60 hover:text-ink-0"
              }`}
            >
              <span>
                <span className="block font-medium">{a.company}</span>
                <span className="font-mono-tight block text-[11px] text-ink-4">{a.account_id}</span>
              </span>
              {selected?.account_id === a.account_id && <ArrowRight size={12} className="text-signal" />}
            </button>
          ))}
          {filtered.length === 0 && <p className="px-2.5 py-4 text-[13px] text-ink-4">No matches.</p>}
        </div>
      </div>

      <div className="min-h-[440px]">
        {!selected && <EmptyState icon={<ClipboardList size={20} />} text="Pick an account to generate its QBR brief." />}
        {selected && loading && (
          <EmptyState icon={<Loader2 size={20} className="animate-spin" />} text={`Reading tickets & escalation notes for ${selected.company}…`} />
        )}
        {selected && error && !loading && (
          <div className="rounded-lg border border-p1/30 bg-p1/[0.06] p-5 text-[13px] text-p1">{error}</div>
        )}
        {brief && !loading && (
          <div className="animate-fade-up space-y-5 rounded-lg border border-border bg-surface">
            <div className="flex items-start justify-between gap-4 border-b border-border px-5 py-4">
              <div>
                <h3 className="text-[15px] font-semibold text-ink-0">{brief.company}</h3>
                <p className="font-mono-tight text-[11px] text-ink-4">{brief.account_id}</p>
              </div>
              <Pill>
                {brief.tickets_analyzed} ticket{brief.tickets_analyzed === 1 ? "" : "s"} · {brief.window_days}d
              </Pill>
            </div>

            <div className="space-y-5 px-5 pb-5">
              <p className="rounded-md border-l-2 border-signal bg-canvas px-4 py-3 text-[13px] leading-relaxed text-ink-1">
                {brief.executive_summary}
              </p>

              <div>
                <p className="mb-2 flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-ink-3">
                  <AlertCircle size={12} />
                  Open risks {brief.open_risks.length > 0 && `(${brief.open_risks.length})`}
                </p>
                {brief.open_risks.length === 0 ? (
                  <div className="flex items-center gap-2 rounded-md border border-border bg-canvas px-3.5 py-3 text-[12px] text-ink-3">
                    <ShieldCheck size={13} /> No flagged risks.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {brief.open_risks.map((r, i) => (
                      <div key={i} className="rounded-md border border-border bg-canvas px-3.5 py-3">
                        <div className="mb-1.5 flex items-center justify-between gap-2">
                          <p className="text-[13px] font-medium text-ink-0">{r.risk}</p>
                          <SeverityBadge value={r.severity} />
                        </div>
                        <p className="border-l-2 border-border-hover pl-3 text-[12.5px] italic text-ink-3">"{r.evidence_quote}"</p>
                        {r.source_ticket_id && (
                          <p className="font-mono-tight mt-1.5 text-[10.5px] text-ink-4">{r.source_ticket_id}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <p className="mb-2 text-[11px] uppercase tracking-wide text-ink-3">Talking points</p>
                <ul className="space-y-2">
                  {brief.talking_points.map((tp, i) => (
                    <li key={i} className="flex gap-2.5 text-[13px] leading-relaxed text-ink-1">
                      <span className="font-mono-tight mt-0.5 text-ink-4">{String(i + 1).padStart(2, "0")}</span>
                      <span>{tp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function EmptyState({ icon, text }) {
  return (
    <div className="flex h-full min-h-[440px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border p-8 text-center">
      <span className="text-ink-4">{icon}</span>
      <p className="max-w-[240px] text-[13px] text-ink-3">{text}</p>
    </div>
  );
}
