import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoResearch Experiment Platform",
  description: "Track AutoResearch experiments, val_bpb, and checkpoints.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
