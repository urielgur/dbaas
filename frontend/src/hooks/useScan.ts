import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getScanStatus, triggerScan } from "../api/databases";
import type { ScanStatusResponse } from "../types/database";

export function useScan() {
  const queryClient = useQueryClient();

  const statusQuery = useQuery<ScanStatusResponse>({
    queryKey: ["scan-status"],
    queryFn: getScanStatus,
    refetchInterval: (query) =>
      query.state.data?.status === "running" ? 3000 : false,
  });

  const mutation = useMutation({
    mutationFn: triggerScan,
    onSuccess: () => {
      // Start polling for status
      queryClient.invalidateQueries({ queryKey: ["scan-status"] });
    },
  });

  // When scan completes (transitions from running → ok/error), refresh the DB list
  const previousStatus = statusQuery.data?.status;
  if (previousStatus === "ok" || previousStatus === "error") {
    queryClient.invalidateQueries({ queryKey: ["databases"] });
  }

  return {
    trigger: mutation.mutate,
    isPending: mutation.isPending,
    status: statusQuery.data,
    isRunning: statusQuery.data?.status === "running",
  };
}
