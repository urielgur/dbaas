import { ChevronDown, ChevronUp, ChevronsUpDown } from "lucide-react";
import { COLUMN_DEFINITIONS } from "../../config/columns";
import type { DatabaseRecord } from "../../types/database";
import { DatabaseRow } from "./DatabaseRow";

interface DatabaseTableProps {
  records: DatabaseRecord[];
  sortBy: string;
  sortDir: "asc" | "desc";
  onSort: (key: string, dir: "asc" | "desc") => void;
  hasFilters: boolean;
  totalUnfiltered: number;
}

export function DatabaseTable({
  records,
  sortBy,
  sortDir,
  onSort,
  hasFilters,
  totalUnfiltered,
}: DatabaseTableProps) {
  if (records.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400">
        {hasFilters ? (
          <>
            <p className="text-lg">No results match your filters.</p>
            <p className="text-sm mt-1">
              Try broadening your search or clearing the filters.
            </p>
          </>
        ) : totalUnfiltered === 0 ? (
          <>
            <p className="text-lg">No databases found.</p>
            <p className="text-sm mt-1">Trigger a scan to populate the list.</p>
          </>
        ) : (
          <>
            <p className="text-lg">No databases on this page.</p>
            <p className="text-sm mt-1">Go back to a previous page.</p>
          </>
        )}
      </div>
    );
  }

  function handleSort(key: string) {
    if (sortBy === key) {
      onSort(key, sortDir === "asc" ? "desc" : "asc");
    } else {
      onSort(key, "asc");
    }
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="w-full text-left">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            {COLUMN_DEFINITIONS.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={`px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap${col.className ? ` ${col.className}` : ""}`}
              >
                {col.sortable ? (
                  <button
                    onClick={() => handleSort(col.key)}
                    aria-label={`Sort by ${col.label}${sortBy === col.key ? `, currently ${sortDir}ending` : ""}`}
                    className="inline-flex items-center gap-1 hover:text-gray-800 transition-colors focus:outline-none focus:underline"
                  >
                    {col.label}
                    {sortBy === col.key ? (
                      sortDir === "asc" ? (
                        <ChevronUp className="w-3 h-3" aria-hidden="true" />
                      ) : (
                        <ChevronDown className="w-3 h-3" aria-hidden="true" />
                      )
                    ) : (
                      <ChevronsUpDown className="w-3 h-3 opacity-40" aria-hidden="true" />
                    )}
                  </button>
                ) : (
                  col.label
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-100">
          {records.map((record) => (
            <DatabaseRow
              key={record.id}
              record={record}
              columns={COLUMN_DEFINITIONS}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
