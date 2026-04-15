import { COLUMN_DEFINITIONS } from "../../config/columns";
import type { DatabaseRecord } from "../../types/database";
import { DatabaseRow } from "./DatabaseRow";

interface DatabaseTableProps {
  records: DatabaseRecord[];
}

export function DatabaseTable({ records }: DatabaseTableProps) {
  if (records.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400">
        <p className="text-lg">No databases found.</p>
        <p className="text-sm mt-1">Trigger a scan or adjust your filters.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="w-full text-left">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            {COLUMN_DEFINITIONS.map((col) => (
              <th
                key={col.key}
                className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap"
              >
                {col.label}
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
