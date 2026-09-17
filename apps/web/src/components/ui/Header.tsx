export function Header() {
  return (
    <header className="mb-12 border-b border-slate-800 pb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white">Recourse</h1>
          <p className="mt-2 text-sm text-slate-400">
            Detect. Investigate. Approve. Remediate. Verify.
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs font-mono text-slate-500">AWS Operations Intelligence</p>
          <p className="text-xs font-mono text-indigo-400 mt-1">
            AI investigates. Policy constrains.<br /> Humans authorize. AWS executes.
          </p>
        </div>
      </div>
    </header>
  );
}
