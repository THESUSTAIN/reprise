import React from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Building2, Briefcase, Home, FileSignature, Check, ArrowRight, Shield, Zap, Sparkles } from "lucide-react";
import { PublicHeader, UnifiedFooter } from "./LandingHub";

const STATUSES = [
  {
    slug: "bnc",
    icon: Briefcase,
    title: "Profession libérale & Freelance (BNC)",
    subtitle: "Consultants, développeurs, graphistes, coachs, professions médicales et paramédicales.",
    bullets: [
      "Déclaration d'activité auprès du Guichet Unique",
      "Obtention de votre numéro SIRET",
      "Option pour le régime fiscal optimal (Micro-BNC ou Déclaration contrôlée)",
      "Configuration du cockpit MyExtension AI",
    ],
    pour: "Pour qui : Consultants, développeurs, graphistes, coachs, professions médicales et paramédicales.",
  },
  {
    slug: "lmnp",
    icon: Home,
    title: "Investissement Immobilier (LMNP / BIC)",
    subtitle: "Propriétaires de locations meublées (courte ou longue durée).",
    bullets: [
      "Inscription obligatoire au Greffe via P0 i",
      "Levée de votre numéro SIRET pour activité immobilière",
      "Choix du régime fiscal (Forfaitaire ou Réel)",
      "Optimisation des amortissements et impôts",
    ],
    pour: "Pour qui : Propriétaires de locations meublées (courte ou longue durée).",
  },
  {
    slug: "societe",
    icon: Building2,
    title: "Création de Société (SASU, EURL, SARL, SAS)",
    subtitle: "Artisans, commerçants, startups — structure juridique distincte.",
    bullets: [
      "Rédaction des statuts par notre juriste référent",
      "Dépôt de capital auprès de nos banques partenaires (Qonto, Shine)",
      "Publication de l'annonce légale incluse",
      "Suivi INSEE et obtention du K-bis",
    ],
    pour: "Pour qui : Ceux qui ont besoin d'une structure juridique distincte (EURL, SASU, SARL, SAS).",
  },
];

const STEPS = [
  { n: 1, title: "Dossier Guichet Unique clé en main", desc: "Zéro stress face à l'INPI. Nos équipes et automatisations Make valident la conformité pour éviter les rejets." },
  { n: 2, title: "Obtention SIRET & Code APE", desc: "Suivi temps réel jusqu'à la réception de votre avis de situation INSEE." },
  { n: 3, title: "Accès immédiat à MyExtension AI", desc: "Votre cockpit est pré-configuré : Vision Board, popup d'énergie, suivi flux financiers (via Make)." },
  { n: 4, title: "Options de Prestige (optionnel)", desc: "Adresse Paris 2e, compte pro partenaire, pack DAF Serenity — activables durant le parcours." },
];

export default function CreationEntreprise() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--zayado-cream)" }}>
      <Helmet>
        <title>Création 1€ SASU/ EURL/ MICRO / BIC (LMNP/LMP) | ZAYADO</title>
        <meta
          name="description"
          content="Confiez votre déclaration d'activité, ou vos statuts à nos équipes. Lancez votre activité l'esprit serein avec notre formule d'accompagnement à 1 € symbolique c'est possible."
        />
        <meta property="og:title" content="Création 1€ SASU/ EURL/ MICRO / BIC (LMNP/LMP) | ZAYADO" />
        <meta property="og:description" content="Confiez votre déclaration d'activité, ou vos statuts à nos équipes. Lancez votre activité l'esprit serein avec notre formule d'accompagnement à 1 € symbolique c'est possible." />
        <link rel="canonical" href="https://zayado.net/creation-entreprise" />
      </Helmet>

      <PublicHeader />

      <main className="flex-1" data-testid="page-creation-entreprise">
        {/* Hero — pro tone */}
        <section className="relative overflow-hidden" style={{ background: "var(--zayado-navy-gradient)", color: "#F6F3EE" }}>
          <div
            className="absolute inset-0 opacity-10 pointer-events-none"
            style={{
              backgroundImage:
                "url(https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&w=1800&q=80)",
              backgroundSize: "cover",
              backgroundPosition: "center",
              mixBlendMode: "overlay",
            }}
          />
          <div className="max-w-6xl mx-auto px-6 py-20 sm:py-28 relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] tracking-[0.22em] uppercase font-semibold mb-6"
                 style={{ background: "rgba(255,255,255,0.10)", color: "#F6F3EE", border: "1px solid rgba(255,255,255,0.20)" }}
                 data-testid="creation-eyebrow">
              <Sparkles size={12} /> Simple, rapide et conforme
            </div>
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl leading-[1.0] mb-5 max-w-3xl tracking-tight">
              Lancez votre activité<br />
              <em className="italic" style={{ color: "#F6F3EE", fontStyle: "italic" }}>l'esprit tranquille.</em>
            </h1>
            <p className="text-lg sm:text-xl opacity-90 max-w-2xl mb-3 leading-relaxed">
              De l'immatriculation officielle au premier euro encaissé. ZAYADO s'occupe de vos formalités administratives auprès du
              <strong> Guichet Unique</strong> pour <strong>1 € de frais de dossier</strong>, et configure votre cockpit de pilotage.
            </p>
            <p className="text-[14px] opacity-70 max-w-2xl mb-9 leading-relaxed">
              Cabinet partenaire, juriste référent, rédaction des statuts, dépôt INPI, accompagnement bancaire (Qonto / Shine).
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                to="/myextension-ai"
                data-testid="creation-cta-primary"
                className="inline-flex items-center gap-2 px-7 h-12 rounded-full font-semibold transition shadow-lg"
                style={{ background: "#F6F3EE", color: "var(--zayado-navy)" }}
              >
                Commencer mon immatriculation pour 1€ <ArrowRight size={15} />
              </Link>
              <Link
                to="/simulateur-statut-juridique"
                data-testid="creation-cta-secondary"
                className="inline-flex items-center gap-2 px-6 h-12 rounded-full bg-white/10 hover:bg-white/20 border border-white/25 text-white font-medium transition backdrop-blur-sm"
              >
                Tester mon statut juridique
              </Link>
            </div>
          </div>
        </section>

        {/* Status cards */}
        <section className="max-w-6xl mx-auto px-6 py-16 sm:py-20" data-testid="creation-statuts">
          <div className="text-center mb-12">
            <div className="text-[11px] tracking-[0.22em] uppercase font-semibold mb-2" style={{ color: "var(--zayado-navy)" }}>
              Choisissez votre trajectoire
            </div>
            <h2 className="font-display text-3xl sm:text-4xl mb-3" style={{ color: "var(--zayado-text)" }}>
              3 parcours. Nous faisons le reste.
            </h2>
            <p className="text-base sm:text-lg opacity-75 max-w-2xl mx-auto" style={{ color: "var(--zayado-text)" }}>
              Nous expliquons les termes techniques de manière simple et rassurante.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-5">
            {STATUSES.map((s) => {
              const Icon = s.icon;
              return (
                <div
                  key={s.slug}
                  data-testid={`statut-${s.slug}`}
                  className="bg-white rounded-3xl p-7 border border-[var(--zayado-border)] hover:shadow-md transition flex flex-col"
                >
                  <div className="flex items-start gap-4 mb-4">
                    <div
                      className="w-12 h-12 shrink-0 rounded-2xl grid place-items-center shadow-md"
                      style={{
                        background: "linear-gradient(135deg, #1F3B73 0%, #2A4D8F 100%)",
                        color: "#F6F3EE",
                        boxShadow: "0 4px 12px rgba(31, 59, 115, 0.25)",
                      }}
                    >
                      <Icon size={20} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="font-display text-2xl leading-tight" style={{ color: "var(--zayado-text)" }}>
                        {s.title}
                      </h3>
                      <p className="text-[12.5px] opacity-65 mt-0.5" style={{ color: "var(--zayado-text)" }}>
                        {s.subtitle}
                      </p>
                    </div>
                  </div>
                  <ul className="space-y-2 mb-5 text-[14px]" style={{ color: "var(--zayado-text)" }}>
                    {s.bullets.map((b, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <Check size={15} className="shrink-0 mt-0.5" style={{ color: "var(--zayado-navy)" }} />
                        <span>{b}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-auto pt-4 border-t border-[var(--zayado-border)]">
                    <div className="text-[11.5px] tracking-[0.18em] uppercase font-semibold mb-1.5 opacity-65" style={{ color: "var(--zayado-text)" }}>
                      Pour qui ?
                    </div>
                    <p className="text-[13.5px] italic leading-relaxed" style={{ color: "var(--zayado-text)" }}>
                      {s.pour}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Process steps */}
        <section className="bg-white border-y border-[var(--zayado-border)]" data-testid="creation-process">
          <div className="max-w-6xl mx-auto px-6 py-16 sm:py-20">
            <div className="text-center mb-12">
              <div className="text-[11px] tracking-[0.22em] uppercase font-semibold mb-2" style={{ color: "var(--zayado-navy)" }}>
                Comment ça marche
              </div>
              <h2 className="font-display text-3xl sm:text-4xl" style={{ color: "var(--zayado-text)" }}>
                4 étapes, de l'idée à l'immatriculation.
              </h2>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {STEPS.map((st) => (
                <div key={st.n} className="relative" data-testid={`step-${st.n}`}>
                  <div
                    className="w-12 h-12 rounded-full grid place-items-center font-display text-xl mb-4"
                    style={{ background: "var(--zayado-navy)", color: "#F6F3EE" }}
                  >
                    {st.n}
                  </div>
                  <h3 className="font-display text-xl mb-2" style={{ color: "var(--zayado-text)" }}>
                    {st.title}
                  </h3>
                  <p className="text-[14px] leading-relaxed opacity-75" style={{ color: "var(--zayado-text)" }}>
                    {st.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Trust strip */}
        <section className="max-w-6xl mx-auto px-6 py-14" data-testid="creation-trust">
          <div className="grid sm:grid-cols-3 gap-5">
            {[
              { icon: Shield, title: "Hébergement 100% Français & RGPD", desc: "Vos documents d'identité et infos d'activité sont cryptés et stockés en Europe." },
              { icon: Sparkles, title: "Protection juridique", desc: "Dès votre immatriculation, vous êtes protégé contre les fausses factures et arnaques de contenu (faux registres payants)." },
              { icon: Zap, title: "Cockpit IA pré-configuré", desc: "Vision Board, popup d'énergie, flux financiers — utilisez-les avant même votre 1er client." },
            ].map((t, i) => {
              const Ic = t.icon;
              return (
                <div key={i} className="bg-white rounded-2xl p-5 border border-[var(--zayado-border)]">
                  <Ic size={20} style={{ color: "var(--zayado-navy)" }} className="mb-3" />
                  <h4 className="font-display text-lg mb-1" style={{ color: "var(--zayado-text)" }}>{t.title}</h4>
                  <p className="text-[13.5px] opacity-75" style={{ color: "var(--zayado-text)" }}>{t.desc}</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* Final CTA */}
        <section className="max-w-4xl mx-auto px-6 pb-20 text-center" data-testid="creation-final-cta">
          <div className="bg-[var(--zayado-navy)] rounded-3xl p-10 sm:p-14" style={{ color: "#F6F3EE" }}>
            <h2 className="font-display text-3xl sm:text-4xl mb-4">
              Prêt·e à donner vie à votre projet avec sens et clarté ?
            </h2>
            <p className="text-base sm:text-lg opacity-85 mb-7 max-w-xl mx-auto">
              Rejoignez les entrepreneurs qui ont choisi de poser des fondations stables pour leur activité.
            </p>
            <Link
              to="/myextension-ai"
              className="inline-flex items-center gap-2 px-8 h-13 py-3.5 rounded-full font-semibold transition shadow-lg"
              style={{ background: "#F6F3EE", color: "var(--zayado-navy)" }}
              data-testid="creation-bottom-cta"
            >
              Configurer ma déclaration d'activité (1 €) <ArrowRight size={15} />
            </Link>
          </div>
        </section>
      </main>

      <UnifiedFooter />
    </div>
  );
}
