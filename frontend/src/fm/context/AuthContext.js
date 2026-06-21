import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { authApi, getToken, setToken, setStoredUser, getStoredUser, clearAuth } from "@fm/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser());
  const [booting, setBooting] = useState(Boolean(getToken()));

  // On mount: if token present, fetch /me to refresh user
  useEffect(() => {
    let cancelled = false;
    const t = getToken();
    if (!t) {
      setBooting(false);
      return () => {};
    }
    authApi
      .me()
      .then((u) => {
        if (cancelled) return;
        setUser(u);
        setStoredUser(u);
      })
      .catch(() => {
        if (cancelled) return;
        clearAuth();
        setUser(null);
      })
      .finally(() => !cancelled && setBooting(false));
    return () => { cancelled = true; };
  }, []);

  const login = useCallback(async (email, password) => {
    const { token, user: u } = await authApi.login(email, password);
    setToken(token); setStoredUser(u); setUser(u);
    return u;
  }, []);

  const register = useCallback(async (email, password) => {
    const { token, user: u } = await authApi.register(email, password);
    setToken(token); setStoredUser(u); setUser(u);
    return u;
  }, []);

  const refresh = useCallback(async () => {
    const u = await authApi.me();
    setUser(u); setStoredUser(u);
    return u;
  }, []);

  const logout = useCallback(() => {
    clearAuth(); setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, booting, login, register, refresh, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
