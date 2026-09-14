import React from "react";
import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import { useApp } from "@/context/AppContext";

export const RoadmapView = ({ template }) => {
  const { lang } = useApp();

  return (
    <div data-testid="roadmap-timeline-container" className="relative">
      <div className="grid gap-5 lg:grid-cols-4">
        {template.quarters.map((q, i) => (
          <motion.div
            key={q.q}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="relative rounded-2xl border border-border bg-card p-5"
          >
            <div className="mb-4 flex items-center gap-3">
              <span
                className="grid h-11 w-11 place-items-center rounded-xl font-mono-accent text-sm font-bold text-white"
                style={{ background: q.color }}
              >
                {q.q}
              </span>
              <div className="h-[3px] flex-1 rounded-full" style={{ background: `${q.color}33` }}>
                <div className="h-full rounded-full" style={{ width: `${100 - i * 22}%`, background: q.color }} />
              </div>
            </div>
            <h4 className="font-display text-lg font-bold leading-tight">{q.title[lang]}</h4>
            <p className="mt-1 text-sm text-muted-foreground">{q.focus[lang]}</p>
            <ul className="mt-4 space-y-2.5">
              {q.milestones[lang].map((m) => (
                <li key={m} className="flex items-start gap-2 text-sm">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" style={{ color: q.color }} />
                  {m}
                </li>
              ))}
            </ul>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
