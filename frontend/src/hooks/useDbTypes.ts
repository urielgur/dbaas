import { useQuery } from "@tanstack/react-query";
import { listDbTypes } from "../api/databases";
import type { DBTypeDescriptor } from "../types/database";

export function useDbTypes() {
  return useQuery<DBTypeDescriptor[]>({
    queryKey: ["db-types"],
    queryFn: listDbTypes,
    staleTime: Infinity,
  });
}
