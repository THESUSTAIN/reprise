import React from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { Wallet, TrendingUp, AlertTriangle, Sparkles, ArrowUpRight } from "lucide-react";
import { GlassCard } from "@/components/common/GlassCard";
import { PageHeader } from "@/components/common/PageHeader";
import { daf } from "@/data/mock";
import { tooltipStyle, chartAxis } from "@/components/common/chartTheme";
import { cn } from "@/lib/utils";

const alertTone = {
  rose: "border-rose-500/25 bg-rose-500/5 text-rose-400",
  gold: "border-gold/25 bg-gold/5 text-gold",
  emerald: "border-emerald-500/25 bg-emerald-500/5 text-emerald-400",
};
const statutColor = {
  "Payée": "text-emerald-400 bg-emerald-500/10",
  "En retard": "text-rose-400 bg-rose-500/10",
  "En attente": "text-gold bg-gold/10",
};

export default function Pilotage() {
  const metrics = [
    { label: "Trésorerie nette", value: `${daf.tresorerie.toLocaleString("fr-FR")} €`, sub: "+6% ce mois", icon: Wallet, color: "text-emerald-400" },
    { label: "Marge nette", value: `${daf.margeNette}%`, sub: "cible 55%", icon: TrendingUp, color: "text-gold" },
    { label: "Factures en retard", value: daf.facturesRetard, sub: "à relancer", icon: AlertTriangle, color: "text-rose-400" },
    { label: "Runway", value: `${daf.runwayMonths} mois`, sub: "de charges couvertes", icon: TrendingUp, color: "text-cyan-400" },
  ];

  return (
    <div data-testid="pilotage-page">
      <PageHeader
        icon={Wallet}
        title="Pilotage / DAF IA"
        subtitle="Votre directeur financier augmenté. Trésorerie, marge et alertes lues par l'IA."
      />

      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-4">
        {metrics.map((m, i) => (
          <GlassCard key={m.label} delay={i * 0.05}>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{m.label}</span>
              <m.icon className={cn("h-4 w-4", m.color)} />
            </div>
            <p className="font-serif text-2xl font-semibold mt-2">{m.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{m.sub}</p>
          </GlassCard>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <GlassCard className="lg:col-span-2">
          <h2 className="font-serif text-lg font-medium mb-3">Flux de trésorerie</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%" minHeight={200}>
              <AreaChart data={daf.cashflow} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                <defs>
                  <linearGradient id="entrees" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10B981" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#10B981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="sorties" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#F43F5E" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#F43F5E" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" vertical={false} />
                <XAxis dataKey="mois" {...chartAxis} className="text-muted-foreground" />
                <YAxis {...chartAxis} className="text-muted-foreground" width={38} tickFormatter={(v) => `${v / 1000}k`} />
                <Tooltip contentStyle={tooltipStyle} formatter={(v) => `${v.toLocaleString("fr-FR")} €`} />
                <Area type="monotone" dataKey="entrees" stroke="#10B981" strokeWidth={2} fill="url(#entrees)" name="Entrées" />
                <Area type="monotone" dataKey="sorties" stroke="#F43F5E" strokeWidth={2} fill="url(#sorties)" name="Sorties" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* AI reading */}
        <GlassCard glow="gold">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-4 w-4 text-gold" />
            <h2 className="font-serif text-lg font-medium">Lecture IA & alertes</h2>
          </div>
          <div className="space-y-2.5">
            {daf.alerts.map((a) => (
              <div key={a.id} className={cn("rounded-xl border p-3 text-sm", alertTone[a.tone])}>
                {a.text}
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
        {/* Invoices */}
        <GlassCard className="lg:col-span-2">
          <h2 className="font-serif text-lg font-medium mb-3">Factures</h2>
          <div className="space-y-1">
            {daf.invoices.map((inv) => (
              <div key={inv.id} className="flex items-center gap-3 py-2.5 border-b border-border/50 last:border-0">
                <span className="text-xs tabular-nums text-muted-foreground w-14">{inv.id}</span>
                <span className="text-sm flex-1 min-w-0 truncate">{inv.client}</span>
                <span className="text-xs text-muted-foreground hidden sm:block">{inv.echeance}</span>
                <span className="font-medium text-sm w-20 text-right">{inv.montant.toLocaleString("fr-FR")} €</span>
                <span className={cn("text-[11px] rounded-full px-2 py-0.5 w-20 text-center shrink-0", statutColor[inv.statut])}>{inv.statut}</span>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Goals */}
        <GlassCard glow="emerald">
          <h2 className="font-serif text-lg font-medium mb-4">Objectifs & jalons</h2>
          <div className="space-y-4">
            {daf.goals.map((g) => (
              <div key={g.id}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm">{g.label}</span>
                  <span className="text-xs font-medium text-gold">{g.progress}%</span>
                </div>
                <div className="h-2 rounded-full bg-secondary overflow-hidden">
                  <div className="h-full rounded-full bg-gradient-to-r from-gold to-emerald-400" style={{ width: `${g.progress}%` }} />
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
