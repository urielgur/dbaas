import { ExternalLink } from "lucide-react";
import { useDbTypes } from "../../hooks/useDbTypes";
import type { FieldRendererProps } from "./types";

export function HelmChartField({ record, value }: FieldRendererProps) {
  const { data: dbTypes } = useDbTypes();
  const version = typeof value === "string" ? value : null;

  if (!version) return <span className="text-gray-400" aria-label="Not available">—</span>;

  const descriptor = dbTypes?.find((t) => t.canonical_name === record.db_type);
  const chartUrl = descriptor?.helm_chart_url;

  if (!chartUrl) {
    return <span className="text-sm text-gray-700">{version}</span>;
  }

  return (
    <a
      href={chartUrl}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`Parent helm chart version ${version} (opens in new tab)`}
      className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-800 hover:underline"
    >
      {version}
      <ExternalLink className="w-3 h-3" aria-hidden="true" />
    </a>
  );
}
