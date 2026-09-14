import React from "react";
import { Layers, CalendarClock, Star, Info, ArrowRight } from "lucide-react";
import { GlassCard } from "@/components/common/GlassCard";
import { PageHeader } from "@/components/common/PageHeader";
import { contexte } from "@/data/mock";
import { cn } from "@/lib/utils";

const tone = {
  rose: "text-rose-400 bg-rose-500/10 border-rose-500/25",
  gold: "text-gold bg-gold/10 border-gold/25",
  cyan: "text-cyan-400 bg-cyan-500/10 border-cyan-500/25",
};
const impactColor = { "Élevé": "text-rose-400 bg-rose-500/10", "Moyen": "text-gold bg-gold/10", "Faible": "text-cyan-400 bg-cyan-500/10" };

export default function Contexte() {
  return (
    <div data-testid="contexte-page">
      <PageHeader
        icon={Layers}
        title="Contexte"
        subtitle="Une vue agrégée de tout ce qui compte maintenant : échéances, priorités et infos utiles."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <GlassCard glow="gold">
          <div className="flex items-center gap-2 mb-4">
            <CalendarClock className="h-4 w-4 text-gold" />
            <h2 className="font-serif text-lg font-medium">Échéances</h2>
          </div>
          <div className="space-y-2.5">
            {contexte.echeances.map((e) => (
              <div key={e.id} className={cn("flex items-center justify-between rounded-xl border p-3", tone[e.tone])}>
                <span className="text-sm text-foreground">{e.label}</span>
                <span className="text-xs font-medium">{e.date}</span>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard glow="emerald">
          <div className="flex items-center gap-2 mb-4">
            <Star className="h-4 w-4 text-gold" />
            <h2 className="font-serif text-lg font-medium">Priorités</h2>
          </div>
          <div className="space-y-2.5">
            {contexte.priorites.map((p, i) => (
              <div key={p.id} className="flex items-center gap-3 rounded-xl bg-secondary/40 border border-border/60 p-3">
                <span className="h-6 w-6 shrink-0 grid place-items-center rounded-full bg-gold/15 text-gold text-xs font-semibold">{i + 1}</span>
                <span className="text-sm flex-1">{p.label}</span>
                <span className={cn("text-[11px] rounded-full px-2 py-0.5", impactColor[p.impact])}>{p.impact}</span>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard>
          <div className="flex items-center gap-2 mb-4">
            <Info className="h-4 w-4 text-cyan-400" />
            <h2 className="font-serif text-lg font-medium">Infos utiles</h2>
          </div>
          <div className="space-y-2.5">
            {contexte.infos.map((info) => (
              <div key={info.id} className="flex items-start gap-2.5 rounded-xl bg-cyan-500/5 border border-cyan-500/15 p-3">
                <ArrowRight className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
                <span className="text-sm text-muted-foreground">{info.label}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
