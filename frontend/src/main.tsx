import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Toaster } from "sonner";
import App from "./App.tsx";
import { AuthProvider } from "./auth/AuthContext.tsx";
import { ErrorBoundary } from "./components/ErrorBoundary.tsx";
import { ExamplePage } from "./pages/ExamplePage.tsx";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const isExamplePage = window.location.pathname === "/example";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {isExamplePage ? (
      <ExamplePage />
    ) : (
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ErrorBoundary>
            <App />
          </ErrorBoundary>
          <Toaster position="bottom-right" richColors closeButton />
        </AuthProvider>
      </QueryClientProvider>
    )}
  </StrictMode>,
);
