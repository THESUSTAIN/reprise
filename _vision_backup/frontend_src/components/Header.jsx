import React from "react";
import { motion } from "framer-motion";
import { Languages, Moon, Sun, Heart, Compass } from "lucide-react";
import { useApp } from "@/context/AppContext";

export const Header = ({ onFavoritesClick, onLogoClick }) => {
  const { t, lang, toggleLang, theme, toggleTheme, favorites } = useApp();

  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="fixed top-0 inset-x-0 z-50"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 mt-3">
        <div className="glass flex items-center justify-between gap-3 rounded-full border border-border bg-card/70 px-4 sm:px-6 py-3 shadow-[0_12px_32px_rgba(0,0,0,0.08)]">
          <button
            data-testid="nav-brand-logo"
            onClick={onLogoClick}
            className="flex items-center gap-2.5 group"
          >
            <span className="grid h-9 w-9 place-items-center rounded-full bg-[hsl(var(--clay))] text-white shadow-lg transition-transform group-hover:rotate-[20deg]">
              <Compass className="h-5 w-5" strokeWidth={2.2} />
            </span>
            <span className="font-display text-lg font-bold tracking-tight">{t("brand")}</span>
          </button>

          <div className="flex items-center gap-1.5 sm:gap-2">
            <button
              data-testid="favorites-counter-badge"
              onClick={onFavoritesClick}
              className="relative flex items-center gap-1.5 rounded-full border border-border px-3 py-2 text-sm font-medium transition-colors hover:bg-secondary"
            >
              <Heart className="h-4 w-4 text-[hsl(var(--clay))]" fill={favorites.length ? "currentColor" : "none"} />
              <span className="hidden sm:inline">{t("nav_favorites")}</span>
              {favorites.length > 0 && (
                <span className="ml-0.5 grid h-5 min-w-5 place-items-center rounded-full bg-[hsl(var(--clay))] px-1 text-xs font-bold text-white">
                  {favorites.length}
                </span>
              )}
            </button>

            <button
              data-testid="language-toggle-button"
              onClick={toggleLang}
              className="flex items-center gap-1.5 rounded-full border border-border px-3 py-2 text-sm font-semibold transition-colors hover:bg-secondary"
            >
              <Languages className="h-4 w-4" />
              <span>{lang.toUpperCase()}</span>
            </button>

            <button
              data-testid="theme-toggle-button"
              onClick={toggleTheme}
              className="grid h-9 w-9 place-items-center rounded-full border border-border transition-colors hover:bg-secondary"
              aria-label="Toggle theme"
            >
              {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </div>
    </motion.header>
  );
};
