import { apiClient } from "./client";
import type {
  DBTypeDescriptor,
  DatabaseRecord,
  ListResponse,
  ScanStatusResponse,
} from "../types/database";

export interface DatabaseFilters {
  db_type?: string;
  namespace?: string;
  group?: string;
  q?: string;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
}

export async function listDatabases(filters?: DatabaseFilters): Promise<ListResponse> {
  const { data } = await apiClient.get<ListResponse>("/databases", { params: filters });
  return data;
}

export async function getDatabase(id: string): Promise<DatabaseRecord> {
  const { data } = await apiClient.get<DatabaseRecord>(`/databases/${id}`);
  return data;
}

export async function listDbTypes(): Promise<DBTypeDescriptor[]> {
  const { data } = await apiClient.get<DBTypeDescriptor[]>("/databases/types");
  return data;
}

export async function listGroups(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>("/databases/groups");
  return data;
}

export async function triggerScan(): Promise<void> {
  await apiClient.post("/scan");
}

export async function getScanStatus(): Promise<ScanStatusResponse> {
  const { data } = await apiClient.get<ScanStatusResponse>("/scan/status");
  return data;
}
