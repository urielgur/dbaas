import { Database } from "lucide-react";
import type { FieldRendererProps } from "./types";

// Map canonical db type names to a Tailwind color class for the badge
const TYPE_COLORS: Record<string, string> = {
  elasticsearch: "bg-yellow-100 text-yellow-800",
  mongodb: "bg-green-100 text-green-800",
  postgresql: "bg-blue-100 text-blue-800",
};

export function DBTypeField({ value }: FieldRendererProps) {
  const dbType = typeof value === "string" ? value : "unknown";
  const colorClass = TYPE_COLORS[dbType] ?? "bg-gray-100 text-gray-700";

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold ${colorClass}`}
    >
      <Database className="w-3 h-3" />
      {dbType}
    </span>
  );
}
