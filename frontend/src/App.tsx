import { ErrorBoundary } from "./components/ErrorBoundary";
import { Pagination } from "./components/Pagination";
import { TableSkeleton } from "./components/TableSkeleton";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { DatabaseTable } from "./components/databases/DatabaseTable";
import { Header } from "./components/layout/Header";
import { ScanButton } from "./components/scan/ScanButton";
import { useDbTypes } from "./hooks/useDbTypes";
import { useGroups } from "./hooks/useGroups";
import { useDatabases } from "./hooks/useDatabases";
import { useUrlFilters } from "./hooks/useUrlFilters";

const INPUT_CLS =
  "w-full px-3 py-2 text-sm border border-gray-300 rounded-md shadow-sm " +
  "focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 bg-white";

export default function App() {
  const { filters, setFilters } = useUrlFilters();
  const { q, db_type, group, page, page_size, sort_by, sort_dir } = filters;

  const { data, isLoading, isError, refetch } = useDatabases({
    q: q || undefined,
    db_type: db_type || undefined,
    group: group || undefined,
    limit: page_size,
    offset: (page - 1) * page_size,
    sort_by: sort_by || undefined,
    sort_dir: sort_dir,
  });

  const { data: dbTypes } = useDbTypes();
  const { data: groups } = useGroups();

  const hasFilters = !!(q || db_type || group);

  function handleSearch(val: string) {
    setFilters({ q: val, page: 1 });
  }

  function handleTypeChange(val: string) {
    setFilters({ db_type: val, page: 1 });
  }

  function handleGroupChange(val: string) {
    setFilters({ group: val, page: 1 });
  }

  function handleSort(key: string, dir: "asc" | "desc") {
    setFilters({ sort_by: key, sort_dir: dir, page: 1 });
  }

  return (
    <ProtectedRoute>
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />

      <main className="flex-1 max-w-screen-2xl mx-auto w-full px-6 py-6">
        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row sm:items-end gap-3 mb-6">
          <div className="flex flex-col sm:flex-row gap-3 flex-1">
            {/* Type filter — matches "Type" column (1st) */}
            <div className="flex-1 sm:max-w-xs">
              <label htmlFor="type-filter" className="block text-xs font-medium text-gray-500 mb-1">
                Type
              </label>
              <select
                id="type-filter"
                value={db_type}
                onChange={(e) => handleTypeChange(e.target.value)}
                className={INPUT_CLS}
              >
                <option value="">All types</option>
                {dbTypes?.map((t) => (
                  <option key={t.canonical_name} value={t.canonical_name}>
                    {t.display_label}
                  </option>
                ))}
              </select>
            </div>

            {/* Name search — matches "Name" column (2nd) */}
            <div className="flex-1 sm:max-w-xs">
              <label htmlFor="search-input" className="block text-xs font-medium text-gray-500 mb-1">
                Name
              </label>
              <input
                id="search-input"
                type="search"
                placeholder="Search…"
                value={q}
                onChange={(e) => handleSearch(e.target.value)}
                className={INPUT_CLS}
              />
            </div>

            {/* Group filter — matches "Group" column (3rd) */}
            <div className="flex-1 sm:max-w-xs">
              <label htmlFor="group-filter" className="block text-xs font-medium text-gray-500 mb-1">
                Group
              </label>
              <select
                id="group-filter"
                value={group}
                onChange={(e) => handleGroupChange(e.target.value)}
                className={INPUT_CLS}
              >
                <option value="">All groups</option>
                {groups?.map((g) => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>
          </div>

          <ScanButton />
        </div>

        {/* Loading skeleton */}
        {isLoading && <TableSkeleton />}

        {/* Error state */}
        {isError && (
          <div className="text-center py-16">
            <p className="text-red-500 mb-4 text-sm">
              Failed to load databases. Is the backend running?
            </p>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 text-sm font-medium bg-brand-600 text-white rounded-md hover:bg-brand-700 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
            >
              Retry
            </button>
          </div>
        )}

        {/* Table + pagination */}
        {data && (
          <ErrorBoundary>
            <DatabaseTable
              records={data.items}
              sortBy={sort_by}
              sortDir={sort_dir}
              onSort={handleSort}
              hasFilters={hasFilters}
              totalUnfiltered={data.total}
            />
            <Pagination
              page={page}
              pageSize={page_size}
              total={data.total}
              onPageChange={(p) => setFilters({ page: p })}
              onPageSizeChange={(size) => setFilters({ page_size: size, page: 1 })}
            />
          </ErrorBoundary>
        )}
      </main>
    </div>
    </ProtectedRoute>
  );
}
