export function MetricCard({ label, value, description }: { label: string; value: string | React.ReactNode; description?: string }) {
  return (
    <div className="rounded-md bg-slate-800/40 p-4 border border-slate-800/60">
      <div className="text-xs font-medium text-slate-400 mb-1">{label}</div>
      <div className="text-lg font-semibold text-slate-100">{value}</div>
      {description && <div className="text-xs text-slate-500 mt-1">{description}</div>}
    </div>
  );
}
