import { DatabaseIcon, LogOutIcon, UserIcon } from "lucide-react";
import { useAuth } from "../../auth/AuthContext";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="border-b border-gray-200 bg-white px-6 py-4 flex items-center gap-3">
      <DatabaseIcon className="w-6 h-6 text-brand-600" aria-hidden="true" />
      <h1 className="text-xl font-semibold text-gray-900">DBaaS Manager</h1>

      {user && (
        <div className="ml-auto flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-sm text-gray-600">
            <UserIcon className="w-4 h-4" aria-hidden="true" />
            {user.username}
          </span>
          <button
            onClick={logout}
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900
                       transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500
                       focus:ring-offset-2 rounded"
            aria-label="Sign out"
          >
            <LogOutIcon className="w-4 h-4" aria-hidden="true" />
            Sign out
          </button>
        </div>
      )}
    </header>
  );
}
