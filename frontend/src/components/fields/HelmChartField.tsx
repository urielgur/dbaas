import { ExternalLink } from "lucide-react";
import type { FieldRendererProps } from "./types";

export function HelmChartField({ record, value }: FieldRendererProps) {
  const version = typeof value === "string" ? value : null;

  if (!version) return <span className="text-gray-400" aria-label="Not available">—</span>;

  if (!record.gitlab_project_url) {
    return <span className="text-sm text-gray-700">{version}</span>;
  }

  return (
    <a
      href={record.gitlab_project_url}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`GitLab project for version ${version} (opens in new tab)`}
      className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-800 hover:underline"
    >
      {version}
      <ExternalLink className="w-3 h-3" aria-hidden="true" />
    </a>
  );
}
