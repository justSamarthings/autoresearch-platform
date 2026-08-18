import Link from "next/link";
import { AppShell } from "@/components/AppShell";

export default function NotFound() {
  return (
    <AppShell current="/experiments">
      <h2 className="font-display text-3xl font-semibold">Not found</h2>
      <p className="mt-2 text-sm text-mute">
        That experiment id is not in the database.
      </p>
      <Link
        href="/experiments"
        className="mt-6 inline-block text-sm text-accent-ink hover:underline"
      >
        Back to experiments
      </Link>
    </AppShell>
  );
}
