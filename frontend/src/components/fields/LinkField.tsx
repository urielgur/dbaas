import { ExternalLink } from "lucide-react";
import type { FieldRendererProps } from "./types";

export function LinkField({ value, columnDef }: FieldRendererProps) {
  const href = typeof value === "string" ? value : null;
  const label = (columnDef.rendererProps?.label as string) ?? "Link";

  if (!href) return <span className="text-gray-400">—</span>;

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 hover:underline"
    >
      {label}
      <ExternalLink className="w-3 h-3" />
    </a>
  );
}
