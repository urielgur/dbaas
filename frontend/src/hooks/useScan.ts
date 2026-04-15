import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { getScanStatus, triggerScan } from "../api/databases";
import type { ScanStatus, ScanStatusResponse } from "../types/database";

export function useScan() {
  const queryClient = useQueryClient();
  const prevStatusRef = useRef<ScanStatus | undefined>(undefined);

  const statusQuery = useQuery<ScanStatusResponse>({
    queryKey: ["scan-status"],
    queryFn: getScanStatus,
    refetchInterval: (query) =>
      query.state.data?.status === "running" ? 3000 : false,
  });

  const currentStatus = statusQuery.data?.status;

  // Detect running→ok/error transition to refresh DB list and fire a toast
  useEffect(() => {
    const prev = prevStatusRef.current;
    if (prev === "running") {
      if (currentStatus === "ok") {
        queryClient.invalidateQueries({ queryKey: ["databases"] });
        toast.success("Scan complete — database list refreshed.");
      } else if (currentStatus === "error") {
        queryClient.invalidateQueries({ queryKey: ["databases"] });
        toast.error(`Scan failed: ${statusQuery.data?.error_message ?? "Unknown error"}`);
      }
    }
    prevStatusRef.current = currentStatus;
  }, [currentStatus, queryClient, statusQuery.data?.error_message]);

  const mutation = useMutation({
    mutationFn: triggerScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scan-status"] });
      toast.info("Scan started…");
    },
    onError: () => {
      toast.error("Failed to start scan. Is the backend running?");
    },
  });

  return {
    trigger: mutation.mutate,
    isPending: mutation.isPending,
    status: statusQuery.data,
    isRunning: statusQuery.data?.status === "running",
  };
}
