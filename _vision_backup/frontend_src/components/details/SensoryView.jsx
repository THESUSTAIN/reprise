import React from "react";
import { motion } from "framer-motion";
import { useApp } from "@/context/AppContext";

export const SensoryView = ({ template }) => {
  const { lang } = useApp();

  return (
    <div data-testid="sensory-moodboard-grid" className="space-y-8">
      {/* Bento collage */}
      <div className="grid auto-rows-[130px] grid-cols-2 gap-3 sm:grid-cols-4 sm:auto-rows-[150px]">
        {template.collage.map((src, i) => {
          const spans = [
            "col-span-2 row-span-2",
            "col-span-1 row-span-1",
            "col-span-1 row-span-2",
            "col-span-1 row-span-1",
            "col-span-1 row-span-1",
          ];
          return (
            <motion.div
              key={src}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.07 }}
              whileHover={{ scale: 1.03 }}
              className={`group relative overflow-hidden rounded-2xl ${spans[i % spans.length]}`}
            >
              <img src={src} alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110" />
            </motion.div>
          );
        })}
        {/* Quote tile */}
        <div className="col-span-2 flex items-center rounded-2xl bg-[hsl(var(--rose))] p-5 text-white sm:col-span-1">
          <p className="font-display text-lg font-bold italic leading-tight">“{template.quote[lang]}”</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Palette */}
        <div className="rounded-2xl border border-border bg-card p-5">
          <span className="font-mono-accent text-xs uppercase tracking-[0.2em] text-muted-foreground">
            {lang === "fr" ? "Palette" : "Palette"}
          </span>
          <div className="mt-3 flex flex-wrap gap-2">
            {template.palette.map((c) => (
              <div key={c} className="h-12 flex-1 min-w-[44px] rounded-xl shadow-inner" style={{ background: c }} title={c} />
            ))}
          </div>
        </div>

        {/* Keywords */}
        <div className="rounded-2xl border border-border bg-card p-5">
          <span className="font-mono-accent text-xs uppercase tracking-[0.2em] text-muted-foreground">
            {lang === "fr" ? "Mots-clés d'énergie" : "Energy keywords"}
          </span>
          <div className="mt-3 flex flex-wrap gap-2">
            {template.keywords[lang].map((k, i) => (
              <span
                key={k}
                className="rounded-full px-3 py-1.5 text-sm font-medium"
                style={{ background: `${template.palette[i % template.palette.length]}22`, color: template.palette[i % template.palette.length] }}
              >
                {k}
              </span>
            ))}
          </div>
        </div>

        {/* Textures */}
        <div className="rounded-2xl border border-border bg-card p-5">
          <span className="font-mono-accent text-xs uppercase tracking-[0.2em] text-muted-foreground">
            {lang === "fr" ? "Textures & matières" : "Textures & materials"}
          </span>
          <ul className="mt-3 space-y-2">
            {template.textures[lang].map((tx) => (
              <li key={tx} className="flex items-center gap-2 text-sm">
                <span className="h-2 w-2 rounded-full bg-[hsl(var(--rose))]" />
                {tx}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
