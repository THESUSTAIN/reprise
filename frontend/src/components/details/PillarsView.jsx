import React from "react";
import { motion } from "framer-motion";
import { Briefcase, Wallet, HeartPulse, Users, Sparkles } from "lucide-react";
import { useApp } from "@/context/AppContext";

const ICONS = { briefcase: Briefcase, wallet: Wallet, "heart-pulse": HeartPulse, users: Users, sparkles: Sparkles };

export const PillarsView = ({ template }) => {
  const { lang } = useApp();
  const sectors = template.sectors;
  const R = 130;
  const cx = 160;
  const cy = 160;

  return (
    <div data-testid="interactive-wheel-pillars" className="grid gap-10 lg:grid-cols-[340px_1fr] lg:items-start">
      {/* Radial wheel */}
      <div className="mx-auto">
        <div className="relative">
          <svg width="320" height="320" viewBox="0 0 320 320" className="animate-spin-slow" style={{ animationDuration: "80s" }}>
            {sectors.map((s, i) => {
              const a0 = (i / sectors.length) * Math.PI * 2 - Math.PI / 2;
              const a1 = ((i + 1) / sectors.length) * Math.PI * 2 - Math.PI / 2;
              const x0 = cx + R * Math.cos(a0);
              const y0 = cy + R * Math.sin(a0);
              const x1 = cx + R * Math.cos(a1);
              const y1 = cy + R * Math.sin(a1);
              return (
                <path
                  key={s.name.en}
                  d={`M${cx},${cy} L${x0},${y0} A${R},${R} 0 0,1 ${x1},${y1} Z`}
                  fill={s.color}
                  opacity={0.85}
                  stroke="hsl(var(--card))"
                  strokeWidth="3"
                />
              );
            })}
          </svg>
          <div className="absolute inset-0 grid place-items-center">
            <div className="grid h-24 w-24 place-items-center rounded-full bg-card text-center shadow-xl">
              <span className="font-display text-sm font-bold leading-tight">
                {lang === "fr" ? "Équilibre" : "Balance"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Sector cards */}
      <div className="grid gap-4 sm:grid-cols-2">
        {sectors.map((s, i) => {
          const Icon = ICONS[s.icon] || Sparkles;
          return (
            <motion.div
              key={s.name.en}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              className="rounded-2xl border border-border bg-card p-5"
              style={{ borderTop: `4px solid ${s.color}` }}
            >
              <div className="flex items-center gap-3">
                <span className="grid h-10 w-10 place-items-center rounded-xl text-white" style={{ background: s.color }}>
                  <Icon className="h-5 w-5" />
                </span>
                <h4 className="font-display text-lg font-bold">{s.name[lang]}</h4>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">{s.focus[lang]}</p>
              <ul className="mt-3 space-y-1.5">
                {s.goals[lang].map((g) => (
                  <li key={g} className="flex items-start gap-2 text-sm">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: s.color }} />
                    {g}
                  </li>
                ))}
              </ul>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
