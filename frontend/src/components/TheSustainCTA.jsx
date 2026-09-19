/* Section CTA finale (bleue pleine largeur) — calquée sur thesustain-app.vercel.app.
   Bouton blanc fond + texte bleu sur fond bleu plein. */
import React from "react";
import { Link } from "react-router-dom";
import { PARTNER as P } from "../pages/partners-theme";

export default function TheSustainCTA({
  title = "Prêt à rejoindre le réseau ?",
  description = "Rejoignez des centaines de prestataires chrétiens qui développent leur activité avec TheSustain.",
  buttonLabel = "Devenir partenaire",
  buttonTo = "/devenir-partenaire",
  testId = "thesustain-cta",
}) {
  return (
    <section className="py-20 md:py-24 text-center text-white"
             style={{
               background: P.BG_CTA,
               fontFamily: "'Inter', system-ui, sans-serif",
             }}
             data-testid={testId}>
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="font-bold mb-4"
            style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", lineHeight: 1.15 }}>
          {title}
        </h2>
        <p className="text-base md:text-lg text-white/85 mb-9 leading-relaxed">
          {description}
        </p>
        <Link to={buttonTo}
              data-testid={`${testId}-btn`}
              className="inline-flex items-center px-7 py-3.5 text-base font-bold transition hover:opacity-90"
              style={{ background: P.RED, color: "#fff", borderRadius: "8px" }}>
          {buttonLabel}
        </Link>
      </div>
    </section>
  );
}
