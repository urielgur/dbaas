import { ExternalLink, Loader2 } from "lucide-react";
import { useState } from "react";
import { getConnectUrls } from "../../api/databases";
import { useDbTypes } from "../../hooks/useDbTypes";
import type { ArgoAppInfo, DatabaseRecord } from "../../types/database";
import type { FieldRendererProps } from "./types";

// TODO: replace with real OpenShift console base URL
const OPENSHIFT_CONSOLE_BASE = "https://console.openshift.example.com/k8s/namespaces";

// Namespace convention: dbaas-{db_type}-{group}-{db_name}
// e.g. dbaas-mongodb-prod-my-db
function openShiftNamespace(record: DatabaseRecord): string {
  return `dbaas-${record.db_type}-${record.group}-${record.db_name}`;
}

function openShiftUrl(record: DatabaseRecord): string {
  return `${OPENSHIFT_CONSOLE_BASE}/${openShiftNamespace(record)}`;
}

// ── Connect action ────────────────────────────────────────────────────────────

const CREDENTIAL_PLACEHOLDERS = ["{username}", "{password}", "{host}", "{port}"];

function needsSecret(template: string): boolean {
  return CREDENTIAL_PLACEHOLDERS.some((p) => template.includes(p));
}

function applyTemplate(template: string, vars: Record<string, string>): string {
  return template.replace(/\{(\w+)\}/g, (_, key) => vars[key] ?? "");
}

function ConnectAction({
  record,
  app,
  template,
}: {
  record: DatabaseRecord;
  app: ArgoAppInfo;
  template: string;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const linkCls =
    "inline-flex items-center gap-1 text-xs text-gray-500 hover:text-brand-600 transition-colors";

  if (needsSecret(template)) {
    async function handleClick() {
      setLoading(true);
      setError(null);
      try {
        const results = await getConnectUrls(record.id, app.cluster);
        for (const { url } of results) {
          window.open(url, "_blank", "noopener,noreferrer");
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed");
      } finally {
        setLoading(false);
      }
    }

    return (
      <span className="flex flex-col">
        <button onClick={handleClick} disabled={loading} className={linkCls}>
          {loading ? (
            <Loader2 className="w-3 h-3 animate-spin" aria-hidden="true" />
          ) : (
            <ExternalLink className="w-3 h-3" aria-hidden="true" />
          )}
          Connect
        </button>
        {error && <span className="text-xs text-red-500">{error}</span>}
      </span>
    );
  }

  const href = applyTemplate(template, {
    db_name: record.db_name,
    group: record.group,
    db_type: record.db_type,
    cluster: app.cluster,
  });

  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={linkCls}>
      <ExternalLink className="w-3 h-3" aria-hidden="true" />
      Connect
    </a>
  );
}

// ── Per-cluster row ───────────────────────────────────────────────────────────

function ClusterRow({
  app,
  record,
  connectTemplate,
}: {
  app: ArgoAppInfo;
  record: DatabaseRecord;
  connectTemplate: string | null;
}) {
  const { synced, out_of_sync, out_of_sync_resources } = app.sync_stats;

  return (
    <div className="flex flex-col gap-0.5">
      {/* Row 1: cluster name + sync badges */}
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
        {synced > 0 && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">
            {synced}
          </span>
        )}
        {out_of_sync > 0 && (
          <span className="relative group/oos inline-flex items-center">
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700 cursor-help">
              {out_of_sync}
            </span>
            {out_of_sync_resources.length > 0 && (
              <span className="absolute bottom-full left-0 mb-1.5 hidden group-hover/oos:flex flex-col gap-0.5 bg-gray-900 text-white text-xs rounded-md px-3 py-2 shadow-lg z-50 min-w-max">
                <span className="font-semibold mb-0.5 text-gray-300">Out of sync</span>
                {out_of_sync_resources.map((r) => (
                  <span key={r} className="font-mono">{r}</span>
                ))}
                <span className="absolute top-full left-3 border-4 border-transparent border-t-gray-900" />
              </span>
            )}
          </span>
        )}
      </div>

      {/* Row 2: connect + openshift */}
      <div className="flex items-center gap-3 pl-0.5">
        {connectTemplate && (
          <ConnectAction record={record} app={app} template={connectTemplate} />
        )}
        <a
          href={openShiftUrl(record)}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-brand-600 transition-colors"
        >
          <ExternalLink className="w-3 h-3" aria-hidden="true" />
          OpenShift
        </a>
      </div>
    </div>
  );
}

// ── Main renderer ─────────────────────────────────────────────────────────────

export function ManageField({ record, value }: FieldRendererProps) {
  const apps = value as ArgoAppInfo[] | undefined;
  const { data: dbTypes } = useDbTypes();

  if (!apps || apps.length === 0) {
    return <span className="text-gray-400 text-sm">—</span>;
  }

  const descriptor = dbTypes?.find((t) => t.canonical_name === record.db_type);
  const connectTemplate = descriptor?.console_url_template ?? null;

  return (
    <div className="flex flex-col gap-3">
      {apps.map((app) => (
        <ClusterRow
          key={`${app.cluster}-${app.app_name}`}
          app={app}
          record={record}
          connectTemplate={connectTemplate}
        />
      ))}
    </div>
  );
}
