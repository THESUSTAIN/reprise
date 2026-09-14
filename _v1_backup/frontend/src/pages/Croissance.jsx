import React, { useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, Flame, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { GlassCard } from "@/components/common/GlassCard";
import { PageHeader } from "@/components/common/PageHeader";
import { pipeline as initialPipeline } from "@/data/mock";
import { cn } from "@/lib/utils";

const stages = ["Nouveaux", "Échange", "Proposition", "Négo", "Gagnés"];
const stageAccent = {
  Nouveaux: "text-cyan-400 border-cyan-500/30",
  "Échange": "text-indigo-400 border-indigo-500/30",
  Proposition: "text-gold border-gold/30",
  "Négo": "text-orange-400 border-orange-500/30",
  "Gagnés": "text-emerald-400 border-emerald-500/30",
};

const scoreColor = (s) => (s >= 85 ? "text-emerald-400 bg-emerald-500/10" : s >= 70 ? "text-gold bg-gold/10" : "text-cyan-400 bg-cyan-500/10");

export default function Croissance() {
  const [pipeline, setPipeline] = useState(initialPipeline);

  const advance = (stage, id) => {
    const idx = stages.indexOf(stage);
    if (idx >= stages.length - 1) return;
    const next = stages[idx + 1];
    setPipeline((p) => {
      const deal = p[stage].find((d) => d.id === id);
      return {
        ...p,
        [stage]: p[stage].filter((d) => d.id !== id),
        [next]: [...p[next], next === "Gagnés" ? { ...deal, score: 100 } : deal],
      };
    });
    toast.success(`Déplacé vers « ${next} »`);
  };

  const total = (stage) => pipeline[stage].reduce((a, d) => a + d.value, 0);
  const grandTotal = stages.reduce((a, s) => a + total(s), 0);

  return (
    <div data-testid="croissance-page">
      <PageHeader
        icon={TrendingUp}
        title="Croissance"
        subtitle="Votre pipeline commercial priorisé par scoring IA. Cliquez sur une carte pour la faire avancer."
        action={
          <div className="hidden sm:flex flex-col items-end">
            <span className="text-xs text-muted-foreground">Pipeline total</span>
            <span className="font-serif text-xl font-semibold text-gold">{grandTotal.toLocaleString("fr-FR")} €</span>
          </div>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-3">
        {stages.map((stage, si) => (
          <div key={stage} className="min-w-0">
            <div className="flex items-center justify-between mb-3 px-1">
              <span className={cn("text-sm font-medium rounded-full border px-2.5 py-0.5", stageAccent[stage])}>{stage}</span>
              <span className="text-xs text-muted-foreground">{pipeline[stage].length}</span>
            </div>
            <div className="space-y-2.5">
              {pipeline[stage].map((deal, i) => (
                <motion.button
                  key={deal.id}
                  layout
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: si * 0.03 + i * 0.03 }}
                  onClick={() => advance(stage, deal.id)}
                  data-testid={`pipeline-card-${deal.id}`}
                  className="w-full text-left glass !p-3.5 hover:-translate-y-0.5 hover:border-gold/40 transition-[transform,border-color] group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm font-medium">{deal.name}</span>
                    <span className={cn("text-[10px] font-semibold rounded-full px-1.5 py-0.5 shrink-0", scoreColor(deal.score))}>{deal.score}</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-0.5">{deal.tag}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="font-serif text-base font-semibold text-gold">{deal.value.toLocaleString("fr-FR")} €</span>
                    {stage !== "Gagnés" && (
                      <span className="text-[11px] text-muted-foreground flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                        avancer <ArrowRight className="h-3 w-3" />
                      </span>
                    )}
                  </div>
                </motion.button>
              ))}
              {pipeline[stage].length === 0 && (
                <div className="rounded-xl border border-dashed border-border/60 py-6 text-center text-xs text-muted-foreground">Vide</div>
              )}
            </div>
            <div className="mt-3 px-1 text-xs text-muted-foreground flex items-center gap-1.5">
              <Flame className="h-3 w-3 text-gold" /> {total(stage).toLocaleString("fr-FR")} €
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
