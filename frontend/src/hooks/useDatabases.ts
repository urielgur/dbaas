import { useQuery } from "@tanstack/react-query";
import { listDatabases, type DatabaseFilters } from "../api/databases";
import type { ListResponse } from "../types/database";

export function useDatabases(filters?: DatabaseFilters) {
  return useQuery<ListResponse>({
    queryKey: ["databases", filters],
    queryFn: () => listDatabases(filters),
    staleTime: 30_000,
  });
}
