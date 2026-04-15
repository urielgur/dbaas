import type { ComponentType } from "react";
import type { ColumnDefinition } from "../../config/columns";
import type { DatabaseRecord } from "../../types/database";

export interface FieldRendererProps {
  record: DatabaseRecord;
  columnDef: ColumnDefinition;
  value: unknown;
}

export type FieldRenderer = ComponentType<FieldRendererProps>;
