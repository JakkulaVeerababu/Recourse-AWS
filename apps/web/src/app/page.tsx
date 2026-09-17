import { AppShell } from "@/components/ui/AppShell";
import { Header } from "@/components/ui/Header";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";

export default function Home() {
  const components = [
    { name: "System Foundation", status: "READY" },
    { name: "Frontend", status: "READY" },
    { name: "AWS Infrastructure", status: "NOT_DEPLOYED" },
    { name: "Detection Pipeline", status: "NOT_CONFIGURED" },
    { name: "Investigation Agent", status: "NOT_CONFIGURED" },
    { name: "Human Approval", status: "NOT_CONFIGURED" },
    { name: "Remediation", status: "NOT_CONFIGURED" },
    { name: "Verification", status: "NOT_CONFIGURED" },
  ];

  return (
    <AppShell>
      <Header />
      
      <main className="grid gap-6 md:grid-cols-2">
        <SectionCard title="Component Status">
          <ul className="divide-y divide-slate-800/50">
            {components.map((comp) => (
              <li key={comp.name} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
                <span className="text-sm font-medium text-slate-300">{comp.name}</span>
                <StatusBadge status={comp.status as 'READY' | 'NOT_DEPLOYED' | 'NOT_CONFIGURED'} />
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard title="Active Incidents">
          <div className="flex h-40 flex-col items-center justify-center rounded-md border border-dashed border-slate-800 bg-slate-900/20 text-slate-500">
            <p className="text-sm">No active incidents</p>
            <p className="text-xs mt-1 text-slate-600">Waiting for detection pipeline...</p>
          </div>
        </SectionCard>
      </main>
    </AppShell>
  );
}
