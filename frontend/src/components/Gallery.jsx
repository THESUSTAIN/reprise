import React, { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { useApp } from "@/context/AppContext";
import { templates } from "@/data/templates";
import { TemplateCard } from "@/components/TemplateCard";

const FILTERS = ["all", "holistic", "planning", "mindset", "artistic", "strategic"];

export const Gallery = React.forwardRef(({ onOpen }, ref) => {
  const { t } = useApp();
  const [filter, setFilter] = useState("all");

  const list = useMemo(
    () => (filter === "all" ? templates : templates.filter((tp) => tp.category === filter)),
    [filter]
  );

  return (
    <section ref={ref} className="relative mx-auto max-w-7xl px-4 sm:px-6 py-16 sm:py-24">
      <div className="max-w-2xl">
        <span className="font-mono-accent text-xs uppercase tracking-[0.24em] text-[hsl(var(--clay))]">
          {t("section_eyebrow")}
        </span>
        <h2 className="mt-3 font-display text-2xl font-bold tracking-tight sm:text-3xl lg:text-4xl">
          {t("section_title")}
        </h2>
        <p className="mt-3 text-muted-foreground">{t("section_sub")}</p>
      </div>

      <div className="mt-8 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            data-testid={`filter-tab-${f}`}
            onClick={() => setFilter(f)}
            className={`rounded-full border px-4 py-2 text-sm font-medium transition-all ${
              filter === f
                ? "border-transparent bg-foreground text-background"
                : "border-border bg-card/60 hover:bg-secondary"
            }`}
          >
            {t(`filter_${f}`)}
          </button>
        ))}
      </div>

      <motion.div
        data-testid="templates-gallery-grid"
        key={filter}
        variants={{ hidden: {}, show: { transition: { staggerChildren: 0.08 } } }}
        initial="hidden"
        animate="show"
        className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4"
      >
        {list.map((tpl, i) => (
          <TemplateCard key={tpl.id} template={tpl} index={i} onOpen={onOpen} />
        ))}
      </motion.div>
    </section>
  );
});

Gallery.displayName = "Gallery";
