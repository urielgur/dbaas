import { DatabaseIcon } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-gray-200 bg-white px-6 py-4 flex items-center gap-3">
      <DatabaseIcon className="w-6 h-6 text-blue-600" />
      <h1 className="text-xl font-semibold text-gray-900">DBaaS Manager</h1>
    </header>
  );
}
