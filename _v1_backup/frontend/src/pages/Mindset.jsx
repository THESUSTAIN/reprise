import React, { useState } from "react";
import { motion } from "framer-motion";
import { Brain, Check, GitBranch, X } from "lucide-react";
import { toast } from "sonner";
import { GlassCard } from "@/components/common/GlassCard";
import { PageHeader } from "@/components/common/PageHeader";
import { mindsetDecisions } from "@/data/mock";
import { cn } from "@/lib/utils";

const options = [
  { key: "accepter", label: "Accepter", icon: Check, color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30 hover:bg-emerald-500/20" },
  { key: "pivoter", label: "Pivoter", icon: GitBranch, color: "text-gold bg-gold/10 border-gold/30 hover:bg-gold/20" },
  { key: "refuser", label: "Refuser", icon: X, color: "text-rose-400 bg-rose-500/10 border-rose-500/30 hover:bg-rose-500/20" },
];

export default function Mindset() {
  const [decisions, setDecisions] = useState(() => Object.fromEntries(mindsetDecisions.map((d) => [d.id, null])));

  const decide = (id, choice) => {
    setDecisions((s) => ({ ...s, [id]: choice }));
    toast.success(`Décision enregistrée : ${choice}`);
  };

  return (
    <div data-testid="mindset-page">
      <PageHeader
        icon={Brain}
        title="Mindset"
        subtitle="Un espace de recul. Le Copilote suggère, vous tranchez : accepter, pivoter ou refuser."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {mindsetDecisions.map((d, i) => {
          const chosen = decisions[d.id];
          return (
            <GlassCard key={d.id} delay={i * 0.06} glow="gold" data-testid={`decision-${d.id}`}>
              <h2 className="font-serif text-lg font-medium leading-snug">{d.title}</h2>
              <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{d.context}</p>

              <div className="mt-3 rounded-xl bg-secondary/40 border border-border/60 p-3">
                <p className="text-[11px] uppercase tracking-wide text-gold/80 mb-1">Suggestion du Copilote</p>
                <p className="text-sm">
                  <span className="capitalize font-medium">{d.suggestion}</span> — {d.note}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2 mt-4">
                {options.map((o) => (
                  <button
                    key={o.key}
                    data-testid={`decision-${d.id}-${o.key}`}
                    onClick={() => decide(d.id, o.key)}
                    className={cn(
                      "flex flex-col items-center gap-1 rounded-xl border py-2.5 text-xs font-medium transition-colors",
                      o.color,
                      chosen && chosen !== o.key && "opacity-40"
                    )}
                  >
                    <o.icon className="h-4 w-4" />
                    {o.label}
                  </button>
                ))}
              </div>

              {chosen && (
                <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-xs text-center text-muted-foreground mt-3">
                  Tu as choisi de <span className="font-medium text-foreground capitalize">{chosen}</span>.
                </motion.p>
              )}
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}
