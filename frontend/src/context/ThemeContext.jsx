/**
 * Zayado — ThemeContext
 *
 * 3 modes : "light" | "dark" | "system" (suit prefers-color-scheme du navigateur).
 * Persisté en localStorage. Applique `data-theme="dark"` ou rien sur <html>.
 * Le mode "system" écoute matchMedia et bascule automatiquement.
 */
import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

const ThemeContext = createContext({
  theme: "light",       // mode choisi par l'user : light | dark | system
  resolved: "light",    // mode appliqué effectivement (system résolu)
  setTheme: () => {},
});

const STORAGE_KEY = "zayado.theme";

function getSystemTheme() {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(resolved) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  if (resolved === "dark") root.setAttribute("data-theme", "dark");
  else root.removeAttribute("data-theme");
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || "light";
    } catch {
      return "light";
    }
  });
  const [resolved, setResolved] = useState(() => {
    const initial = (typeof localStorage !== "undefined" && localStorage.getItem(STORAGE_KEY)) || "light";
    return initial === "system" ? getSystemTheme() : initial;
  });

  const setTheme = useCallback((mode) => {
    setThemeState(mode);
    try { localStorage.setItem(STORAGE_KEY, mode); } catch {}
    const r = mode === "system" ? getSystemTheme() : mode;
    setResolved(r);
    applyTheme(r);
  }, []);

  // Listen to system changes when in "system" mode
  useEffect(() => {
    if (theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      const r = mq.matches ? "dark" : "light";
      setResolved(r);
      applyTheme(r);
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [theme]);

  // Apply on mount
  useEffect(() => {
    applyTheme(resolved);
  }, [resolved]);

  return (
    <ThemeContext.Provider value={{ theme, resolved, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
