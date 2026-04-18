/**
 * Demo page — shows how the app looks with realistic fake data.
 * No real API calls are made. Access at /example.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { DatabaseIcon, Info, RefreshCw } from "lucide-react";
import { DatabaseTable } from "../components/databases/DatabaseTable";
import { ParentChartsSection } from "../components/databases/ParentChartsSection";
import { Pagination } from "../components/Pagination";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { EXAMPLE_DATABASES, EXAMPLE_DB_TYPES } from "../data/example-data";
import type { DatabaseRecord } from "../types/database";

const PAGE_SIZE_OPTIONS = [10, 25, 50];

// A QueryClient pre-seeded with fake db-types so ParentChartsSection renders.
function makeExampleQueryClient() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
  });
  qc.setQueryData(["db-types"], EXAMPLE_DB_TYPES);
  return qc;
}

const INPUT_CLS =
  "w-full px-3 py-2 text-sm border border-gray-300 rounded-md shadow-sm " +
  "focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 bg-white";

function ExamplePageInner() {
  const [q, setQ] = useState("");
  const [dbType, setDbType] = useState("");
  const [group, setGroup] = useState("");
  const [sortBy, setSortBy] = useState("db_name");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Reset to page 1 on filter change
  useEffect(() => { setPage(1); }, [q, dbType, group]);

  const allGroups = useMemo(
    () => [...new Set(EXAMPLE_DATABASES.map((d) => d.group))].sort(),
    [],
  );

  const filtered = useMemo(() => {
    let rows = EXAMPLE_DATABASES.filter((d) => {
      if (dbType && d.db_type !== dbType) return false;
      if (group && d.group !== group) return false;
      if (q) {
        const lq = q.toLowerCase();
        if (
          !d.db_name.toLowerCase().includes(lq) &&
          !d.db_type.toLowerCase().includes(lq) &&
          !d.group.toLowerCase().includes(lq)
        )
          return false;
      }
      return true;
    });

    rows = [...rows].sort((a, b) => {
      const aVal = String((a as Record<string, unknown>)[sortBy] ?? "");
      const bVal = String((b as Record<string, unknown>)[sortBy] ?? "");
      return sortDir === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });

    return rows;
  }, [q, dbType, group, sortBy, sortDir]);

  const paginated: DatabaseRecord[] = filtered.slice(
    (page - 1) * pageSize,
    page * pageSize,
  );

  function handleSort(key: string, dir: "asc" | "desc") {
    setSortBy(key);
    setSortDir(dir);
    setPage(1);
  }

  const hasFilters = !!(q || dbType || group);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white px-6 py-4 flex items-center gap-3">
        <DatabaseIcon className="w-6 h-6 text-brand-600" aria-hidden="true" />
        <h1 className="text-xl font-semibold text-gray-900">DBaaS Manager</h1>
        <span className="ml-2 text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200">
          Demo
        </span>
        <div className="ml-auto flex items-center gap-2 text-sm text-gray-500">
          <span className="font-medium text-gray-700">admin</span>
        </div>
      </header>

      {/* Demo banner */}
      <div className="bg-amber-50 border-b border-amber-200 px-6 py-2.5 flex items-center gap-2 text-sm text-amber-800">
        <Info className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
        <span>
          This is a <strong>demo preview</strong> with synthetic data. No real API calls are made.{" "}
          <a href="/" className="underline font-medium hover:text-amber-900">
            Go to the live app →
          </a>
        </span>
      </div>

      <main className="flex-1 max-w-screen-2xl mx-auto w-full px-6 py-6">
        <ParentChartsSection />

        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row sm:items-end gap-3 mb-6">
          <div className="flex flex-col sm:flex-row gap-3 flex-1">
            <div className="flex-1 sm:max-w-xs">
              <label htmlFor="ex-type-filter" className="block text-xs font-medium text-gray-500 mb-1">
                Type
              </label>
              <select
                id="ex-type-filter"
                value={dbType}
                onChange={(e) => setDbType(e.target.value)}
                className={INPUT_CLS}
              >
                <option value="">All types</option>
                {EXAMPLE_DB_TYPES.map((t) => (
                  <option key={t.canonical_name} value={t.canonical_name}>
                    {t.display_label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex-1 sm:max-w-xs">
              <label htmlFor="ex-search" className="block text-xs font-medium text-gray-500 mb-1">
                Name
              </label>
              <input
                id="ex-search"
                type="search"
                placeholder="Search…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                className={INPUT_CLS}
              />
            </div>

            <div className="flex-1 sm:max-w-xs">
              <label htmlFor="ex-group-filter" className="block text-xs font-medium text-gray-500 mb-1">
                Group
              </label>
              <select
                id="ex-group-filter"
                value={group}
                onChange={(e) => setGroup(e.target.value)}
                className={INPUT_CLS}
              >
                <option value="">All groups</option>
                {allGroups.map((g) => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Fake scan button */}
          <div className="flex items-center gap-3">
            <button
              disabled
              title="Scan is disabled in demo mode"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium bg-gray-100 text-gray-400 cursor-not-allowed"
            >
              <RefreshCw className="w-4 h-4" aria-hidden="true" />
              Scan Now
            </button>
            <span className="text-xs text-gray-400">
              Last scan: {new Date("2026-04-17T08:00:00Z").toLocaleString()}
            </span>
          </div>
        </div>

        <ErrorBoundary>
          <DatabaseTable
            records={paginated}
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={handleSort}
            hasFilters={hasFilters}
            totalUnfiltered={EXAMPLE_DATABASES.length}
          />
          <Pagination
            page={page}
            pageSize={pageSize}
            total={filtered.length}
            onPageChange={setPage}
            onPageSizeChange={(size) => { setPageSize(size); setPage(1); }}
          />
        </ErrorBoundary>
      </main>
    </div>
  );
}

export function ExamplePage() {
  const queryClient = useMemo(makeExampleQueryClient, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ExamplePageInner />
    </QueryClientProvider>
  );
}
