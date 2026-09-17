import React from "react";
import { motion } from "framer-motion";
import { Heart, ArrowUpRight } from "lucide-react";
import { useApp } from "@/context/AppContext";

const cardVariant = {
  hidden: { y: 40, opacity: 0 },
  show: { y: 0, opacity: 1, transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] } },
};

export const TemplateCard = ({ template, index, onOpen }) => {
  const { lang, t, favorites, toggleFavorite } = useApp();
  const isFav = favorites.includes(template.id);
  const wide = index === 0 || index === 3;

  return (
    <motion.article
      variants={cardVariant}
      data-testid={`template-card-${template.id}`}
      className={`group relative overflow-hidden rounded-3xl border border-border bg-card shadow-[0_12px_32px_rgba(0,0,0,0.07)] transition-all duration-300 hover:-translate-y-1.5 hover:shadow-[0_24px_48px_rgba(0,0,0,0.14)] ${
        wide ? "lg:col-span-2" : ""
      }`}
      style={{ minHeight: 340 }}
    >
      <div role="button" tabIndex={0} onClick={() => onOpen(template)} onKeyDown={(e) => e.key === "Enter" && onOpen(template)} className="block w-full cursor-pointer text-left">
        <div className={`relative overflow-hidden ${wide ? "h-56 sm:h-64" : "h-48"}`}>
          <img
            src={template.cardImage}
            alt={template.name[lang]}
            className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
          />
          <div
            className="absolute inset-0"
            style={{ background: `linear-gradient(160deg, ${template.accent}22 0%, transparent 45%, ${template.accent}ee 100%)` }}
          />
          <span
            className="absolute left-4 top-4 rounded-full px-3 py-1 font-mono-accent text-[10px] uppercase tracking-[0.18em] text-white backdrop-blur"
            style={{ background: `${template.accent}cc` }}
          >
            {t(`filter_${template.category}`)}
          </span>
          <div className="absolute bottom-4 left-4 right-4">
            <p className="font-mono-accent text-[11px] uppercase tracking-[0.2em] text-white/85">
              {template.subtitle[lang]}
            </p>
            <h3 className="font-display text-2xl font-bold text-white drop-shadow-sm">
              {template.name[lang]}
            </h3>
          </div>
        </div>

        <div className="p-5 sm:p-6">
          <p className="text-sm leading-relaxed text-muted-foreground line-clamp-2">
            {template.tagline[lang]}
          </p>
          <div className="mt-5 flex items-center gap-2 font-semibold" style={{ color: template.accent }}>
            <span data-testid={`view-detail-btn-${template.id}`}>{t("view_detail")}</span>
            <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </div>
        </div>
      </div>

      <button
        data-testid={`favorite-btn-${template.id}`}
        onClick={(e) => {
          e.stopPropagation();
          toggleFavorite(template);
        }}
        className="glass absolute right-4 top-4 grid h-10 w-10 place-items-center rounded-full border border-white/30 bg-white/25 text-white transition-transform hover:scale-110"
        aria-label={t("favorite")}
      >
        <Heart className="h-5 w-5" fill={isFav ? "currentColor" : "none"} />
      </button>
    </motion.article>
  );
};
