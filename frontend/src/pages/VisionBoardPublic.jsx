import React from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Sparkles, ArrowRight, Check, BookOpen, TrendingUp, GitBranch } from "lucide-react";
import { PublicHeader, UnifiedFooter } from "@/pages/LandingHub";

/**
 * Page publique Vision Board — showcase des 3 templates pour conversion.
 * Affiche un aperçu iframe live de chaque template (magazine / trajectoire / arbre).
 *
 * SEO + meta synchronisés avec WP via /api/wp/page/vision-board (cache 30s).
 */

const TEMPLATES = [
  {
    id: "magazine",
    title: "Magazine éditorial",
    pitch: "Une couverture digne d'un mook. Vos valeurs, votre why, vos 10 ans projetés — en lecture longue.",
    benefits: ["Couverture full-width", "Mosaïque keywords + 6 piliers", "Quote du fondateur en double page", "Roadmap visuelle"],
    icon: BookOpen,
    color: "#b89855",
    bg: "#f3e9d0",
  },
  {
    id: "trajectoire",
    title: "Trajectoire 10 ans",
    pitch: "Votre projection temporelle : aujourd'hui → 1 an → 3 ans → 10 ans. Idéal pour les fondateurs ambitieux.",
    benefits: ["Timeline horizontale", "3 jalons clés", "KPIs cibles par étape", "Photo de vous dans 10 ans (IA)"],
    icon: TrendingUp,
    color: "#1a3a6e",
    bg: "rgba(26,58,110,0.08)",
  },
  {
    id: "arbre",
    title: "Arbre de vie",
    pitch: "Vos racines (valeurs), votre tronc (mission), vos branches (domaines). Une visualisation organique.",
    benefits: ["Racines = valeurs profondes", "Tronc = pourquoi central", "Branches = 5 domaines de vie", "Fruits = livrables visés"],
    icon: GitBranch,
    color: "#2D6A4F",
    bg: "rgba(45,106,79,0.1)",
  },
];

export default function VisionBoardPublic() {
  const previewBase = (import.meta.env.VITE_API_URL || "") + "/api/vision/board/preview-public?template=";

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#f6f3ee" }} data-testid="vb-public-page">
      <Helmet>
        <title>Vision Board IA · Donnez vie à votre vision — Zayado</title>
        <meta name="description" content="Créez votre Vision Board personnalisé en 5 minutes. 3 templates éditoriaux (Magazine, Trajectoire, Arbre de vie) générés par IA. Téléchargez en PDF flipbook ou partagez en ligne." />
        <meta property="og:title" content="Vision Board IA · Donnez vie à votre vision — Zayado" />
        <meta property="og:description" content="3 templates éditoriaux générés par IA. Magazine, Trajectoire, Arbre. PDF + flipbook + partage protégé." />
        <link rel="canonical" href="https://zayado.net/vision-board" />
      </Helmet>

      <PublicHeader />

      <main className="flex-1 max-w-6xl mx-auto px-6 lg:px-10 py-16">
        {/* Hero */}
        <section className="text-center mb-14">
          <div className="text-[11px] tracking-[0.22em] uppercase font-bold mb-3" style={{ color: "#b89855" }}>
            Vision Board IA · 3 templates
          </div>
          <h1 className="font-display text-[40px] sm:text-[56px] leading-[1.05] mb-5"
              style={{ color: "#1a3a6e", letterSpacing: "-0.03em", fontWeight: 600 }}>
            Donnez vie à <span className="font-serif-italic" style={{ color: "#b89855" }}>votre vision.</span>
          </h1>
          <p className="text-[16px] max-w-2xl mx-auto leading-relaxed mb-7" style={{ color: "#4a4538" }}>
            En 5 minutes, l'IA transforme vos réponses (mission, valeurs, projection 10 ans) en un Vision Board éditorial professionnel. Téléchargez-le en PDF flipbook ou partagez-le avec un lien protégé.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Link to="/?login=1" className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-[13.5px] font-semibold shadow-md transition"
                  style={{ background: "#1a3a6e", color: "#f6f3ee" }} data-testid="vb-cta-create">
              <Sparkles size={14} /> Créer mon Vision Board <ArrowRight size={13} />
            </Link>
            <a href="#templates" className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-[13.5px] font-medium transition"
               style={{ background: "transparent", color: "#1a3a6e", outline: "1.5px solid rgba(26,58,110,0.22)" }}>
              Voir les 3 templates
            </a>
          </div>
        </section>

        {/* Templates showcase avec iframe live */}
        <section id="templates" className="space-y-12">
          {TEMPLATES.map((t, idx) => {
            const Icon = t.icon;
            const reverse = idx % 2 === 1;
            return (
              <article
                key={t.id}
                className="rounded-3xl bg-white shadow-md hover:shadow-xl transition overflow-hidden"
                data-testid={`vb-template-${t.id}`}
              >
                <div className={`grid grid-cols-1 lg:grid-cols-12 gap-0 ${reverse ? "lg:flex-row-reverse" : ""}`}>
                  {/* Iframe preview live */}
                  <div className={`lg:col-span-7 ${reverse ? "lg:order-2" : ""}`}
                       style={{ background: t.bg, padding: "2rem", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <div className="relative w-full max-w-[640px] aspect-[1.41/1] rounded-2xl overflow-hidden shadow-2xl"
                         style={{ background: "white" }}>
                      <iframe
                        src={previewBase + t.id}
                        title={`Aperçu ${t.title}`}
                        loading="lazy"
                        className="w-full h-full border-0 pointer-events-none"
                        style={{ transform: "scale(0.75)", transformOrigin: "top left", width: "133.33%", height: "133.33%" }}
                        data-testid={`vb-iframe-${t.id}`}
                      />
                      <span className="absolute top-3 right-3 px-2.5 py-1 rounded-full text-[9.5px] font-bold tracking-[0.14em] uppercase shadow-md"
                            style={{ background: "white", color: t.color }}>
                        Aperçu live
                      </span>
                    </div>
                  </div>

                  {/* Texte */}
                  <div className={`lg:col-span-5 p-8 lg:p-10 flex flex-col justify-center ${reverse ? "lg:order-1" : ""}`}>
                    <div className="w-12 h-12 rounded-2xl grid place-items-center mb-4"
                         style={{ background: t.bg, color: t.color }}>
                      <Icon size={20} />
                    </div>
                    <div className="text-[10.5px] tracking-[0.22em] uppercase font-bold mb-2" style={{ color: t.color }}>
                      Template · 0{idx + 1}
                    </div>
                    <h2 className="font-display text-[28px] leading-tight mb-3"
                        style={{ color: "#1a1815", letterSpacing: "-0.02em", fontWeight: 700 }}>
                      {t.title}
                    </h2>
                    <p className="text-[14px] leading-relaxed mb-5" style={{ color: "#6b6358" }}>
                      {t.pitch}
                    </p>
                    <ul className="space-y-2 mb-6">
                      {t.benefits.map((b, i) => (
                        <li key={i} className="flex items-start gap-2 text-[13px]" style={{ color: "#4a4538" }}>
                          <span className="w-4 h-4 shrink-0 rounded-full grid place-items-center mt-0.5"
                                style={{ background: "#f3e9d0", color: "#b89855" }}>
                            <Check size={9} strokeWidth={3} />
                          </span>
                          <span>{b}</span>
                        </li>
                      ))}
                    </ul>
                    <Link to="/?login=1"
                          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-[13px] font-semibold shadow-md self-start transition"
                          style={{ background: "#1a3a6e", color: "#f6f3ee" }}
                          data-testid={`vb-template-cta-${t.id}`}>
                      Utiliser ce template <ArrowRight size={13} />
                    </Link>
                  </div>
                </div>
              </article>
            );
          })}
        </section>

        {/* CTA final */}
        <section className="mt-16 rounded-3xl p-10 text-center shadow-md"
                 style={{ background: "linear-gradient(135deg, #1a3a6e 0%, #2c4d85 100%)", color: "#f6f3ee" }}>
          <div className="text-[11px] tracking-[0.22em] uppercase font-bold mb-3" style={{ color: "#d4b982" }}>
            En 5 minutes · pas plus
          </div>
          <h2 className="font-display text-[32px] leading-tight mb-3"
              style={{ letterSpacing: "-0.025em", fontWeight: 600 }}>
            Votre <span className="font-serif-italic" style={{ color: "#d4b982" }}>premier Vision Board</span> en quelques clics.
          </h2>
          <p className="text-[14.5px] mb-6 opacity-85 max-w-md mx-auto">
            L'IA pose les bonnes questions, génère un brouillon, vous éditez, vous téléchargez. Aussi simple que ça.
          </p>
          <Link to="/?login=1"
                className="inline-flex items-center gap-2 px-7 py-3 rounded-full text-[14px] font-semibold transition shadow-md"
                style={{ background: "#d4b982", color: "#0c1d33" }}
                data-testid="vb-cta-final">
            Commencer gratuitement <ArrowRight size={14} />
          </Link>
        </section>
      </main>

      <UnifiedFooter />
    </div>
  );
}
