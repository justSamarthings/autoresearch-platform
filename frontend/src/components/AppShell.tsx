import Link from "next/link";

const nav = [
  { href: "/", label: "Overview" },
  { href: "/experiments", label: "Experiments" },
];

export function AppShell({
  children,
  current,
}: {
  children: React.ReactNode;
  current?: string;
}) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-panel/80 backdrop-blur-sm sticky top-0 z-20">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-5 py-4">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-mute">
              AutoResearch
            </p>
            <h1 className="font-display text-lg font-semibold tracking-tight text-ink">
              Experiment Platform
            </h1>
          </div>
          <nav className="flex items-center gap-1">
            {nav.map((item) => {
              const active =
                current === item.href ||
                (item.href !== "/" && current?.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-md px-3 py-1.5 text-sm transition ${
                    active
                      ? "bg-ink text-paper"
                      : "text-mute hover:bg-line/60 hover:text-ink"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-5 py-8">{children}</main>
    </div>
  );
}
