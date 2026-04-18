import { useQuery } from "@tanstack/react-query";
import { listClusters } from "../api/databases";

export function useClusters() {
  return useQuery<string[]>({
    queryKey: ["clusters"],
    queryFn: listClusters,
    staleTime: 30_000,
  });
}
