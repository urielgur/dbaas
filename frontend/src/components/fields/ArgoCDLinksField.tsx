import { ExternalLink } from "lucide-react";
import type { ArgoAppInfo } from "../../types/database";
import type { FieldRendererProps } from "./types";

const SYNC_STYLES: Record<string, string> = {
  Synced: "bg-green-100 text-green-700",
  OutOfSync: "bg-red-100 text-red-700",
  Unknown: "bg-gray-100 text-gray-500",
};

const HEALTH_STYLES: Record<string, string> = {
  Healthy: "bg-green-100 text-green-700",
  Degraded: "bg-red-100 text-red-700",
  Progressing: "bg-blue-100 text-blue-700",
  Missing: "bg-yellow-100 text-yellow-700",
  Unknown: "bg-gray-100 text-gray-500",
};

function StatusPill({ label, styles }: { label: string; styles: Record<string, string> }) {
  const cls = styles[label] ?? "bg-gray-100 text-gray-500";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}

function AppRow({ app }: { app: ArgoAppInfo }) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <a
        href={app.app_url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-800 hover:underline shrink-0"
      >
        {app.cluster}
        <ExternalLink className="w-3 h-3" aria-hidden="true" />
      </a>
      <StatusPill label={app.sync_status} styles={SYNC_STYLES} />
      <StatusPill label={app.health_status} styles={HEALTH_STYLES} />
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
