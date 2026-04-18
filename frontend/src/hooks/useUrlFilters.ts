import { useCallback, useState } from "react";

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100, 1000] as const;
const DEFAULT_PAGE_SIZE = 25;

export { PAGE_SIZE_OPTIONS, DEFAULT_PAGE_SIZE };

export interface UrlFilters {
  q: string;
  db_type: string;
  group: string;
  cluster: string;
  page: number;
  page_size: number;
  sort_by: string;
  sort_dir: "asc" | "desc";
}

function readFromUrl(): UrlFilters {
  const p = new URLSearchParams(window.location.search);
  const rawSize = parseInt(p.get("page_size") ?? String(DEFAULT_PAGE_SIZE), 10);
  const page_size = (PAGE_SIZE_OPTIONS as readonly number[]).includes(rawSize)
    ? rawSize
    : DEFAULT_PAGE_SIZE;
  return {
    q: p.get("q") ?? "",
    db_type: p.get("db_type") ?? "",
    group: p.get("group") ?? "",
    cluster: p.get("cluster") ?? "",
    page: Math.max(1, parseInt(p.get("page") ?? "1", 10)),
    page_size,
    sort_by: p.get("sort_by") ?? "",
    sort_dir: p.get("sort_dir") === "desc" ? "desc" : "asc",
  };
}

function writeToUrl(filters: UrlFilters) {
  const p = new URLSearchParams();
  if (filters.q) p.set("q", filters.q);
  if (filters.db_type) p.set("db_type", filters.db_type);
  if (filters.group) p.set("group", filters.group);
  if (filters.cluster) p.set("cluster", filters.cluster);
  if (filters.page > 1) p.set("page", String(filters.page));
  if (filters.page_size !== DEFAULT_PAGE_SIZE) p.set("page_size", String(filters.page_size));
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
