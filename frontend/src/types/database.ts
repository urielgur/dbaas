export interface SyncStats {
  synced: number;
  out_of_sync: number;
  unknown: number;
  out_of_sync_resources: string[];
}

export interface ArgoAppInfo {
  cluster: string;
  argocd_url: string;
  app_name: string;
  app_url: string;
  sync_status: "Synced" | "OutOfSync" | "Unknown";
  health_status: string;
  sync_stats: SyncStats;
}

export interface DatabaseRecord {
  id: string;
  db_type: string;
  db_name: string;
  group: string;
  gitlab_project_id: number;
  gitlab_project_url: string;
  gitlab_namespace: string;
  chart_version: string;
  chart_name: string;
  argocd_apps: ArgoAppInfo[];
  extra_fields: Record<string, unknown>;
  notes: string;
  last_scanned_at: string;
}

export interface DBTypeDescriptor {
  canonical_name: string;
  display_label: string;
  icon_name: string;
  console_url_template: string;
  helm_chart_url: string;
  helm_chart_version: string;
}

export type ScanStatus = "ok" | "running" | "error" | "never";

export interface ScanStatusResponse {
  status: ScanStatus;
  last_scan_at: string | null;
  error_message: string | null;
}

export interface ListResponse {
  items: DatabaseRecord[];
  total: number;
  last_scanned_at: string | null;
}
