import { AppShell } from "@/components/AppShell";
import { ApiErrorBanner } from "@/components/ApiErrorBanner";
import { ExperimentsTable } from "@/components/ExperimentsTable";
import { fetchExperiments } from "@/lib/api";
import type { ExperimentSummary } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function ExperimentsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const params = await searchParams;
  const status = params.status || undefined;

  let error: string | null = null;
  let items: ExperimentSummary[] = [];
  let total = 0;

  try {
    const list = await fetchExperiments({ limit: 200, status });
    items = list.items;
    total = list.total;
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <AppShell current="/experiments">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-3xl font-semibold tracking-tight">
            Experiments
          </h2>
          <p className="mt-2 text-sm text-mute">
            {error ? "—" : `${total} registered`} · click a row id for detail
          </p>
        </div>
        <div className="flex gap-2 font-mono text-xs">
          {[
            { label: "all", href: "/experiments" },
            { label: "ok", href: "/experiments?status=ok" },
            { label: "fail", href: "/experiments?status=fail" },
            { label: "crash", href: "/experiments?status=crash" },
          ].map((f) => {
            const active =
              (!status && f.label === "all") || status === f.label;
            return (
              <a
                key={f.label}
                href={f.href}
                className={`rounded-md border px-2.5 py-1 ${
                  active
                    ? "border-ink bg-ink text-paper"
                    : "border-line bg-panel text-mute hover:text-ink"
                }`}
              >
                {f.label}
              </a>
            );
          })}
        </div>
      </div>

      {error ? <ApiErrorBanner message={error} /> : null}
      <ExperimentsTable items={items} />
    </AppShell>
  );
}
