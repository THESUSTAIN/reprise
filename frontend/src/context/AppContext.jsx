import React, { createContext, useContext, useEffect, useMemo, useState, useCallback } from "react";

const AppContext = createContext(null);

const readLS = (k, fallback) => {
  try {
    const v = localStorage.getItem(k);
    return v === null ? fallback : JSON.parse(v);
  } catch {
    return fallback;
  }
};

export function AppProvider({ children }) {
  const [authed, setAuthed] = useState(() => readLS("mx_authed", false));
  const [theme, setTheme] = useState(() => readLS("mx_theme", "dark"));
  const [ambiance, setAmbiance] = useState(() => readLS("mx_ambiance", "elan"));
  const [faith, setFaith] = useState(() => readLS("mx_faith", false));

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") root.classList.add("dark");
    else root.classList.remove("dark");
    localStorage.setItem("mx_theme", JSON.stringify(theme));
  }, [theme]);

  useEffect(() => localStorage.setItem("mx_authed", JSON.stringify(authed)), [authed]);
  useEffect(() => localStorage.setItem("mx_ambiance", JSON.stringify(ambiance)), [ambiance]);
  useEffect(() => localStorage.setItem("mx_faith", JSON.stringify(faith)), [faith]);

  const login = useCallback(() => setAuthed(true), []);
  const logout = useCallback(() => setAuthed(false), []);
  const toggleTheme = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);
  const toggleAmbiance = useCallback(() => setAmbiance((a) => (a === "elan" ? "refuge" : "elan")), []);
  const toggleFaith = useCallback(() => setFaith((f) => !f), []);

  const value = useMemo(
    () => ({
      authed, login, logout,
      theme, setTheme, toggleTheme,
      ambiance, setAmbiance, toggleAmbiance,
      faith, setFaith, toggleFaith,
    }),
    [authed, theme, ambiance, faith, login, logout, toggleTheme, toggleAmbiance, toggleFaith]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
