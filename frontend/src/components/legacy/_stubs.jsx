/**
 * Stubs minimalistes pour porter les composants legacy app-main dans public-site Vite.
 * Pas d'i18n dynamique : on retourne le fallback.
 */
import { createContext, useContext } from "react";

const I18nCtx = createContext({
  t: (_key, fallback) => fallback,
  lang: "fr",
});

export const I18nProvider = ({ children }) => children;

export const useI18n = () => useContext(I18nCtx);

export const useDynamicLogo = () => ({
  logoUrl: "/logo.svg",
});

// useSEO stub — on utilise Helmet directement dans les composants
export const useSEO = () => {};

export const LanguageSwitcher = () => null;

// Simple Button component (replaces shadcn ./ui/button)
export const Button = ({ children, className = "", ...props }) => (
  <button
    {...props}
    className={`inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg font-medium transition ${className}`}
  >
    {children}
  </button>
);
