export function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/50 p-6 shadow-sm">
      <h2 className="mb-4 text-sm font-semibold tracking-wide text-slate-300 uppercase">
        {title}
      </h2>
      <div className="space-y-4">
        {children}
      </div>
    </section>
  );
}
