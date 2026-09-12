import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { getMeRequest, loginRequest, type MeResponse } from "./authApi";

interface AuthState {
  token: string | null;
  user: MeResponse | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

const TOKEN_KEY = "auth_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<MeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const { access_token } = await loginRequest(username, password);
    localStorage.setItem(TOKEN_KEY, access_token);
    setToken(access_token);
    const me = await getMeRequest();
    setUser(me);
  }, []);

  // Validate stored token on mount
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) {
      // Demo builds can bake in a fixed account so visitors skip the login
      // screen entirely. Unset in a normal deployment, so this is a no-op there.
      const demoUsername = import.meta.env.VITE_DEMO_USERNAME;
      const demoPassword = import.meta.env.VITE_DEMO_PASSWORD;
      if (demoUsername && demoPassword) {
        login(demoUsername, demoPassword)
          .catch(() => {
            // Demo credentials rejected — fall back to the normal login page
          })
          .finally(() => setIsLoading(false));
        return;
      }
      setIsLoading(false);
      return;
    }
    // Token exists — verify it's still valid
    setToken(stored);
    getMeRequest()
      .then((me) => {
        setUser(me);
      })
      .catch(() => {
        // Token is expired or invalid
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [login]);

  // Listen for 401s from the Axios interceptor
  useEffect(() => {
    const handler = () => logout();
    window.addEventListener("auth:logout", handler);
    return () => window.removeEventListener("auth:logout", handler);
  }, [logout]);

  return (
    <AuthContext.Provider value={{ token, user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
