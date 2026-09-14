import React, { useEffect } from "react";
import { motion } from "framer-motion";
import { X, Heart, Quote } from "lucide-react";
import { useApp } from "@/context/AppContext";
import { PillarsView } from "@/components/details/PillarsView";
import { RoadmapView } from "@/components/details/RoadmapView";
import { IdentityView } from "@/components/details/IdentityView";
import { SensoryView } from "@/components/details/SensoryView";
import { StrategicView } from "@/components/details/StrategicView";

const VIEWS = {
  pillars: PillarsView,
  roadmap: RoadmapView,
  identity: IdentityView,
  sensory: SensoryView,
  strategic: StrategicView,
};

export const TemplateDetail = ({ template, onClose }) => {
  const { lang, t, favorites, toggleFavorite } = useApp();
  const isFav = favorites.includes(template.id);
  const View = VIEWS[template.id];

  useEffect(() => {
    document.body.style.overflow = "hidden";
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  return (
    <motion.div
      data-testid="template-detail-view"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[60] overflow-y-auto bg-background"
    >
      {/* Hero banner */}
      <div className="relative h-64 sm:h-80 overflow-hidden">
        <motion.img
          initial={{ scale: 1.12 }}
          animate={{ scale: 1 }}
          transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
          src={template.heroImage}
          alt={template.name[lang]}
          className="h-full w-full object-cover"
        />
        <div
          className="absolute inset-0"
          style={{ background: `linear-gradient(180deg, ${template.accent}44 0%, transparent 30%, hsl(var(--background)) 100%)` }}
        />

        <div className="absolute right-4 top-4 flex gap-2 sm:right-6 sm:top-6">
          <button
            data-testid="detail-save-button"
            onClick={() => toggleFavorite(template)}
            className="glass flex items-center gap-2 rounded-full border border-white/30 bg-white/25 px-4 py-2.5 font-semibold text-white transition-transform hover:scale-105"
          >
            <Heart className="h-5 w-5" fill={isFav ? "currentColor" : "none"} />
            <span className="hidden sm:inline">{t("favorite")}</span>
          </button>
          <button
            data-testid="detail-close-button"
            onClick={onClose}
            className="glass grid h-11 w-11 place-items-center rounded-full border border-white/30 bg-white/25 text-white transition-transform hover:scale-105 hover:rotate-90"
            aria-label={t("close")}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="absolute bottom-5 left-4 right-4 sm:left-8">
          <span
            className="inline-block rounded-full px-3 py-1 font-mono-accent text-[11px] uppercase tracking-[0.2em] text-white"
            style={{ background: `${template.accent}cc` }}
          >
            {t(`filter_${template.category}`)}
          </span>
          <h2 className="mt-2 font-display text-3xl font-black tracking-tight text-white drop-shadow sm:text-5xl">
            {template.name[lang]}
          </h2>
          <p className="font-mono-accent text-xs uppercase tracking-[0.24em] text-white/90 sm:text-sm">
            {template.subtitle[lang]}
          </p>
        </div>
      </div>

      {/* Body */}
      <div className="mx-auto max-w-6xl px-4 sm:px-8 pb-24 pt-8">
        <div className="grid gap-6 lg:grid-cols-[1fr_320px] lg:items-start">
          <p className="text-base leading-relaxed text-muted-foreground sm:text-lg">
            {template.description[lang]}
          </p>
          <div className="rounded-2xl border border-border bg-card p-5">
            <span className="font-mono-accent text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              {t("best_for")}
            </span>
            <p className="mt-1.5 font-display text-lg font-bold" style={{ color: template.accent }}>
              {template.bestFor[lang]}
            </p>
            <div className="mt-4 flex gap-2 border-t border-border pt-4">
              <Quote className="h-5 w-5 shrink-0" style={{ color: template.accent }} />
              <p className="text-sm italic leading-relaxed">{template.quote[lang]}</p>
            </div>
          </div>
        </div>

        <div className="mt-10">
          <div className="mb-5 flex items-center gap-3">
            <span className="h-px flex-1 bg-border" />
            <span className="font-mono-accent text-xs uppercase tracking-[0.2em] text-muted-foreground">
              {t("structure_label")}
            </span>
            <span className="h-px flex-1 bg-border" />
          </div>
          {View && <View template={template} />}
        </div>
      </div>
    </motion.div>
  );
};
