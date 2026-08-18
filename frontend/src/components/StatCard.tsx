export function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-line bg-panel p-4 shadow-sm">
      <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-mute">
        {label}
      </p>
      <p className="mt-2 font-display text-2xl font-semibold tracking-tight text-ink tabular-nums">
        {value}
      </p>
      {hint ? <p className="mt-1 text-xs text-mute">{hint}</p> : null}
    </div>
  );
}
