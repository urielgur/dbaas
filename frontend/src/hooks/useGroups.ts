import { useQuery } from "@tanstack/react-query";
import { listGroups } from "../api/databases";

export function useGroups() {
  return useQuery<string[]>({
    queryKey: ["groups"],
    queryFn: listGroups,
    staleTime: 30_000,
  });
}
