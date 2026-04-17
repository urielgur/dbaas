import { ExternalLink, Loader2 } from "lucide-react";
import { useState } from "react";
import { getConnectUrls } from "../../api/databases";
import { useDbTypes } from "../../hooks/useDbTypes";
import type { ArgoAppInfo, DatabaseRecord } from "../../types/database";
import type { FieldRendererProps } from "./types";

const CREDENTIAL_PLACEHOLDERS = ["{username}", "{password}", "{host}", "{port}"];

function applyTemplate(template: string, vars: Record<string, string>): string {
  return template.replace(/\{(\w+)\}/g, (_, key) => vars[key] ?? "");
}

function needsSecret(template: string): boolean {
  return CREDENTIAL_PLACEHOLDERS.some((p) => template.includes(p));
}

// ── Static link (no secret needed) ──────────────────────────────────────────

function StaticConnectLinks({
  apps,
  template,
  record,
}: {
  apps: ArgoAppInfo[];
  template: string;
  record: DatabaseRecord;
}) {
  const baseVars = { db_name: record.db_name, group: record.group, db_type: record.db_type };
  const usesCluster = template.includes("{cluster}");

  if (usesCluster) {
    return (
      <div className="flex flex-col gap-1">
        {apps.map((app) => (
          <a
            key={app.cluster}
            href={applyTemplate(template, { ...baseVars, cluster: app.cluster })}
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

  return (
    <a
      href={applyTemplate(template, baseVars)}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-800 hover:underline"
    >
      Connect
      <ExternalLink className="w-3 h-3" aria-hidden="true" />
    </a>
  );
}

// ── Secret-backed link (fetches creds from OpenShift) ────────────────────────

function SecretConnectButton({
  record,
  clusterName,
}: {
  record: DatabaseRecord;
  clusterName?: string;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setLoading(true);
    setError(null);
    try {
      const results = await getConnectUrls(record.id, clusterName);
      for (const { url } of results) {
        window.open(url, "_blank", "noopener,noreferrer");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to fetch credentials";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-0.5">
      <button
        onClick={handleClick}
        disabled={loading}
        className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-800 hover:underline disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <Loader2 className="w-3 h-3 animate-spin" aria-hidden="true" />
        ) : (
          <ExternalLink className="w-3 h-3" aria-hidden="true" />
        )}
        {clusterName ?? "Connect"}
      </button>
      {error && <span className="text-xs text-red-500">{error}</span>}
    </div>
  );
}

// ── Main renderer ────────────────────────────────────────────────────────────

export function ConnectField({ record, value }: FieldRendererProps) {
  const { data: dbTypes } = useDbTypes();
  const apps = value as ArgoAppInfo[] | undefined;

  if (!dbTypes || !apps || apps.length === 0) return null;

  const descriptor = dbTypes.find((t) => t.canonical_name === record.db_type);
  const template = descriptor?.console_url_template ?? "";

  if (!template) return null;

  if (needsSecret(template)) {
    return (
      <div className="flex flex-col gap-1">
        {apps.map((app) => (
          <SecretConnectButton key={app.cluster} record={record} clusterName={app.cluster} />
        ))}
      </div>
    );
  }

  return <StaticConnectLinks apps={apps} template={template} record={record} />;
}
