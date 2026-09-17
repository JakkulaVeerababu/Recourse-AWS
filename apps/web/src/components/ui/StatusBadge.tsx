type Status = 'READY' | 'NOT_DEPLOYED' | 'NOT_CONFIGURED';

interface StatusBadgeProps {
  status: Status;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const styles = {
    READY: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    NOT_DEPLOYED: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    NOT_CONFIGURED: "bg-slate-800/50 text-slate-400 border-slate-700",
  };

  const labels = {
    READY: "READY",
    NOT_DEPLOYED: "NOT DEPLOYED",
    NOT_CONFIGURED: "NOT CONFIGURED",
  };

  return (
    <span
      className={`inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold tracking-wide ${styles[status]}`}
    >
      {labels[status]}
    </span>
  );
}
