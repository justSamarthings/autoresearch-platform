import Link from "next/link";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { ApiErrorBanner } from "@/components/ApiErrorBanner";
import { fetchExperiment } from "@/lib/api";
import {
  formatDuration,
  formatParams,
  formatTimestamp,
  formatValBpb,
  shortCommit,
} from "@/lib/format";
import type { ExperimentDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[140px_1fr] gap-3 border-b border-line/70 py-2 text-sm last:border-0">
      <dt className="font-mono text-[11px] uppercase tracking-[0.12em] text-mute">
        {label}
      </dt>
      <dd className="min-w-0 break-words">{children}</dd>
    </div>
  );
}

export default async function ExperimentDetailPage({
  params,
}: {
  params: Promise<{ experimentId: string }>;
}) {
  const { experimentId } = await params;
  let error: string | null = null;
  let exp: ExperimentDetail | null = null;

  try {
    exp = await fetchExperiment(experimentId);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    if (msg.includes("404")) {
      notFound();
    }
    error = msg;
  }

  return (
    <AppShell current="/experiments">
      <div className="mb-6">
        <Link
          href="/experiments"
          className="text-sm text-mute hover:text-ink"
        >
          ← Experiments
        </Link>
        <h2 className="mt-3 font-display text-3xl font-semibold tracking-tight">
          {experimentId}
        </h2>
        {exp ? (
          <p className="mt-2 font-mono text-sm text-mute">
            val_bpb {formatValBpb(exp.val_bpb)} · {exp.status}
          </p>
        ) : null}
      </div>

      {error ? <ApiErrorBanner message={error} /> : null}

      {exp ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-lg border border-line bg-panel p-5 shadow-sm">
            <h3 className="font-display text-lg font-semibold">Metadata</h3>
            <dl className="mt-3">
              <Row label="Status">{exp.status}</Row>
              <Row label="val_bpb">
                <span className="font-mono">{formatValBpb(exp.val_bpb)}</span>
              </Row>
              <Row label="Duration">
                {formatDuration(exp.duration_seconds)}
              </Row>
              <Row label="Git">
                <span className="font-mono">
                  {shortCommit(exp.git_commit)}
                  {exp.git_dirty ? " (dirty)" : ""}
                </span>
              </Row>
              <Row label="Parent">
                {exp.parent_experiment_id ? (
                  <Link
                    href={`/experiments/${encodeURIComponent(exp.parent_experiment_id)}`}
                    className="font-mono text-accent-ink hover:underline"
                  >
                    {exp.parent_experiment_id}
                  </Link>
                ) : (
                  "—"
                )}
              </Row>
              <Row label="Params">
                <span className="font-mono">
                  {formatParams(exp.num_params)}
                </span>
              </Row>
              <Row label="Architecture">
                <span className="font-mono text-xs">
                  depth={exp.depth ?? "—"} seq={exp.max_seq_len ?? "—"} vocab=
                  {exp.vocab_size ?? "—"} window={exp.window_pattern ?? "—"}
                </span>
              </Row>
              <Row label="Started">{formatTimestamp(exp.started_at)}</Row>
              <Row label="Completed">
                {formatTimestamp(exp.completed_at)}
              </Row>
              <Row label="Created">{formatTimestamp(exp.created_at)}</Row>
              {exp.crash_message ? (
                <Row label="Crash">
                  <span className="text-danger">{exp.crash_message}</span>
                </Row>
              ) : null}
            </dl>
          </section>

          <section className="rounded-lg border border-line bg-panel p-5 shadow-sm">
            <h3 className="font-display text-lg font-semibold">Checkpoint</h3>
            {exp.checkpoints.length === 0 ? (
              <p className="mt-3 text-sm text-mute">No checkpoint metadata.</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {exp.checkpoints.map((c) => (
                  <li key={c.id} className="text-sm">
                    <p className="font-mono text-xs break-all">
                      {c.checkpoint_path}
                    </p>
                    <p className="mt-1 text-mute">
                      {formatTimestamp(c.created_at)}
                    </p>
                    {c.metadata ? (
                      <pre className="mt-2 overflow-x-auto rounded bg-wash p-3 font-mono text-[11px] text-mute">
                        {JSON.stringify(c.metadata, null, 2)}
                      </pre>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
            {exp.checkpoint_path && exp.checkpoints.length === 0 ? (
              <p className="mt-2 font-mono text-xs break-all text-mute">
                {exp.checkpoint_path}
              </p>
            ) : null}
          </section>

          <section className="rounded-lg border border-line bg-panel p-5 shadow-sm lg:col-span-2">
            <h3 className="font-display text-lg font-semibold">Metrics</h3>
            {exp.metrics.length === 0 ? (
              <p className="mt-3 text-sm text-mute">No metrics stored.</p>
            ) : (
              <div className="mt-3 overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="border-b border-line font-mono text-[11px] uppercase tracking-[0.12em] text-mute">
                    <tr>
                      <th className="py-2 pr-4 font-medium">Name</th>
                      <th className="py-2 pr-4 font-medium">Value</th>
                      <th className="py-2 pr-4 font-medium">Step</th>
                      <th className="py-2 font-medium">Recorded</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exp.metrics.map((m) => (
                      <tr key={m.id} className="border-b border-line/60">
                        <td className="py-2 pr-4 font-mono text-xs">
                          {m.metric_name}
                        </td>
                        <td className="py-2 pr-4 font-mono tabular-nums">
                          {m.metric_value}
                        </td>
                        <td className="py-2 pr-4 font-mono text-mute">
                          {m.step ?? "—"}
                        </td>
                        <td className="py-2 text-mute">
                          {formatTimestamp(m.recorded_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="rounded-lg border border-line bg-panel p-5 shadow-sm lg:col-span-2">
            <h3 className="font-display text-lg font-semibold">Configuration</h3>
            {exp.configuration ? (
              <pre className="mt-3 overflow-x-auto rounded bg-wash p-4 font-mono text-[11px] leading-relaxed text-mute">
                {JSON.stringify(exp.configuration, null, 2)}
              </pre>
            ) : (
              <p className="mt-3 text-sm text-mute">No configuration JSON.</p>
            )}
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}
