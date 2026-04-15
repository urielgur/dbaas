import { RefreshCw } from "lucide-react";
import { useScan } from "../../hooks/useScan";

export function ScanButton() {
  const { trigger, isPending, isRunning, status } = useScan();
  const busy = isPending || isRunning;

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={() => trigger()}
        disabled={busy}
        aria-label={busy ? "Scan in progress" : "Trigger database scan"}
        aria-busy={busy}
        className={`inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2
          ${
            busy
              ? "bg-gray-100 text-gray-400 cursor-not-allowed"
              : "bg-brand-600 text-white hover:bg-brand-700 active:bg-brand-800"
          }`}
      >
        <RefreshCw className={`w-4 h-4 ${busy ? "animate-spin" : ""}`} aria-hidden="true" />
        {isRunning ? "Scanning…" : "Scan Now"}
      </button>

      {status && (
        <span className="text-xs text-gray-400" aria-live="polite">
          {status.status === "error" && (
            <span className="text-red-500">Error: {status.error_message}</span>
          )}
          {status.last_scan_at && status.status !== "error" && (
            <>Last scan: {new Date(status.last_scan_at).toLocaleString()}</>
          )}
          {status.status === "never" && "Never scanned"}
        </span>
      )}
    </div>
  );
}
