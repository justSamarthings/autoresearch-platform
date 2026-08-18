export function ApiErrorBanner({ message }: { message: string }) {
  return (
    <div className="mb-6 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
      <p className="font-medium">Could not reach the API</p>
      <p className="mt-1 font-mono text-xs opacity-90">{message}</p>
      <p className="mt-2 text-xs text-mute">
        Start FastAPI on the URL in{" "}
        <span className="font-mono">NEXT_PUBLIC_API_URL</span> (default{" "}
        <span className="font-mono">http://127.0.0.1:8000</span>).
      </p>
    </div>
  );
}
