import { useState } from "react";
import { DatabaseTable } from "./components/databases/DatabaseTable";
import { Header } from "./components/layout/Header";
import { ScanButton } from "./components/scan/ScanButton";
import { useDatabases } from "./hooks/useDatabases";

export default function App() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const { data, isLoading, isError } = useDatabases({
    q: search || undefined,
    db_type: typeFilter || undefined,
  });

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />

      <main className="flex-1 max-w-screen-2xl mx-auto w-full px-6 py-6">
        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-6">
          <div className="flex-1 flex gap-3">
            <input
              type="text"
              placeholder="Search by name…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-64 px-3 py-2 text-sm border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <input
              type="text"
              placeholder="Filter by type (e.g. postgresql)…"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-56 px-3 py-2 text-sm border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <ScanButton />
        </div>

        {/* Results count */}
        {data && (
          <p className="text-sm text-gray-500 mb-3">
            Showing {data.items.length} of {data.total} databases
          </p>
        )}

        {/* Table */}
        {isLoading && (
          <div className="text-center py-16 text-gray-400">Loading…</div>
        )}
        {isError && (
          <div className="text-center py-16 text-red-500">
            Failed to load databases. Is the backend running?
          </div>
        )}
        {data && <DatabaseTable records={data.items} />}
      </main>
    </div>
  );
}
