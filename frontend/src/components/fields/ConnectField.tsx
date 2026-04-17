import { ExternalLink } from "lucide-react";
import { useDbTypes } from "../../hooks/useDbTypes";
import type { ArgoAppInfo } from "../../types/database";
import type { FieldRendererProps } from "./types";

function applyTemplate(template: string, vars: Record<string, string>): string {
  return template.replace(/\{(\w+)\}/g, (_, key) => vars[key] ?? "");
}

export function ConnectField({ record, value }: FieldRendererProps) {
  const { data: dbTypes } = useDbTypes();
  const apps = value as ArgoAppInfo[] | undefined;

  if (!dbTypes || !apps || apps.length === 0) return null;

  const descriptor = dbTypes.find((t) => t.canonical_name === record.db_type);
  const template = descriptor?.console_url_template ?? "";

  if (!template) return null;

  const vars: Record<string, string> = {
    db_name: record.db_name,
    group: record.group,
    db_type: record.db_type,
  };

  const usesCluster = template.includes("{cluster}");

  if (usesCluster) {
    return (
      <div className="flex flex-col gap-1">
        {apps.map((app) => (
          <a
            key={app.cluster}
            href={applyTemplate(template, { ...vars, cluster: app.cluster })}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-800 hover:underline"
          >
            {app.cluster}
            <ExternalLink className="w-3 h-3" aria-hidden="true" />
          </a>
        ))}
      </div>
    );
  }

  const url = applyTemplate(template, vars);
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-800 hover:underline"
    >
      Connect
      <ExternalLink className="w-3 h-3" aria-hidden="true" />
    </a>
  );
}
