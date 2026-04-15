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
        className={`inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors
          ${
            busy
              ? "bg-gray-100 text-gray-400 cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800"
          }`}
      >
        <RefreshCw className={`w-4 h-4 ${busy ? "animate-spin" : ""}`} />
        {isRunning ? "Scanning…" : "Scan Now"}
      </button>

      {status && (
        <span className="text-xs text-gray-400">
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
