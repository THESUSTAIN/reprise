import React from "react";
import { motion } from "framer-motion";
import { TrendingUp, Flag, Users, CheckCircle2, Circle, Loader } from "lucide-react";
import { useApp } from "@/context/AppContext";

const STATUS = {
  done: { icon: CheckCircle2, color: "#10B981" },
  active: { icon: Loader, color: "#D97706" },
  next: { icon: Circle, color: "#8B5CF6" },
};

export const StrategicView = ({ template }) => {
  const { lang } = useApp();

  return (
    <div data-testid="cockpit-dashboard-grid" className="space-y-6">
      {/* KPIs */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {template.kpis.map((kpi, i) => (
          <motion.div
            key={kpi.label.en}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            className="rounded-2xl border border-border bg-card p-5"
            style={{ borderLeft: `4px solid ${kpi.color}` }}
          >
            <div className="flex items-center justify-between">
              <span className="font-mono-accent text-xs uppercase tracking-[0.15em] text-muted-foreground">
                KPI
              </span>
              <TrendingUp className="h-4 w-4" style={{ color: kpi.color }} />
            </div>
            <p className="mt-3 font-display text-3xl font-black" style={{ color: kpi.color }}>
              {kpi.value}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">{kpi.label[lang]}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        {/* Milestones */}
        <div className="rounded-2xl border border-border bg-card p-6">
          <div className="mb-4 flex items-center gap-2">
            <Flag className="h-5 w-5 text-[hsl(var(--emerald))]" />
            <h4 className="font-display text-lg font-bold">
              {lang === "fr" ? "Jalons clés" : "Key milestones"}
            </h4>
          </div>
          <div className="space-y-3">
            {template.milestones.map((m) => {
              const st = STATUS[m.status];
              const Icon = st.icon;
              return (
                <div key={m.title.en} className="flex items-center gap-3 rounded-xl bg-secondary/50 px-4 py-3">
                  <Icon className="h-5 w-5 shrink-0" style={{ color: st.color }} />
                  <span className={`text-sm ${m.status === "done" ? "line-through opacity-60" : "font-medium"}`}>
                    {m.title[lang]}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Team strategy */}
        <div className="rounded-2xl border border-border bg-gradient-to-br from-[hsl(var(--emerald))]/12 to-transparent p-6">
          <div className="mb-4 flex items-center gap-2">
            <Users className="h-5 w-5 text-[hsl(var(--emerald))]" />
            <h4 className="font-display text-lg font-bold">
              {lang === "fr" ? "Stratégie d'équipe" : "Team strategy"}
            </h4>
          </div>
          <ul className="space-y-3">
            {template.team[lang].map((it) => (
              <li key={it} className="flex items-start gap-2 text-sm">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[hsl(var(--emerald))]" />
                {it}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
