import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { ApiErrorBanner } from "@/components/ApiErrorBanner";
import { StatCard } from "@/components/StatCard";
import { fetchExperiments, fetchHealth, getApiBaseUrl } from "@/lib/api";
import {
  formatDuration,
  formatParams,
  formatTimestamp,
  formatValBpb,
} from "@/lib/format";
import type { ExperimentSummary } from "@/lib/types";

export const dynamic = "force-dynamic";

function summarize(items: ExperimentSummary[]) {
  const withBpb = items.filter((e) => e.val_bpb != null) as Array<
    ExperimentSummary & { val_bpb: number }
  >;
  const best =
    withBpb.length === 0
      ? null
      : withBpb.reduce((a, b) => (a.val_bpb <= b.val_bpb ? a : b));
  const latest =
    items.length === 0
      ? null
      : items.reduce((a, b) =>
          new Date(a.created_at) >= new Date(b.created_at) ? a : b
        );
  const ok = items.filter((e) => e.status === "ok").length;
  const rejected = items.filter(
    (e) => e.status === "fail" || e.status === "crash"
  ).length;
  const totalTraining = items.reduce(
    (sum, e) => sum + (e.duration_seconds ?? 0),
    0
  );
  return { best, latest, ok, rejected, totalTraining };
}

export default async function OverviewPage() {
  let error: string | null = null;
  let items: ExperimentSummary[] = [];
  let apiOk = false;

  try {
    const health = await fetchHealth();
    apiOk = health.status === "ok";
    const list = await fetchExperiments({ limit: 200 });
    items = list.items;
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  const { best, latest, ok, rejected, totalTraining } = summarize(items);

  return (
    <AppShell current="/">
      <div className="mb-8">
        <h2 className="font-display text-3xl font-semibold tracking-tight">
          Overview
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-mute">
          Live view of registered AutoResearch runs. Primary metric{" "}
          <span className="font-mono text-ink">val_bpb</span> (lower is better).
          API: <span className="font-mono">{getApiBaseUrl()}</span>
          {apiOk ? " · healthy" : ""}
        </p>
      </div>

      {error ? <ApiErrorBanner message={error} /> : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard label="Total experiments" value={String(items.length)} />
        <StatCard
          label="Best val_bpb"
          value={formatValBpb(best?.val_bpb)}
          hint={best ? best.experiment_id : undefined}
        />
        <StatCard
          label="Latest experiment"
          value={latest?.experiment_id ?? "—"}
          hint={latest ? formatTimestamp(latest.created_at) : undefined}
        />
        <StatCard label="Status ok" value={String(ok)} hint="completed runs" />
        <StatCard
          label="Fail / crash"
          value={String(rejected)}
          hint="failed or crashed"
        />
        <StatCard
          label="Total training time"
          value={formatDuration(totalTraining)}
          hint="sum of duration_seconds"
        />
      </div>

      <section className="mt-10 rounded-lg border border-line bg-panel p-5 shadow-sm">
        <h3 className="font-display text-xl font-semibold">Best model</h3>
        {best ? (
          <div className="mt-3 space-y-2 text-sm">
            <p>
              <Link
                href={`/experiments/${encodeURIComponent(best.experiment_id)}`}
                className="font-mono text-accent-ink underline-offset-2 hover:underline"
              >
                {best.experiment_id}
              </Link>
            </p>
            <p className="text-mute">
              val_bpb{" "}
              <span className="font-mono text-ink">
                {formatValBpb(best.val_bpb)}
              </span>
              {" · "}
              params{" "}
              <span className="font-mono text-ink">
                {formatParams(best.num_params)}
              </span>
              {" · "}
              depth{" "}
              <span className="font-mono text-ink">{best.depth ?? "—"}</span>
            </p>
          </div>
        ) : (
          <p className="mt-3 text-sm text-mute">No scored experiments yet.</p>
        )}
      </section>
    </AppShell>
  );
}
