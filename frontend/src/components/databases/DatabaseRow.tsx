import { getRenderer } from "../fields/FieldRegistry";
import type { ColumnDefinition } from "../../config/columns";
import type { DatabaseRecord } from "../../types/database";

interface DatabaseRowProps {
  record: DatabaseRecord;
  columns: ColumnDefinition[];
}

function extractValue(record: DatabaseRecord, key: string): unknown {
  if (key in record) {
    return record[key as keyof DatabaseRecord];
  }
  return record.extra_fields[key];
}

export function DatabaseRow({ record, columns }: DatabaseRowProps) {
  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
      {columns.map((col) => {
        const Renderer = getRenderer(col.renderer);
        const value = extractValue(record, col.key);
        return (
          <td key={col.key} className={`px-4 py-3 align-top${col.className ? ` ${col.className}` : ""}`}>
            <Renderer record={record} columnDef={col} value={value} />
          </td>
        );
      })}
    </tr>
  );
}
