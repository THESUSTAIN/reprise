import React from "react";
import { motion } from "framer-motion";
import { Quote } from "lucide-react";
import { useApp } from "@/context/AppContext";

export const IdentityView = ({ template }) => {
  const { lang } = useApp();

  return (
    <div data-testid="identity-manifesto-container" className="space-y-8">
      <div className="grid gap-5 md:grid-cols-3">
        {template.columns.map((col, i) => (
          <motion.div
            key={col.key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.09 }}
            className="rounded-2xl border border-border bg-card p-6"
          >
            <span className="font-mono-accent text-xs uppercase tracking-[0.2em]" style={{ color: col.color }}>
              0{i + 1}
            </span>
            <h4 className="mt-2 font-display text-xl font-bold leading-tight">{col.title[lang]}</h4>
            <div className="mt-4 space-y-3">
              {col.items[lang].map((it) => (
                <p key={it} className="border-l-2 pl-3 text-sm leading-relaxed" style={{ borderColor: col.color }}>
                  {it}
                </p>
              ))}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Affirmations */}
      <div className="rounded-2xl border border-border bg-gradient-to-br from-[hsl(var(--lilac))]/12 to-transparent p-6">
        <div className="mb-4 flex items-center gap-2">
          <Quote className="h-5 w-5 text-[hsl(var(--lilac))]" />
          <span className="font-mono-accent text-xs uppercase tracking-[0.2em] text-muted-foreground">
            {lang === "fr" ? "Affirmations quotidiennes" : "Daily affirmations"}
          </span>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          {template.affirmations[lang].map((a) => (
            <p key={a} className="font-display text-lg italic leading-snug">
              “{a}”
            </p>
          ))}
        </div>
      </div>
    </div>
  );
};
