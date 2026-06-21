import React, { createContext, useContext, useEffect, useState } from 'react';
import { authApi } from '../lib/api';

const AuthContext = createContext({
  user: null,
  loading: true,
  login: async () => {},
  logout: () => {},
  refresh: async () => {},
});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    let token = localStorage.getItem('zayado_token');
    // Auto-session invité : aucune page de connexion requise (login ajouté plus tard)
    if (!token) {
      try {
        const res = await authApi.guestLogin();
        token = res?.access_token || res?.token;
        if (token) localStorage.setItem('zayado_token', token);
      } catch {
        setUser(null);
        setLoading(false);
        return;
      }
    }
    try {
      const me = await authApi.me();
      setUser(me);
    } catch {
      localStorage.removeItem('zayado_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const login = async (email, password) => {
    const res = await authApi.login(email, password);
    if (res?.access_token) {
      localStorage.setItem('zayado_token', res.access_token);
      await refresh();
    }
    return res;
  };

  const logout = () => {
    localStorage.removeItem('zayado_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
export default AuthContext;
