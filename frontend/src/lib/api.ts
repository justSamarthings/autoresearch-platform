import type { ExperimentDetail, ExperimentListResponse } from "./types";

export function getApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
    "http://127.0.0.1:8000"
  );
}

async function apiGet<T>(path: string): Promise<T> {
  const url = `${getApiBaseUrl()}${path}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status} ${path}: ${body.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchExperiments(options?: {
  limit?: number;
  offset?: number;
  status?: string;
}): Promise<ExperimentListResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(options?.limit ?? 100));
  params.set("offset", String(options?.offset ?? 0));
  if (options?.status) params.set("status", options.status);
  return apiGet<ExperimentListResponse>(`/api/v1/experiments?${params}`);
}

export async function fetchExperiment(
  experimentId: string
): Promise<ExperimentDetail> {
  return apiGet<ExperimentDetail>(
    `/api/v1/experiments/${encodeURIComponent(experimentId)}`
  );
}

export async function fetchHealth(): Promise<{ status: string }> {
  return apiGet<{ status: string }>("/health");
}
