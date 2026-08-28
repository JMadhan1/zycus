const TIER_COLOR = {
  P1: "var(--color-p1)",
  P2: "var(--color-p2)",
  P3: "var(--color-p3)",
  P4: "var(--color-p4)",
  high: "var(--color-p1)",
  medium: "var(--color-p2)",
  low: "var(--color-p4)",
};

const HEALTH_COLOR = {
  Healthy: "var(--color-p4)",
  New: "var(--color-signal)",
  "At Risk": "var(--color-p2)",
  Churning: "var(--color-p1)",
};

function Tag({ label, color, mono = true }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded border border-border bg-surface px-2 py-1">
      <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: color }} />
      <span className={`text-[11px] font-medium tracking-wide text-ink-1 ${mono ? "font-mono-tight" : ""}`}>
        {label}
      </span>
    </span>
  );
}

export function UrgencyBadge({ value }) {
  return <Tag label={value} color={TIER_COLOR[value] || "var(--color-ink-3)"} />;
}

export function SeverityBadge({ value }) {
  return <Tag label={value.toUpperCase()} color={TIER_COLOR[value] || "var(--color-ink-3)"} />;
}

export function HealthBadge({ value }) {
  return <Tag label={value} color={HEALTH_COLOR[value] || "var(--color-ink-3)"} mono={false} />;
}

export function Pill({ children, className = "" }) {
  return (
    <span className={`font-mono-tight inline-flex items-center rounded border border-border bg-surface px-2 py-1 text-[11px] text-ink-2 ${className}`}>
      {children}
    </span>
  );
}
