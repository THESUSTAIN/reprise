import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { ui } from "@/data/ui";
import { fetchFavorites, toggleFavoriteApi } from "@/lib/api";
import { toast } from "sonner";

const AppContext = createContext(null);
export const useApp = () => useContext(AppContext);

const getSessionId = () => {
  let sid = localStorage.getItem("vb_session");
  if (!sid) {
    sid = crypto.randomUUID();
    localStorage.setItem("vb_session", sid);
  }
  return sid;
};

export const AppProvider = ({ children }) => {
  const [lang, setLang] = useState(() => localStorage.getItem("vb_lang") || "fr");
  const [theme, setTheme] = useState(() => localStorage.getItem("vb_theme") || "light");
  const [favorites, setFavorites] = useState([]);
  const sessionId = getSessionId();

  useEffect(() => {
    localStorage.setItem("vb_lang", lang);
  }, [lang]);

  useEffect(() => {
    localStorage.setItem("vb_theme", theme);
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  useEffect(() => {
    fetchFavorites(sessionId).then(setFavorites).catch(() => {});
  }, [sessionId]);

  const t = useCallback((key) => ui[lang][key] ?? key, [lang]);

  const toggleLang = () => setLang((l) => (l === "fr" ? "en" : "fr"));
  const toggleTheme = () => setTheme((th) => (th === "light" ? "dark" : "light"));

  const toggleFavorite = async (template) => {
    const wasFav = favorites.includes(template.id);
    // optimistic
    setFavorites((prev) =>
      wasFav ? prev.filter((id) => id !== template.id) : [...prev, template.id]
    );
    const name = template.name[lang];
    toast(`${name} ${wasFav ? ui[lang].unsaved : ui[lang].saved}`, {
      description: wasFav ? "♡" : "❤",
    });
    try {
      const ids = await toggleFavoriteApi(sessionId, template.id);
      setFavorites(ids);
    } catch (e) {
      // revert on failure
      setFavorites((prev) =>
        wasFav ? [...prev, template.id] : prev.filter((id) => id !== template.id)
      );
    }
  };

  return (
    <AppContext.Provider
      value={{ lang, setLang, toggleLang, theme, toggleTheme, t, favorites, toggleFavorite }}
    >
      {children}
    </AppContext.Provider>
  );
};
