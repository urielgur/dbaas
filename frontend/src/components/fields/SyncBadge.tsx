import type { SyncStats } from "../../types/database";

interface SyncBadgeProps {
  stats: SyncStats;
  syncStatus: string;
}

export function SyncBadge({ stats, syncStatus }: SyncBadgeProps) {
  const isOutOfSync = syncStatus === "OutOfSync";

  return (
    <span className="inline-flex items-center gap-1 text-xs" aria-label={`Sync status: ${syncStatus}`}>
      {stats.synced > 0 && (
        <span className="inline-flex items-center px-2 py-badge rounded bg-green-100 text-green-700 font-medium">
          {stats.synced} synced
        </span>
      )}
      {stats.out_of_sync > 0 && (
        <span className="inline-flex items-center px-2 py-badge rounded bg-red-100 text-red-700 font-medium">
          {stats.out_of_sync} out-of-sync
        </span>
      )}
      {stats.synced === 0 && stats.out_of_sync === 0 && (
        <span
          className={`inline-flex items-center px-2 py-badge rounded font-medium ${
            isOutOfSync
              ? "bg-yellow-100 text-yellow-700"
              : "bg-gray-100 text-gray-500"
          }`}
        >
          {syncStatus}
        </span>
      )}
    </span>
  );
}
