import React from "react";
import { motion } from "framer-motion";
import { ArrowRight, Heart, Sparkles } from "lucide-react";
import { useApp } from "@/context/AppContext";
import { templates } from "@/data/templates";

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.09, delayChildren: 0.15 } },
};
const rise = {
  hidden: { y: 26, opacity: 0 },
  show: { y: 0, opacity: 1, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] } },
};

export const Hero = ({ onExplore, onFavorites }) => {
  const { t, lang } = useApp();

  return (
    <section className="relative overflow-hidden pt-32 pb-16 sm:pt-40 sm:pb-24">
      {/* ambient blobs */}
      <div className="pointer-events-none absolute -top-24 -left-24 h-96 w-96 rounded-full bg-[hsl(var(--clay))]/20 blur-3xl" />
      <div className="pointer-events-none absolute top-40 -right-20 h-80 w-80 rounded-full bg-[hsl(var(--lilac))]/20 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 left-1/3 h-72 w-72 rounded-full bg-[hsl(var(--ochre))]/15 blur-3xl" />

      <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-[1.05fr_0.95fr]">
        <motion.div variants={stagger} initial="hidden" animate="show">
          <motion.span
            variants={rise}
            className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-4 py-1.5 font-mono-accent text-xs uppercase tracking-[0.22em] text-muted-foreground"
          >
            <Sparkles className="h-3.5 w-3.5 text-[hsl(var(--clay))]" />
            {t("hero_eyebrow")}
          </motion.span>

          <motion.h1
            variants={rise}
            data-testid="hero-headline"
            className="mt-6 font-display text-4xl font-black leading-[1.02] tracking-tight sm:text-5xl lg:text-6xl"
          >
            {t("hero_title_1")}
            <br />
            <span className="relative inline-block text-[hsl(var(--clay))]">
              {t("hero_title_2")}
              <svg className="absolute -bottom-2 left-0 w-full" height="12" viewBox="0 0 300 12" fill="none" preserveAspectRatio="none">
                <path d="M2 9C60 3 220 2 298 6" stroke="hsl(var(--ochre))" strokeWidth="4" strokeLinecap="round" />
              </svg>
            </span>
          </motion.h1>

          <motion.p variants={rise} className="mt-8 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            {t("hero_sub")}
          </motion.p>

          <motion.div variants={rise} className="mt-9 flex flex-wrap items-center gap-3">
            <button
              data-testid="hero-explore-button"
              onClick={onExplore}
              className="group inline-flex items-center gap-2 rounded-full bg-[hsl(var(--clay))] px-6 py-3.5 font-semibold text-white shadow-[0_14px_30px_rgba(224,90,71,0.35)] transition-transform hover:-translate-y-0.5"
            >
              {t("hero_cta")}
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </button>
            <button
              onClick={onFavorites}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-6 py-3.5 font-semibold transition-colors hover:bg-secondary"
            >
              <Heart className="h-4 w-4 text-[hsl(var(--clay))]" />
              {t("hero_cta_fav")}
            </button>
          </motion.div>
        </motion.div>

        {/* Stacked preview cards */}
        <motion.div
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
          className="relative h-[340px] sm:h-[440px]"
        >
          {templates.slice(0, 4).map((tpl, i) => {
            const rot = [-9, -3, 4, 10][i];
            const x = [0, 90, 180, 250][i];
            const y = [40, 0, 60, 20][i];
            return (
              <motion.div
                key={tpl.id}
                whileHover={{ y: -14, rotate: 0, zIndex: 30, scale: 1.03 }}
                transition={{ type: "spring", stiffness: 260, damping: 20 }}
                style={{ rotate: `${rot}deg`, left: x, top: y, borderColor: tpl.accent }}
                className="absolute w-40 sm:w-52 overflow-hidden rounded-2xl border-2 bg-card shadow-2xl"
              >
                <div className="relative h-28 sm:h-36 overflow-hidden">
                  <img src={tpl.cardImage} alt="" className="h-full w-full object-cover" />
                  <div className="absolute inset-0" style={{ background: `linear-gradient(180deg, transparent 40%, ${tpl.accent}dd)` }} />
                </div>
                <div className="p-3">
                  <p className="font-display text-sm font-bold leading-tight">{tpl.name[lang]}</p>
                  <p className="mt-0.5 font-mono-accent text-[10px] uppercase tracking-widest text-muted-foreground">
                    {tpl.subtitle[lang]}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
};
