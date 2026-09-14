import React from "react";
import { motion } from "framer-motion";
import { X, Heart, ArrowUpRight } from "lucide-react";
import { useApp } from "@/context/AppContext";
import { templates } from "@/data/templates";

export const FavoritesPanel = ({ onClose, onOpen }) => {
  const { lang, t, favorites, toggleFavorite } = useApp();
  const favList = templates.filter((tp) => favorites.includes(tp.id));

  React.useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[70] flex justify-end bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.aside
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", stiffness: 320, damping: 34 }}
        onClick={(e) => e.stopPropagation()}
        className="h-full w-full max-w-md overflow-y-auto bg-background p-6 shadow-2xl"
      >
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-2 font-display text-2xl font-bold">
            <Heart className="h-5 w-5 text-[hsl(var(--clay))]" fill="currentColor" />
            {t("nav_favorites")}
          </h3>
          <button
            onClick={onClose}
            className="grid h-10 w-10 place-items-center rounded-full border border-border transition-colors hover:bg-secondary"
            aria-label={t("close")}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {favList.length === 0 ? (
          <p className="mt-16 text-center text-muted-foreground">{t("no_favorites")}</p>
        ) : (
          <div className="mt-6 space-y-4">
            {favList.map((tpl) => (
              <div
                key={tpl.id}
                className="group flex gap-4 rounded-2xl border border-border bg-card p-3 transition-colors hover:bg-secondary/50"
              >
                <img src={tpl.cardImage} alt="" className="h-20 w-20 shrink-0 rounded-xl object-cover" />
                <div className="flex-1">
                  <p className="font-mono-accent text-[10px] uppercase tracking-widest text-muted-foreground">
                    {tpl.subtitle[lang]}
                  </p>
                  <h4 className="font-display text-lg font-bold leading-tight">{tpl.name[lang]}</h4>
                  <div className="mt-2 flex items-center gap-3">
                    <button
                      onClick={() => { onClose(); onOpen(tpl); }}
                      className="inline-flex items-center gap-1 text-sm font-semibold"
                      style={{ color: tpl.accent }}
                    >
                      {t("explore_more")} <ArrowUpRight className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => toggleFavorite(tpl)}
                      className="text-sm text-muted-foreground hover:text-[hsl(var(--clay))]"
                    >
                      <Heart className="h-4 w-4" fill="currentColor" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </motion.aside>
    </motion.div>
  );
};
