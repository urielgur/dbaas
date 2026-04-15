import type { ReactNode } from "react";
import { useAuth } from "../../auth/AuthContext";
import { LoginPage } from "../../pages/LoginPage";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { token, isLoading } = useAuth();

  if (isLoading) {
    // Prevents flash of login page while validating a stored token
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!token) {
    return <LoginPage />;
  }

  return <>{children}</>;
}
