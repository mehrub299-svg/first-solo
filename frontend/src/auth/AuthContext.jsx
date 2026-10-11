import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { getMe, login, logout, register } from "../api/auth";
import {
  refreshSession,
  setAccessToken,
  setSessionExpiredHandler,
} from "../api/client";

// A non-secret flag meaning "a refresh cookie probably exists".
const SESSION_HINT = "p101_has_session";
const LEGACY_TOKEN_KEY = "p101_token";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(true);

  const clearSession = useCallback(() => {
    localStorage.removeItem(SESSION_HINT);
    setAccessToken(null);
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setSessionExpiredHandler(clearSession);
  }, [clearSession]);

  // On page load, restore the session from the refresh cookie.
  useEffect(() => {
    localStorage.removeItem(LEGACY_TOKEN_KEY);
    if (!localStorage.getItem(SESSION_HINT)) {
      setBooting(false);
      return undefined;
    }

    let cancelled = false;
    refreshSession()
      .then((accessToken) => {
        if (!cancelled) setToken(accessToken);
      })
      .catch((error) => {
        if (error.status === 401) localStorage.removeItem(SESSION_HINT);
      })
      .finally(() => {
        if (!cancelled) setBooting(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!token) return undefined;
    let cancelled = false;
    getMe()
      .then((me) => {
        if (!cancelled) setUser(me);
      })
      .catch(() => {
        if (!cancelled) clearSession();
      });
    return () => {
      cancelled = true;
    };
  }, [token, clearSession]);

  const signIn = useCallback(async (email, password) => {
    const { access_token: accessToken } = await login(email, password);
    setAccessToken(accessToken);
    localStorage.setItem(SESSION_HINT, "1");
    setToken(accessToken);
  }, []);

  const signUp = useCallback(
    async (email, password) => {
      await register(email, password);
      await signIn(email, password);
    },
    [signIn],
  );

  const signOut = useCallback(async () => {
    try {
      await logout();
    } catch {
      // The local session is cleared either way.
    }
    clearSession();
  }, [clearSession]);

  const value = useMemo(
    () => ({ token, user, booting, signIn, signUp, signOut }),
    [token, user, booting, signIn, signUp, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}