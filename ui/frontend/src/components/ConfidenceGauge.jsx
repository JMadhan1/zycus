const SEGMENTS = 10;

export function ConfidenceGauge({ value }) {
  const pct = Math.round(value * 100);
  const filled = Math.round(value * SEGMENTS);

  return (
    <div className="shrink-0 text-right">
      <div className="font-mono-tight text-lg font-medium text-ink-0">{pct}<span className="text-ink-3">%</span></div>
      <div className="mt-1.5 flex gap-[3px]">
        {Array.from({ length: SEGMENTS }).map((_, i) => (
          <span
            key={i}
            className="h-3 w-[3px] rounded-full"
            style={{
              background: i < filled ? "var(--color-radar)" : "var(--color-border-hover)",
            }}
          />
        ))}
      </div>
      <p className="mt-1 text-[10px] uppercase tracking-wider text-ink-3">signal strength</p>
    </div>
  );
}
