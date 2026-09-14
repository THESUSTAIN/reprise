import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Compass, Zap, Leaf, Target, Rocket, ShieldAlert, TrendingUp, Award, Heart,
} from "lucide-react";
import { GlassCard } from "@/components/common/GlassCard";
import { PageHeader } from "@/components/common/PageHeader";
import { Gauge } from "@/components/common/Gauge";
import { useApp } from "@/context/AppContext";
import { vision, swot, wins, alignmentScore } from "@/data/mock";
import { cn } from "@/lib/utils";

const swotConfig = [
  { key: "forces", label: "Forces", icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { key: "faiblesses", label: "Faiblesses", icon: ShieldAlert, color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/20" },
  { key: "opportunites", label: "Opportunités", icon: Rocket, color: "text-gold", bg: "bg-gold/10 border-gold/20" },
  { key: "menaces", label: "Menaces", icon: ShieldAlert, color: "text-orange-400", bg: "bg-orange-500/10 border-orange-500/20" },
];

export default function Vision() {
  const { ambiance, toggleAmbiance, faith } = useApp();
  const isRefuge = ambiance === "refuge";

  return (
    <div data-testid="vision-page">
      <PageHeader
        icon={Compass}
        title="Vision"
        subtitle="Votre boussole identitaire. Alignez vos actions avec ce qui compte vraiment."
        action={
          <button
            data-testid="vision-ambiance-toggle"
            onClick={toggleAmbiance}
            className={cn(
              "flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium border transition-colors",
              isRefuge ? "bg-teal-500/10 text-teal-400 border-teal-500/30" : "bg-gold/10 text-gold border-gold/30"
            )}
          >
            {isRefuge ? <Leaf className="h-4 w-4" /> : <Zap className="h-4 w-4" />}
            Mode {isRefuge ? "Refuge" : "Élan"}
          </button>
        }
      />

      <AnimatePresence mode="wait">
        <motion.div
          key={ambiance}
          initial={{ opacity: 0, scale: 0.99 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.99 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="space-y-4"
        >
          {/* Ambiance banner */}
          <div className={cn(
            "rounded-2xl p-5 border relative overflow-hidden",
            isRefuge
              ? "bg-gradient-to-r from-teal-500/10 via-indigo-500/10 to-transparent border-teal-500/20"
              : "bg-gradient-to-r from-gold/10 via-emerald-500/10 to-transparent border-gold/20"
          )}>
            <div className="flex items-center gap-3">
              {isRefuge ? <Leaf className="h-6 w-6 text-teal-400" /> : <Zap className="h-6 w-6 text-gold" />}
              <div>
                <h2 className="font-serif text-xl font-medium">{isRefuge ? "Mode Refuge" : "Mode Élan"}</h2>
                <p className="text-sm text-muted-foreground">
                  {isRefuge
                    ? "Respire. Reconnecte-toi à tes valeurs et célèbre le chemin parcouru."
                    : "Cap sur l'action. Ta vision devient un plan, chaque jour."}
                </p>
              </div>
            </div>
          </div>

          {/* Identity model */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {[
              { label: "Vision", text: vision.vision, icon: Compass },
              { label: "Mission", text: vision.mission, icon: Target },
              { label: "Valeurs", text: null, icon: Heart },
            ].map((b, i) => (
              <GlassCard key={b.label} delay={i * 0.06} glow={isRefuge ? "teal" : "gold"}>
                <div className="flex items-center gap-2 mb-2">
                  <b.icon className={cn("h-4 w-4", isRefuge ? "text-teal-400" : "text-gold")} />
                  <h3 className="font-serif text-lg font-medium">{b.label}</h3>
                </div>
                {b.text ? (
                  <p className="text-sm leading-relaxed text-muted-foreground">{b.text}</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {vision.values.map((v) => (
                      <span key={v} className={cn("text-xs rounded-full px-3 py-1 border", isRefuge ? "bg-teal-500/10 text-teal-300 border-teal-500/25" : "bg-gold/10 text-gold border-gold/25")}>{v}</span>
                    ))}
                  </div>
                )}
              </GlassCard>
            ))}
          </div>

          {/* Refuge extras vs Élan SWOT */}
          {isRefuge ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <GlassCard glow="teal" className="lg:col-span-2">
                <div className="flex items-center gap-2 mb-4">
                  <Award className="h-4 w-4 text-teal-400" />
                  <h3 className="font-serif text-lg font-medium">Tes réussites récentes</h3>
                </div>
                <div className="space-y-2.5">
                  {wins.map((w, i) => (
                    <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }} className="flex items-center gap-3 rounded-xl bg-teal-500/5 border border-teal-500/15 p-3">
                      <span className="h-8 w-8 shrink-0 rounded-lg grid place-items-center bg-teal-500/15 text-teal-400"><Award className="h-4 w-4" /></span>
                      <span className="text-sm">{w}</span>
                    </motion.div>
                  ))}
                </div>
              </GlassCard>
              <GlassCard glow="teal" className="flex flex-col items-center text-center justify-center">
                {faith ? (
                  <>
                    <Heart className="h-6 w-6 text-teal-400 mb-3" />
                    <p className="font-serif text-lg leading-snug">{vision.verse}</p>
                    <p className="text-xs text-muted-foreground mt-3">Ancrage · Faith-Toggle activé</p>
                  </>
                ) : (
                  <>
                    <Leaf className="h-6 w-6 text-teal-400 mb-3" />
                    <p className="font-serif text-lg leading-snug">« Tu as le droit de ralentir pour mieux avancer. »</p>
                    <p className="text-xs text-muted-foreground mt-3">Ancrage du jour</p>
                  </>
                )}
              </GlassCard>
            </div>
          ) : (
            <GlassCard glow="gold">
              <h3 className="font-serif text-lg font-medium mb-4">Analyse SWOT</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {swotConfig.map((s) => (
                  <div key={s.key} className={cn("rounded-xl p-4 border", s.bg)}>
                    <div className={cn("flex items-center gap-2 mb-2", s.color)}>
                      <s.icon className="h-4 w-4" />
                      <span className="font-medium text-sm">{s.label}</span>
                    </div>
                    <ul className="space-y-1.5">
                      {swot[s.key].map((item, i) => (
                        <li key={i} className="text-sm text-muted-foreground flex gap-2"><span className={s.color}>•</span>{item}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}

          {/* Alignment */}
          <GlassCard glow={isRefuge ? "teal" : "emerald"} className="flex flex-col sm:flex-row items-center gap-6">
            <Gauge value={alignmentScore} size={140} label={`${alignmentScore}%`} color={isRefuge ? "#14B8A6" : "#10B981"} />
            <div>
              <h3 className="font-serif text-xl font-medium mb-1">Score d'alignement</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                {alignmentScore}% de tes actions de la semaine servent directement ta vision. Un excellent niveau de cohérence — protège ce cap.
              </p>
            </div>
          </GlassCard>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
