import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer,
} from "recharts";
import { Target, PieChart, Map, Compass, Image as ImageIcon, LayoutGrid } from "lucide-react";
import { GlassCard } from "@/components/common/GlassCard";
import { PageHeader } from "@/components/common/PageHeader";
import { balanceWheel, roadmapQuarters, vision, moodboard } from "@/data/mock";
import { cn } from "@/lib/utils";

const moodImages = [
  "https://images.unsplash.com/photo-1547104442-991cb31eaafd?crop=entropy&cs=srgb&fm=jpg&w=600&q=80",
  "https://images.unsplash.com/photo-1655657874630-2da5679ef515?crop=entropy&cs=srgb&fm=jpg&w=600&q=80",
  "https://images.unsplash.com/photo-1779120388138-6ccf9c7bc5b0?crop=entropy&cs=srgb&fm=jpg&w=600&q=80",
  "https://images.unsplash.com/photo-1784035038826-0f2b55048ca7?crop=entropy&cs=srgb&fm=jpg&w=600&q=80",
  "https://images.unsplash.com/photo-1659607907257-74a21ff75685?crop=entropy&cs=srgb&fm=jpg&w=600&q=80",
  "https://images.unsplash.com/photo-1625487658552-9bf92afde9d0?crop=entropy&cs=srgb&fm=jpg&w=600&q=80",
];

const templates = [
  { id: "roue", label: "Roue de l'équilibre", icon: PieChart },
  { id: "roadmap", label: "Roadmap Q1→Q4", icon: Map },
  { id: "identite", label: "Modèle identitaire", icon: Compass },
  { id: "moodboard", label: "Moodboard émotionnel", icon: ImageIcon },
  { id: "cockpit", label: "Cockpit stratégique", icon: LayoutGrid },
];

export default function VisionBoard() {
  const [active, setActive] = useState("roue");

  return (
    <div data-testid="vision-board-page">
      <PageHeader
        icon={Target}
        title="Vision Board"
        subtitle="5 modèles pour projeter votre futur. Choisissez la lentille qui vous inspire aujourd'hui."
      />

      <div className="flex flex-wrap gap-2 mb-5">
        {templates.map((t) => (
          <button
            key={t.id}
            data-testid={`board-tab-${t.id}`}
            onClick={() => setActive(t.id)}
            className={cn(
              "flex items-center gap-2 rounded-full px-4 py-2 text-sm border transition-colors",
              active === t.id ? "bg-gold/12 text-gold border-gold/40" : "bg-secondary/40 text-muted-foreground border-border/60 hover:text-foreground"
            )}
          >
            <t.icon className="h-4 w-4" /> {t.label}
          </button>
        ))}
      </div>

      <motion.div key={active} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
        {active === "roue" && (
          <GlassCard hover={false}>
            <h2 className="font-serif text-lg font-medium mb-2">Roue de l'équilibre</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%" minHeight={280}>
                <RadarChart data={balanceWheel} outerRadius="72%">
                  <PolarGrid stroke="rgba(148,163,184,0.2)" />
                  <PolarAngleAxis dataKey="domaine" tick={{ fontSize: 12, fill: "currentColor" }} className="text-muted-foreground" />
                  <PolarRadiusAxis domain={[0, 10]} tick={false} axisLine={false} />
                  <Radar dataKey="score" stroke="#D4AF37" fill="#D4AF37" fillOpacity={0.35} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </GlassCard>
        )}

        {active === "roadmap" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            {roadmapQuarters.map((q, i) => (
              <GlassCard key={q.q} delay={i * 0.06}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="font-serif text-2xl font-semibold text-gold">{q.q}</span>
                  <span className="text-sm text-muted-foreground">{q.theme}</span>
                </div>
                <ul className="space-y-2">
                  {q.items.map((it, j) => (
                    <li key={j} className="text-sm flex items-start gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-gold shrink-0" />
                      {it}
                    </li>
                  ))}
                </ul>
              </GlassCard>
            ))}
          </div>
        )}

        {active === "identite" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <GlassCard><h3 className="font-serif text-lg mb-2 text-gold">Vision</h3><p className="text-sm text-muted-foreground leading-relaxed">{vision.vision}</p></GlassCard>
            <GlassCard><h3 className="font-serif text-lg mb-2 text-emerald-400">Mission</h3><p className="text-sm text-muted-foreground leading-relaxed">{vision.mission}</p></GlassCard>
            <GlassCard><h3 className="font-serif text-lg mb-3 text-cyan-400">Valeurs</h3><div className="flex flex-wrap gap-2">{vision.values.map((v) => <span key={v} className="text-xs rounded-full px-3 py-1 bg-gold/10 text-gold border border-gold/25">{v}</span>)}</div></GlassCard>
          </div>
        )}

        {active === "moodboard" && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {moodboard.map((m, i) => (
              <motion.div key={m.id} initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }} className="relative rounded-2xl overflow-hidden aspect-[4/5] group border border-border/60">
                {moodImages[i]?.startsWith("http") ? (
                  <img src={moodImages[i]} alt={m.label} className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
                ) : (
                  <div className="h-full w-full bg-gradient-to-br from-gold/20 to-emerald-500/20 grid place-items-center"><ImageIcon className="h-8 w-8 text-gold/50" /></div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
                <span className="absolute bottom-3 left-3 text-white font-serif text-sm">{m.label}</span>
              </motion.div>
            ))}
          </div>
        )}

        {active === "cockpit" && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { l: "North Star", v: "1 000 solopreneurs", c: "text-gold" },
              { l: "Palier 12 mois", v: "18 k€ MRR", c: "text-emerald-400" },
              { l: "Focus trimestre", v: "Offre signature", c: "text-cyan-400" },
              { l: "Énergie cible", v: "80 / 100", c: "text-rose-400" },
            ].map((k, i) => (
              <GlassCard key={k.l} delay={i * 0.05} className="text-center">
                <p className="text-xs text-muted-foreground">{k.l}</p>
                <p className={cn("font-serif text-xl font-semibold mt-2", k.c)}>{k.v}</p>
              </GlassCard>
            ))}
            <GlassCard className="col-span-2 lg:col-span-4">
              <h3 className="font-serif text-lg mb-2">Le cap en une phrase</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Bâtir un studio de conseil solo aligné et serein, aidant 1 000 indépendants, tout en préservant liberté et énergie.
              </p>
            </GlassCard>
          </div>
        )}
      </motion.div>
    </div>
  );
}
