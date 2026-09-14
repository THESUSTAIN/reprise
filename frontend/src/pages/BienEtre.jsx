import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { HeartPulse, Flame, Timer, Check, Sparkles, Wind } from "lucide-react";
import { GlassCard } from "@/components/common/GlassCard";
import { PageHeader } from "@/components/common/PageHeader";
import { Gauge } from "@/components/common/Gauge";
import { wellbeing } from "@/data/mock";
import { tooltipStyle, chartAxis } from "@/components/common/chartTheme";
import { cn } from "@/lib/utils";

const signalTone = {
  gold: "border-gold/25 bg-gold/5 text-gold",
  emerald: "border-emerald-500/25 bg-emerald-500/5 text-emerald-400",
};
const moodColors = ["#F43F5E", "#FB923C", "#D4AF37", "#34D399", "#10B981"];

export default function BienEtre() {
  const [rituals, setRituals] = useState(() => Object.fromEntries(wellbeing.rituals.map((r) => [r.id, r.done])));
  const done = Object.values(rituals).filter(Boolean).length;

  return (
    <div data-testid="bien-etre-page">
      <PageHeader
        icon={HeartPulse}
        title="Bien-être"
        subtitle="Votre énergie est votre premier actif. Suivez vos rituels et vos signaux anti-surcharge."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <GlassCard className="flex flex-col items-center text-center" glow="emerald">
          <h2 className="font-serif text-lg font-medium self-start mb-2">Énergie du jour</h2>
          <Gauge value={wellbeing.energyToday} size={150} label={`${wellbeing.energyToday}`} sublabel="/ 100" color="#10B981" />
        </GlassCard>

        <div className="grid grid-cols-2 gap-4">
          <GlassCard className="flex flex-col justify-center items-center text-center">
            <Flame className="h-6 w-6 text-gold mb-2" />
            <p className="font-serif text-3xl font-semibold">{wellbeing.streakDays}</p>
            <p className="text-xs text-muted-foreground mt-1">jours de streak</p>
          </GlassCard>
          <GlassCard className="flex flex-col justify-center items-center text-center">
            <Timer className="h-6 w-6 text-cyan-400 mb-2" />
            <p className="font-serif text-3xl font-semibold">{Math.round(wellbeing.focusMinutes / 60)}h</p>
            <p className="text-xs text-muted-foreground mt-1">de focus (7j)</p>
          </GlassCard>
          <GlassCard className="col-span-2">
            <h3 className="font-serif text-base font-medium mb-3">Rituels du jour · {done}/{wellbeing.rituals.length}</h3>
            <div className="space-y-2">
              {wellbeing.rituals.map((r) => (
                <button key={r.id} data-testid={`ritual-${r.id}`} onClick={() => setRituals((s) => ({ ...s, [r.id]: !s[r.id] }))} className="w-full flex items-center gap-2.5 text-left group">
                  <span className={cn("h-4 w-4 shrink-0 rounded-md border grid place-items-center transition-colors", rituals[r.id] ? "bg-emerald-500 border-emerald-500" : "border-muted-foreground/40 group-hover:border-gold")}>
                    {rituals[r.id] && <Check className="h-3 w-3 text-white" />}
                  </span>
                  <span className={cn("text-sm", rituals[r.id] && "line-through text-muted-foreground")}>{r.label}</span>
                </button>
              ))}
            </div>
          </GlassCard>
        </div>

        <GlassCard glow="gold">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-4 w-4 text-gold" />
            <h2 className="font-serif text-lg font-medium">Signaux anti-surcharge</h2>
          </div>
          <div className="space-y-2.5">
            {wellbeing.signals.map((s) => (
              <div key={s.id} className={cn("rounded-xl border p-3 text-sm", signalTone[s.tone])}>{s.text}</div>
            ))}
          </div>
          <div className="mt-4 rounded-xl bg-teal-500/5 border border-teal-500/20 p-3 flex items-center gap-3">
            <Wind className="h-5 w-5 text-teal-400 shrink-0" />
            <div>
              <p className="text-sm font-medium text-teal-300">Respiration guidée</p>
              <p className="text-xs text-muted-foreground">2 min · cohérence cardiaque</p>
            </div>
          </div>
        </GlassCard>
      </div>

      <GlassCard className="mt-4">
        <h2 className="font-serif text-lg font-medium mb-2">Humeur de la semaine</h2>
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%" minHeight={180}>
            <BarChart data={wellbeing.moodWeek} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
              <XAxis dataKey="jour" {...chartAxis} className="text-muted-foreground" />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(148,163,184,0.08)" }} />
              <Bar dataKey="humeur" radius={[6, 6, 0, 0]}>
                {wellbeing.moodWeek.map((m, i) => <Cell key={i} fill={moodColors[m.humeur - 1]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>
    </div>
  );
}
