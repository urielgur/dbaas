/**
 * COLUMN_DEFINITIONS — the single file to edit when adding a new column.
 *
 * To add a column:
 *   1. Add an entry here with a `renderer` key matching one in FieldRegistry.
 *   2. If a custom renderer is needed, create it in src/components/fields/
 *      and register it in FieldRegistry.ts.
 *   3. If the field doesn't exist on DatabaseRecord yet, add it to:
 *      - backend/app/models/database.py
 *      - src/types/database.ts
 *
 * The `key` must be either a top-level field on DatabaseRecord or a key
 * inside `extra_fields`. DatabaseRow handles both cases automatically.
 */

export interface ColumnDefinition {
  key: string;
  label: string;
  renderer: string;
  rendererProps?: Record<string, unknown>;
  sortable?: boolean;
  filterable?: boolean;
}

export const COLUMN_DEFINITIONS: ColumnDefinition[] = [
  {
    key: "db_type",
    label: "Type",
    renderer: "dbType",
    sortable: true,
    filterable: true,
  },
  {
    key: "db_name",
    label: "Name",
    renderer: "text",
    sortable: true,
  },
  {
    key: "group",
    label: "Group",
    renderer: "text",
    sortable: true,
    filterable: true,
  },
  {
    key: "gitlab_project_url",
    label: "GitLab",
    renderer: "link",
    rendererProps: { label: "Project" },
  },
  {
    key: "argocd_apps",
    label: "ArgoCD",
    renderer: "argoCDLinks",
  },
  {
    key: "chart_version",
    label: "Chart Version",
    renderer: "text",
    sortable: true,
  },
  {
    key: "argocd_apps",
    label: "Connect",
    renderer: "connect",
  },
  {
    key: "notes",
    label: "Notes",
    renderer: "notes",
  },
];
