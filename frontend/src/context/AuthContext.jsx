import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import api from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  // Guard pour éviter les double appels (React StrictMode monte 2x en dev)
  const _fetchingRef = useRef(false);

  const checkAuth = useCallback(async () => {
    if (_fetchingRef.current) return;   // déjà en cours — ignorer
    _fetchingRef.current = true;
    try {
      const r = await api.get("/auth/me");
      setUser(r.data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
      _fetchingRef.current = false;
    }
  }, []);

  useEffect(() => {
    // If returning from Emergent OAuth callback, skip /me — AuthCallback handles it
    if (window.location.hash?.includes("session_id=")) {
      setLoading(false);
      return;
    }
    checkAuth();
  }, [checkAuth]);

  const logout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, loading, checkAuth, refreshUser: checkAuth, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
