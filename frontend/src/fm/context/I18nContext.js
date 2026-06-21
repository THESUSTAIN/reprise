import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { LANGUAGES, t } from "@fm/lib/i18n";

const STORAGE_KEY = "mxai_lang";
const SUPPORTED = LANGUAGES.map((l) => l.code);
const FALLBACK = "fr";

// Détection navigator.language → code 2 lettres ('en-US' → 'en')
function detectFromNavigator() {
  if (typeof navigator === "undefined") return null;
  const candidates = [navigator.language, ...(navigator.languages || [])];
  for (const l of candidates) {
    const code = (l || "").toLowerCase().split("-")[0];
    if (SUPPORTED.includes(code)) return code;
  }
  return null;
}

const I18nCtx = createContext(null);

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved && SUPPORTED.includes(saved)) return saved;
    } catch { /* ignore */ }
    // App FR-only par défaut — l'utilisateur peut changer via Paramètres.
    // Avant : detectFromNavigator() || FALLBACK qui exposait l'app en EN/ES/DE selon navigateur.
    return FALLBACK;
  });

  // Update <html lang="…">
  useEffect(() => {
    try { document.documentElement.lang = lang; } catch { /* ignore */ }
  }, [lang]);

  const setLang = useCallback((code) => {
    if (!SUPPORTED.includes(code)) return;
    try { localStorage.setItem(STORAGE_KEY, code); } catch { /* ignore */ }
    setLangState(code);
  }, []);

  const value = {
    lang,
    setLang,
    t: (key, vars) => t(lang, key, vars),
    languages: LANGUAGES,
  };

  return <I18nCtx.Provider value={value}>{children}</I18nCtx.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nCtx);
  if (!ctx) throw new Error("useI18n must be used inside <I18nProvider>");
  return ctx;
}
