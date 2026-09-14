import React, { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, Tooltip,
  AreaChart, Area, LineChart, Line,
} from "recharts";
import {
  ArrowUpRight, ArrowDownRight, Check, Sparkles, Mail, CheckCircle2,
  AlertTriangle, Clock, BookOpen, ChevronLeft, ChevronRight, Zap, CircleDot,
} from "lucide-react";
import { toast } from "sonner";
import { GlassCard } from "@/components/common/GlassCard";
import { Gauge } from "@/components/common/Gauge";
import { useApp } from "@/context/AppContext";
import {
  user, inspirations, kpis, trajectory, alignmentScore, prospectsDonut,
  prospects12m, copilote, recentActivity, deliverables as mockDeliverables,
  dayProgram, weekEnergy, readingList,
} from "@/data/mock";
import { cn } from "@/lib/utils";

const accentColor = {
  gold: "#D4AF37", emerald: "#10B981", cyan: "#06B6D4", rose: "#F43F5E",
};

const activityIcon = { check: CheckCircle2, mail: Mail, sparkles: Sparkles, alert: AlertTriangle };
const toneColor = {
  emerald: "text-emerald-400 bg-emerald-500/10", cyan: "text-cyan-400 bg-cyan-500/10",
  gold: "text-gold bg-gold/10", rose: "text-rose-400 bg-rose-500/10",
};

function KpiCard({ kpi, index }) {
  const color = accentColor[kpi.accent];
  const up = kpi.trend === "up";
  return (
    <GlassCard
      delay={index * 0.06}
      glow={kpi.accent === "emerald" ? "emerald" : "gold"}
      data-testid={`kpi-card-${kpi.key}`}
      className="group"
    >
      <div className="flex items-start justify-between">
        <span className="text-sm text-muted-foreground">{kpi.label}</span>
        <span
          className={cn(
            "flex items-center gap-0.5 text-xs font-medium rounded-full px-2 py-0.5",
            up ? "text-emerald-400 bg-emerald-500/10" : "text-rose-400 bg-rose-500/10"
          )}
        >
          {up ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
          {kpi.delta}
        </span>
      </div>
      <p className="mt-2 font-serif text-3xl font-semibold tracking-tight">{kpi.value}</p>
      <div className="h-10 mt-2 -mx-1">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={kpi.spark} margin={{ top: 4, bottom: 0, left: 0, right: 0 }}>
            <defs>
              <linearGradient id={`g-${kpi.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.5} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area type="monotone" dataKey="y" stroke={color} strokeWidth={2} fill={`url(#g-${kpi.id})`} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </GlassCard>
  );
}

export default function Cockpit() {
  const { ambiance } = useApp();
  const [slide, setSlide] = useState(0);
  const [tasks, setTasks] = useState(() =>
    Object.fromEntries(trajectory.flatMap((h) => h.tasks.map((t) => [t.id, t.done])))
  );
  const [deliverables, setDeliverables] = useState(mockDeliverables);
  const [program, setProgram] = useState(() => Object.fromEntries(dayProgram.map((p) => [p.id, p.done])));

  const insp = inspirations[slide % inspirations.length];
  const totalProspects = useMemo(() => prospectsDonut.reduce((a, b) => a + b.value, 0), []);

  const toggleTask = (id) => setTasks((s) => ({ ...s, [id]: !s[id] }));
  const toggleProgram = (id) => setProgram((s) => ({ ...s, [id]: !s[id] }));

  const actOnDeliverable = (id, accept) => {
    setDeliverables((list) => list.filter((d) => d.id !== id));
    toast[accept ? "success" : "message"](accept ? "Livrable validé ✅" : "Livrable rejeté", {
      description: accept ? "Le Copilote programmera l'action." : "Le Copilote proposera une nouvelle version.",
    });
  };

  return (
    <div className="space-y-6" data-testid="cockpit-page">
      {/* Greeting */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">
            {new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" })}
          </p>
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight mt-1">
            Bonjour <span className="gold-gradient-text">{user.firstName}</span>
          </h1>
        </div>
        <GlassCard hover={false} className="flex items-center gap-4 !py-3 !px-5" delay={0.1}>
          <div className="relative">
            <Gauge value={user.energyToday} size={64} stroke={7} label={`${user.energyToday}`} color={accentColor.gold} />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Énergie du jour</p>
            <p className="font-serif text-lg font-medium">
              {user.energyToday >= 75 ? "Belle forme" : "Rythme modéré"}
            </p>
          </div>
        </GlassCard>
      </div>

      {/* Inspiration */}
      <GlassCard delay={0.12} className="overflow-hidden">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="h-9 w-9 shrink-0 rounded-lg grid place-items-center bg-gold/10 text-gold border border-gold/25">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-[0.18em] text-gold/80 mb-1">Inspiration du jour</p>
              <motion.p key={insp.id} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} className="font-serif text-lg sm:text-xl leading-snug">
                « {insp.quote} »
              </motion.p>
              <p className="text-sm text-muted-foreground mt-1">— {insp.author}</p>
            </div>
          </div>
          <div className="flex gap-1.5 shrink-0">
            <button data-testid="inspiration-prev" onClick={() => setSlide((s) => (s - 1 + inspirations.length) % inspirations.length)} className="h-8 w-8 grid place-items-center rounded-full hover:bg-secondary transition-colors">
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button data-testid="inspiration-next" onClick={() => setSlide((s) => s + 1)} className="h-8 w-8 grid place-items-center rounded-full hover:bg-secondary transition-colors">
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </GlassCard>

      {/* KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {kpis.map((k, i) => <KpiCard key={k.id} kpi={k} index={i} />)}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Trajectory */}
        <GlassCard delay={0.15} className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-serif text-xl font-medium">Ma Trajectoire</h2>
            <span className="text-xs text-muted-foreground">Aujourd'hui → 3 ans</span>
          </div>
          <div className="relative pl-4">
            <div className="absolute left-[6px] top-1 bottom-1 w-px bg-gradient-to-b from-gold via-emerald-500/50 to-transparent" />
            <div className="space-y-5">
              {trajectory.map((h) => (
                <div key={h.id} className="relative">
                  <span className="absolute -left-[13px] top-1 h-3 w-3 rounded-full bg-gold ring-4 ring-gold/15" />
                  <div className="flex items-baseline gap-2">
                    <span className="text-xs font-semibold text-gold uppercase tracking-wide">{h.horizon}</span>
                    <span className="text-sm font-medium">{h.title}</span>
                  </div>
                  <div className="mt-2 space-y-1.5">
                    {h.tasks.map((t) => (
                      <button
                        key={t.id}
                        data-testid={`trajectory-task-${t.id}`}
                        onClick={() => toggleTask(t.id)}
                        className="flex items-center gap-2.5 text-left w-full group"
                      >
                        <span className={cn(
                          "h-4 w-4 shrink-0 rounded-[5px] border grid place-items-center transition-colors",
                          tasks[t.id] ? "bg-emerald-500 border-emerald-500" : "border-muted-foreground/40 group-hover:border-gold"
                        )}>
                          {tasks[t.id] && <Check className="h-3 w-3 text-white" />}
                        </span>
                        <span className={cn("text-sm transition-colors", tasks[t.id] ? "text-muted-foreground line-through" : "")}>
                          {t.label}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </GlassCard>

        {/* Alignment gauge + copilote */}
        <div className="space-y-4">
          <GlassCard delay={0.18} className="flex flex-col items-center text-center">
            <h2 className="font-serif text-lg font-medium mb-2 self-start">Score d'alignement</h2>
            <Gauge value={alignmentScore} size={150} label={`${alignmentScore}%`} sublabel="alignée à ta vision" color={accentColor.emerald} />
            <p className="text-xs text-muted-foreground mt-3">Tes actions reflètent tes valeurs. Continue ainsi.</p>
          </GlassCard>

          <GlassCard delay={0.2} glow="emerald">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="h-4 w-4 text-gold" />
              <h2 className="font-serif text-lg font-medium">Co-pilote</h2>
            </div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">Travail réalisé avec l'IA</span>
              <span className="font-serif text-2xl font-semibold text-gold">{copilote.aiWorkPercent}%</span>
            </div>
            <div className="h-1.5 rounded-full bg-secondary overflow-hidden mb-4">
              <motion.div initial={{ width: 0 }} animate={{ width: `${copilote.aiWorkPercent}%` }} transition={{ duration: 1 }} className="h-full bg-gradient-to-r from-gold to-emerald-400" />
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              {[
                { l: "En attente", v: copilote.pending, c: "text-gold" },
                { l: "Validés", v: copilote.validated, c: "text-emerald-400" },
                { l: "Temps gagné", v: `${copilote.timeSavedHours}h`, c: "text-cyan-400" },
              ].map((s) => (
                <div key={s.l} className="rounded-xl bg-secondary/50 py-2">
                  <p className={cn("font-serif text-lg font-semibold", s.c)}>{s.v}</p>
                  <p className="text-[11px] text-muted-foreground">{s.l}</p>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <GlassCard delay={0.15}>
          <h2 className="font-serif text-lg font-medium mb-2">Répartition prospects</h2>
          <div className="relative h-52">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={prospectsDonut} dataKey="value" nameKey="name" innerRadius={55} outerRadius={80} paddingAngle={3} stroke="none">
                  {prospectsDonut.map((e) => <Cell key={e.name} fill={e.color} />)}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 grid place-items-center pointer-events-none">
              <div className="text-center">
                <p className="font-serif text-2xl font-semibold">{totalProspects}</p>
                <p className="text-xs text-muted-foreground">prospects</p>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-1.5 mt-2">
            {prospectsDonut.map((p) => (
              <div key={p.name} className="flex items-center gap-2 text-xs">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: p.color }} />
                <span className="text-muted-foreground">{p.name}</span>
                <span className="ml-auto font-medium">{p.value}</span>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard delay={0.18} className="lg:col-span-2">
          <h2 className="font-serif text-lg font-medium mb-2">Prospects sur 12 mois</h2>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={prospects12m} margin={{ top: 8, right: 4, left: -18, bottom: 0 }}>
                <XAxis dataKey="mois" tick={{ fontSize: 11, fill: "currentColor" }} tickLine={false} axisLine={false} className="text-muted-foreground" />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(148,163,184,0.08)" }} />
                <Bar dataKey="nouveaux" stackId="a" fill="#06B6D4" radius={[0, 0, 0, 0]} />
                <Bar dataKey="gagnes" stackId="a" fill="#D4AF37" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 text-xs mt-1">
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-cyan-500" />Nouveaux</span>
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-gold" />Gagnés</span>
          </div>
        </GlassCard>
      </div>

      {/* Lower grid: activity / deliverables / program / energy / reading */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Deliverables to validate */}
        <GlassCard delay={0.15} className="lg:col-span-2" glow="gold">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-serif text-xl font-medium">Livrables IA à valider</h2>
            <span className="text-xs rounded-full bg-gold/10 text-gold px-2.5 py-1">{deliverables.length} en attente</span>
          </div>
          <div className="space-y-3">
            {deliverables.length === 0 && (
              <p className="text-sm text-muted-foreground py-6 text-center">Tout est validé. Le Copilote reprend le relais 🎯</p>
            )}
            {deliverables.map((d) => (
              <motion.div
                key={d.id}
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="rounded-xl border border-border/60 bg-secondary/30 p-3.5"
                data-testid={`deliverable-${d.id}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{d.title}</span>
                      <span className="text-[10px] rounded bg-background/70 border border-border/60 px-1.5 py-0.5 text-muted-foreground">{d.type}</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{d.preview}</p>
                  </div>
                  <span className="shrink-0 text-xs text-emerald-400">{d.confidence}%</span>
                </div>
                <div className="flex gap-2 mt-3">
                  <button data-testid={`deliverable-accept-${d.id}`} onClick={() => actOnDeliverable(d.id, true)} className="flex-1 rounded-lg bg-emerald-500/15 text-emerald-400 text-sm py-1.5 hover:bg-emerald-500/25 transition-colors font-medium">
                    Valider
                  </button>
                  <button data-testid={`deliverable-reject-${d.id}`} onClick={() => actOnDeliverable(d.id, false)} className="flex-1 rounded-lg bg-secondary text-muted-foreground text-sm py-1.5 hover:bg-rose-500/15 hover:text-rose-400 transition-colors font-medium">
                    Rejeter
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </GlassCard>

        {/* Recent activity */}
        <GlassCard delay={0.18}>
          <h2 className="font-serif text-lg font-medium mb-4">Activité récente</h2>
          <div className="space-y-3.5">
            {recentActivity.map((a) => {
              const Icon = activityIcon[a.icon];
              return (
                <div key={a.id} className="flex items-start gap-3">
                  <span className={cn("h-8 w-8 shrink-0 rounded-lg grid place-items-center", toneColor[a.tone])}>
                    <Icon className="h-4 w-4" />
                  </span>
                  <div>
                    <p className="text-sm leading-snug">{a.label}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{a.time}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Program */}
        <GlassCard delay={0.15}>
          <h2 className="font-serif text-lg font-medium mb-4">Programme du jour</h2>
          <div className="space-y-2.5">
            {dayProgram.map((p) => (
              <button key={p.id} data-testid={`program-${p.id}`} onClick={() => toggleProgram(p.id)} className="w-full flex items-center gap-3 text-left group">
                <span className="text-xs tabular-nums text-muted-foreground w-11">{p.time}</span>
                <span className={cn("h-4 w-4 shrink-0 rounded-full border grid place-items-center transition-colors", program[p.id] ? "bg-emerald-500 border-emerald-500" : "border-muted-foreground/40 group-hover:border-gold")}>
                  {program[p.id] && <Check className="h-2.5 w-2.5 text-white" />}
                </span>
                <span className={cn("text-sm flex-1", program[p.id] && "line-through text-muted-foreground")}>{p.label}</span>
                <span className="text-[10px] rounded-full bg-secondary px-2 py-0.5 text-muted-foreground">{p.tag}</span>
              </button>
            ))}
          </div>
        </GlassCard>

        {/* Energy week */}
        <GlassCard delay={0.18}>
          <h2 className="font-serif text-lg font-medium mb-2">Énergie de la semaine</h2>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weekEnergy} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
                <XAxis dataKey="jour" tick={{ fontSize: 11, fill: "currentColor" }} tickLine={false} axisLine={false} className="text-muted-foreground" />
                <Tooltip contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="energie" stroke="#10B981" strokeWidth={2.5} dot={{ r: 3, fill: "#10B981" }} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Reading */}
        <GlassCard delay={0.2}>
          <div className="flex items-center gap-2 mb-4">
            <BookOpen className="h-4 w-4 text-gold" />
            <h2 className="font-serif text-lg font-medium">À lire</h2>
          </div>
          <div className="space-y-3">
            {readingList.map((r) => (
              <div key={r.id} className="flex items-center gap-3 rounded-xl bg-secondary/30 p-2.5">
                <span className="h-9 w-9 shrink-0 rounded-lg bg-gold/10 text-gold grid place-items-center"><BookOpen className="h-4 w-4" /></span>
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{r.title}</p>
                  <p className="text-xs text-muted-foreground">{r.author} · {r.minutes} min</p>
                </div>
                <span className="ml-auto text-[10px] rounded-full bg-background/70 border border-border/60 px-2 py-0.5 text-muted-foreground shrink-0">{r.tag}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}

const tooltipStyle = {
  background: "rgba(10,18,40,0.95)",
  border: "1px solid rgba(212,175,55,0.25)",
  borderRadius: 12,
  color: "#F8FAFC",
  fontSize: 12,
};
