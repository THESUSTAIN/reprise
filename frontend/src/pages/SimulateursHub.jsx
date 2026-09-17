import React from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Calculator, BarChart3, Scale, ArrowRight, Sparkles } from "lucide-react";
import { PublicHeader, UnifiedFooter } from "./LandingHub";

const SIMULATORS = [
  {
    slug: "rentabilite",
    icon: Calculator,
    title: "Simulateur de rentabilité",
    desc: "Calculez votre seuil de rentabilité, vos marges et le revenu net qu'un projet peut générer.",
    time: "3 min",
    route: "/simulateur-rentabilite",
  },
  {
    slug: "statut",
    icon: Scale,
    title: "Simulateur de statut juridique",
    desc: "Trouvez le statut adapté (SASU, EURL, Micro-entreprise) à votre projet et votre fiscalité.",
    time: "5 min",
    route: "/simulateur-statut-juridique",
  },
  {
    slug: "sante",
    icon: BarChart3,
    title: "Analyse santé financière",
    desc: "Diagnostiquez la santé financière de votre activité : trésorerie, marges, dépendance clients.",
    time: "4 min",
    route: "/analyse-sante-financiere",
  },
];

export default function SimulateursHub() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--zayado-cream)" }}>
      <Helmet>
        <title>Simulateurs Gratuits pour Entrepreneurs | ZAYADO</title>
        <meta name="description" content="Testez gratuitement votre projet : calculez la rentabilité de votre entreprise, trouvez votre statut juridique idéal ou évaluez votre bien-être pro en 2 minutes." />
        <meta property="og:title" content="Simulateurs Gratuits pour Entrepreneurs | ZAYADO" />
        <meta property="og:description" content="Testez gratuitement votre projet : calculez la rentabilité de votre entreprise, trouvez votre statut juridique idéal ou évaluez votre bien-être pro en 2 minutes." />
        <link rel="canonical" href="https://zayado.net/simulateurs" />
      </Helmet>

      <PublicHeader />
      <main className="flex-1" data-testid="page-simulateurs-hub">
        <section className="relative" style={{ background: "var(--zayado-navy-gradient)", color: "#F6F3EE" }}>
          <div className="max-w-6xl mx-auto px-6 py-16 sm:py-24">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] tracking-[0.18em] uppercase font-semibold mb-5"
                 style={{ background: "rgba(255,255,255,0.10)", color: "#F6F3EE", border: "1px solid rgba(255,255,255,0.20)" }}>
              <Sparkles size={12} /> Outils gratuits
            </div>
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl leading-[1.05] mb-4 max-w-3xl">
              3 simulateurs pour <span style={{ color: "#F6F3EE" }}>décider juste</span>.
            </h1>
            <p className="text-lg sm:text-xl opacity-85 max-w-2xl leading-relaxed">
              Sans inscription, sans carte. Calculs instantanés, rapport téléchargeable. Conçus pour les solo-fondateurs et les entrepreneurs en lancement.
            </p>
          </div>
        </section>

        <section className="max-w-6xl mx-auto px-6 py-16 sm:py-20">
          <div className="grid md:grid-cols-3 gap-5">
            {SIMULATORS.map((s) => {
              const Ic = s.icon;
              return (
                <Link
                  key={s.slug}
                  to={s.route}
                  data-testid={`simulator-${s.slug}`}
                  className="group bg-white rounded-3xl p-7 border border-[var(--zayado-border)] hover:shadow-lg hover:-translate-y-0.5 transition flex flex-col"
                >
                  <div className="w-12 h-12 rounded-2xl grid place-items-center mb-5 shadow-md"
                       style={{
                         background: "linear-gradient(135deg, #1F3B73 0%, #2A4D8F 100%)",
                         color: "#F6F3EE",
                         boxShadow: "0 4px 12px rgba(31, 59, 115, 0.25)",
                       }}>
                    <Ic size={20} />
                  </div>
                  <h2 className="font-display text-2xl leading-tight mb-2" style={{ color: "var(--zayado-text)" }}>
                    {s.title}
                  </h2>
                  <p className="text-[14px] opacity-75 leading-relaxed mb-5 flex-1" style={{ color: "var(--zayado-text)" }}>
                    {s.desc}
                  </p>
                  <div className="flex items-center justify-between pt-4 border-t border-[var(--zayado-border)]">
                    <span className="text-[12px] uppercase tracking-wider opacity-65" style={{ color: "var(--zayado-text)" }}>
                      ~{s.time}
                    </span>
                    <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold group-hover:gap-2.5 transition-all" style={{ color: "var(--zayado-navy)" }}>
                      Lancer <ArrowRight size={14} />
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      </main>
      <UnifiedFooter />
    </div>
  );
}
