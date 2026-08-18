import Link from "next/link";
import type { ExperimentSummary } from "@/lib/types";
import {
  formatDuration,
  formatTimestamp,
  formatValBpb,
  shortCommit,
} from "@/lib/format";

function StatusPill({ status }: { status: string }) {
  const tone =
    status === "ok"
      ? "bg-accent/15 text-accent-ink"
      : status === "crash" || status === "fail"
        ? "bg-danger/15 text-danger"
        : "bg-line text-mute";
  return (
    <span
      className={`inline-flex rounded px-2 py-0.5 font-mono text-[11px] uppercase tracking-wide ${tone}`}
    >
      {status}
    </span>
  );
}

export function ExperimentsTable({ items }: { items: ExperimentSummary[] }) {
  if (items.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-line bg-panel px-4 py-10 text-center text-sm text-mute">
        No experiments registered yet. Train on Colab, then register the result
        JSON with the API.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-line bg-panel shadow-sm">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b border-line bg-wash font-mono text-[11px] uppercase tracking-[0.12em] text-mute">
          <tr>
            <th className="px-4 py-3 font-medium">Experiment</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">val_bpb</th>
            <th className="px-4 py-3 font-medium">Duration</th>
            <th className="px-4 py-3 font-medium">Commit</th>
            <th className="px-4 py-3 font-medium">Created</th>
            <th className="px-4 py-3 font-medium">Config</th>
          </tr>
        </thead>
        <tbody>
          {items.map((exp) => (
            <tr
              key={exp.id}
              className="border-b border-line/70 last:border-0 hover:bg-wash/80"
            >
              <td className="px-4 py-3">
                <Link
                  href={`/experiments/${encodeURIComponent(exp.experiment_id)}`}
                  className="font-mono text-sm text-accent-ink underline-offset-2 hover:underline"
                >
                  {exp.experiment_id}
                </Link>
              </td>
              <td className="px-4 py-3">
                <StatusPill status={exp.status} />
              </td>
              <td className="px-4 py-3 font-mono tabular-nums">
                {formatValBpb(exp.val_bpb)}
              </td>
              <td className="px-4 py-3 tabular-nums text-mute">
                {formatDuration(exp.duration_seconds)}
              </td>
              <td className="px-4 py-3 font-mono text-mute">
                {shortCommit(exp.git_commit)}
                {exp.git_dirty ? "*" : ""}
              </td>
              <td className="px-4 py-3 text-mute">
                {formatTimestamp(exp.created_at)}
              </td>
              <td className="px-4 py-3 font-mono text-xs text-mute">
                d{exp.depth ?? "—"} / L{exp.max_seq_len ?? "—"} / v
                {exp.vocab_size ?? "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
