import { COLUMN_DEFINITIONS } from "../config/columns";

const SKELETON_ROWS = 8;

export function TableSkeleton() {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm" aria-busy="true" aria-label="Loading databases">
      <table className="w-full text-left" role="presentation">
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
          {Array.from({ length: SKELETON_ROWS }).map((_, i) => (
            <tr key={i} className="animate-pulse">
              {COLUMN_DEFINITIONS.map((col) => (
                <td key={col.key} className="px-4 py-3">
                  <div className="h-4 bg-gray-200 rounded w-3/4" />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
