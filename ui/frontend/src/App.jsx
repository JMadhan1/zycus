import { ClipboardList, Database, FileText, Radio, Target, Ticket } from "lucide-react";
import { useEffect, useState } from "react";
import { AccountBriefPanel } from "./components/AccountBriefPanel";
import { TriagePanel } from "./components/TriagePanel";
import { getStats } from "./api";

const TABS = [
  { id: "triage", label: "Triage", icon: Target },
  { id: "accounts", label: "Account briefs", icon: ClipboardList },
];

export default function App() {
  const [tab, setTab] = useState("triage");
  const [stats, setStats] = useState(null);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
  }, []);

  return (
    <div className="relative min-h-screen bg-canvas">
      <div className="bg-grid pointer-events-none absolute inset-0" aria-hidden="true" />
      <div className="relative mx-auto max-w-6xl px-6">
        <header className="flex items-center justify-between border-b border-border py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-7 w-7 items-center justify-center rounded bg-signal/15 text-signal">
              <Target size={15} strokeWidth={2.4} />
            </div>
            <div className="leading-none">
              <p className="font-mono-tight text-[13px] font-medium text-ink-0">support-ai</p>
              <p className="text-[10px] text-ink-3">triage · account intelligence</p>
            </div>
          </div>

          <nav className="flex items-center gap-1">
            {TABS.map((t) => {
              const Icon = t.icon;
              const active = tab === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors ${
                    active ? "bg-surface-raised text-ink-0" : "text-ink-3 hover:text-ink-1"
                  }`}
                >
                  <Icon size={14} strokeWidth={2} />
                  {t.label}
                </button>
              );
            })}
          </nav>

          <div className="flex items-center gap-2 rounded-md border border-border bg-surface px-2.5 py-1.5">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-blink absolute inline-flex h-full w-full rounded-full bg-p4" />
            </span>
            <span className="font-mono-tight text-[11px] text-ink-2">groq · gpt-oss-20b</span>
          </div>
        </header>

        {stats && (
          <div className="flex items-center gap-6 border-b border-border py-3 text-[11px] text-ink-3">
            <StatItem icon={<Ticket size={12} />} value={stats.tickets} label="tickets indexed" />
            <StatItem icon={<Database size={12} />} value={stats.accounts} label="accounts" />
            <StatItem icon={<FileText size={12} />} value={stats.kb_docs} label="knowledge-base docs" />
          </div>
        )}

        <main className="py-8">{tab === "triage" ? <TriagePanel /> : <AccountBriefPanel />}</main>

        <footer className="flex items-center justify-between border-t border-border py-5 text-[11px] text-ink-4">
          <span className="flex items-center gap-1.5">
            <Radio size={12} />
            local TF-IDF retrieval · cached for determinism
          </span>
          <span className="font-mono-tight">zycus / support-ai</span>
        </footer>
      </div>
    </div>
  );
}

function StatItem({ icon, value, label }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="text-signal">{icon}</span>
      <span className="font-mono-tight font-medium text-ink-1">{value}</span>
      {label}
    </span>
  );
}
