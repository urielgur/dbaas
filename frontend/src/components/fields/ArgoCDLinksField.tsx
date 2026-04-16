import { ExternalLink } from "lucide-react";
import type { ArgoAppInfo } from "../../types/database";
import type { FieldRendererProps } from "./types";

function AppRow({ app }: { app: ArgoAppInfo }) {
  const { synced, out_of_sync } = app.sync_stats;

  return (
    <div className="flex items-center gap-2">
      <a
        href={app.app_url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-800 hover:underline shrink-0"
      >
        {app.cluster}
        <ExternalLink className="w-3 h-3" aria-hidden="true" />
      </a>
      {synced > 0 && (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
          {synced}
        </span>
      )}
      {out_of_sync > 0 && (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
          {out_of_sync}
        </span>
      )}
    </div>
  );
}

export function ArgoCDLinksField({ value }: FieldRendererProps) {
  const apps = value as ArgoAppInfo[] | undefined;

  if (!apps || apps.length === 0) {
    return <span className="text-gray-400 text-sm">—</span>;
  }

  return (
    <div className="flex flex-col gap-1.5">
      {apps.map((app) => (
        <AppRow key={`${app.cluster}-${app.app_name}`} app={app} />
      ))}
    </div>
  );
}
