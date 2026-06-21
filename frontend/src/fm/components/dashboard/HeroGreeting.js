import React, { useEffect, useState } from "react";
import { useI18n } from "@fm/context/I18nContext";
import { quoteApi } from "@fm/lib/api";

/**
 * HeroGreeting v3 — image en haut + greeting + citation seulement.
 * (Suppression des KPI chips selon mockup utilisateur.)
 */
export default function HeroGreeting({ name = "Julien", quote: quoteProp }) {
  const { t } = useI18n();
  const [fetchedQuote, setFetchedQuote] = useState(null);
  const quote = quoteProp || fetchedQuote;

  useEffect(() => {
    if (!quoteProp) quoteApi.today().then(setFetchedQuote).catch(() => {});
  }, [quoteProp]);

  return (
    <section className="relative mb-6 rise" data-testid="hero-greeting">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-end">
        {/* Greeting */}
        <div className="md:col-span-7">
          <div className="text-[10.5px] tracking-[0.24em] uppercase font-semibold mb-2" style={{ color: "#b89855" }}>
            {new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" })}
          </div>
          <h1
            className="font-display text-[34px] sm:text-[42px] lg:text-[48px] leading-[1.05]"
            style={{ color: "#1a3a6e", letterSpacing: "-0.035em", fontWeight: 600 }}
            data-testid="hero-greeting-name"
          >
            Bonjour, <span className="font-serif-italic" style={{ color: "#b89855" }}>{name}.</span>
          </h1>
        </div>

        {/* Citation */}
        <div className="md:col-span-5 flex flex-col items-start md:items-end text-left md:text-right">
          <div className="relative max-w-[340px]">
            <span aria-hidden className="absolute -inset-x-6 -inset-y-3 rounded-[28px] citation-glow" />
            <p className="relative font-serif-italic text-[17px] md:text-[19px] leading-[1.3]"
               style={{ color: "#9c7d40" }}>
              {quote ? `« ${quote.text || quote.content || quote.quote || ""} »` : t("hero.citation")}
            </p>
            <p className="relative mt-2 text-[10px] tracking-[0.26em] uppercase font-semibold" style={{ color: "#6b6358" }}>
              — {quote ? (quote.author?.trim() || quote.ref?.trim() || quote.source?.trim() || t("hero.citationLabel")) : t("hero.citationLabel")}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
