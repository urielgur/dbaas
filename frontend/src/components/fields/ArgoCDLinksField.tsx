import { ExternalLink } from "lucide-react";
import type { ArgoAppInfo } from "../../types/database";
import { SyncBadge } from "./SyncBadge";
import type { FieldRendererProps } from "./types";

export function ArgoCDLinksField({ value }: FieldRendererProps) {
  const apps = value as ArgoAppInfo[] | undefined;

  if (!apps || apps.length === 0) {
    return <span className="text-gray-400 text-sm">No apps</span>;
  }

  return (
    <div className="flex flex-col gap-1.5">
      {apps.map((app) => (
        <div key={`${app.cluster}-${app.app_name}`} className="flex items-center gap-2">
          <a
            href={app.app_url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`ArgoCD app ${app.app_name} on ${app.cluster} (opens in new tab)`}
            className="inline-flex items-center gap-1 text-sm text-brand-600 hover:text-brand-800 hover:underline"
          >
            {app.cluster}
            <ExternalLink className="w-3 h-3" aria-hidden="true" />
          </a>
          <SyncBadge stats={app.sync_stats} syncStatus={app.sync_status} />
        </div>
      ))}
    </div>
  );
}
