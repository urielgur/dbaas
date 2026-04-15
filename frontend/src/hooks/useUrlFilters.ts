import { useCallback, useState } from "react";

export interface UrlFilters {
  q: string;
  db_type: string;
  page: number;
  sort_by: string;
  sort_dir: "asc" | "desc";
}

function readFromUrl(): UrlFilters {
  const p = new URLSearchParams(window.location.search);
  return {
    q: p.get("q") ?? "",
    db_type: p.get("db_type") ?? "",
    page: Math.max(1, parseInt(p.get("page") ?? "1", 10)),
    sort_by: p.get("sort_by") ?? "",
    sort_dir: p.get("sort_dir") === "desc" ? "desc" : "asc",
  };
}

function writeToUrl(filters: UrlFilters) {
  const p = new URLSearchParams();
  if (filters.q) p.set("q", filters.q);
  if (filters.db_type) p.set("db_type", filters.db_type);
  if (filters.page > 1) p.set("page", String(filters.page));
  if (filters.sort_by) p.set("sort_by", filters.sort_by);
  if (filters.sort_dir !== "asc") p.set("sort_dir", filters.sort_dir);
  const qs = p.toString();
  window.history.replaceState(null, "", `${window.location.pathname}${qs ? `?${qs}` : ""}`);
}

export function useUrlFilters() {
  const [filters, setFiltersState] = useState<UrlFilters>(readFromUrl);

  const setFilters = useCallback((updates: Partial<UrlFilters>) => {
    setFiltersState((prev) => {
      const next = { ...prev, ...updates };
      writeToUrl(next);
      return next;
    });
  }, []);

  return { filters, setFilters };
}
