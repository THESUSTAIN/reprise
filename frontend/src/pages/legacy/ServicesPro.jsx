/* /services-pro — Vitrine des 3 leviers Pro by Zayado.
   Reprend la section du modèle TheSustain en page dédiée :
   - Création d'entreprise (dès 290€)
   - Pilotage d'entreprise (dès 190€/mois)
   - Extension IA (essai 3j gratuit)
   Design Zayado : navy/or, beige cream, DM Serif Display italique. */
import React from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  FileSignature, BarChart3, Sparkles, Check,
  ArrowRight, ArrowLeft, Crown, Shield, Percent,
} from "lucide-react";
import TheSustainHeader from "@/components/TheSustainHeader";
import TheSustainFooter from "@/components/TheSustainFooter";

const NAVY = "#3B5998";
const GOLD = "#AF1C1A";
const MUTED = "#4B5563";

const SERVICES = [
  {
    icon: FileSignature,
    title: "Création d'entreprise",
    tagline: "Statuts, immat, banque, comptabilité — clé en main.",
    price: "290 €",
    priceLabel: "dès",
    duration: "9 à 14 jours",
    cta: "Démarrer ma création",
    to: "/contact?subject=Création+d'entreprise",
    color: "linear-gradient(135deg, var(--zayado-navy) 0%, #2d3e60 100%)",
    features: [
      "Choix de structure (SASU, EURL, micro, SARL)",
      "Rédaction des statuts sur-mesure",
      "Immatriculation INPI / Greffe",
      "Ouverture compte pro (3 banques partenaires)",
      "Mise en place comptabilité IA (3 premiers mois offerts)",
      "Accompagnement humain Zayado",
    ],
    use_cases: [
      "Vous lancez votre activité solo ou en société",
      "Vous voulez éviter les pièges juridiques classiques",
      "Vous cherchez du sur-mesure, pas un formulaire en ligne",
    ],
  },
  {
    icon: BarChart3,
    title: "Pilotage d'entreprise",
    tagline: "Tableau de bord, OKR, finances. Votre copilote business mensuel.",
    price: "190 €",
    priceLabel: "dès",
    duration: "mois",
    cta: "Découvrir Pilotage",
    to: "/contact?subject=Pilotage+d'entreprise",
    color: "linear-gradient(135deg, #d4af37 0%, #b8941f 100%)",
    features: [
      "Dashboard personnalisé (CA, marge, trésorerie)",
      "Méthode OKR trimestrielle adaptée solo",
      "Pilotage financier mensuel par un expert",
      "Alertes proactives (trésorerie, marge en baisse…)",
      "Préparation bilan annuel",
      "Accès Extension IA inclus",
    ],
    use_cases: [
      "Vous facturez plus de 30k€/an et voulez piloter sérieusement",
      "Vous ne savez plus où en est votre trésorerie",
      "Vous voulez un copilote qui pousse à agir, pas juste regarder",
    ],
  },
  {
    icon: Sparkles,
    title: "Extension IA",
    tagline: "Automatisation, agents IA, contenu — app.zayado.net.",
    price: "Gratuit",
    priceLabel: "essai",
    duration: "14 jours",
    cta: "Tester gratuitement",
    to: "/login",
    color: "linear-gradient(135deg, #1a2742 0%, var(--zayado-gold) 200%)",
    features: [
      "Agents IA Claude pour rédaction, analyse, pilotage",
      "Automatisations n8n + intégrations 200+ outils",
      "Génération contenu (articles, newsletters, emails)",
      "Tableau de bord énergie/humeur du fondateur",
      "Diagnostic mutuelle, fiscalité, juridique IA",
      "Communauté privée Zayado",
    ],
    use_cases: [
      "Vous êtes solo et noyé sous les tâches répétitives",
      "Vous voulez générer du contenu pro sans copywriter",
      "Vous cherchez à automatiser sans coder",
    ],
  },
];

const BENEFITS = [
  { icon: Shield, label: "Garantie satisfaction 30j", desc: "Remboursement intégral sans condition" },
  { icon: Percent, label: "Tarifs préférentiels groupement", desc: "Économie moyenne −22% vs marché" },
  { icon: Crown, label: "Accompagnement humain", desc: "Pas juste un outil — un partenaire qui répond" },
];

export default function ServicesPro({ embedded = false }) {
  return (
    <div className="min-h-screen ts-page" style={{ background: "#FFFFFF" }} data-testid="services-pro-page">
      <Helmet>
        <title>Services Pro · Presta-Partenaire TheSustain</title>
        <meta name="description" content="3 leviers pour faire grandir votre entreprise. Réseau de prestataires chrétiens TheSustain." />
      </Helmet>
      {!embedded && <TheSustainHeader />}

      {/* HERO */}
      <section className="max-w-[1200px] mx-auto px-4 md:px-6 pt-12 pb-10">
        <Link to="/partenaires" className="text-xs hover:underline inline-flex items-center gap-1 mb-5" style={{ color: MUTED }}>
          <ArrowLeft size={11} /> Réseau Zayado
        </Link>
        <div className="text-[11px] uppercase tracking-[0.3em] mb-3" style={{ color: GOLD }}>
          — Services Pro by Zayado
        </div>
        <h1 className="font-bold mb-5"
            style={{ fontFamily: "'DM Serif Display', serif",
                     fontSize: "clamp(2.2rem, 5vw, 3.8rem)", lineHeight: 1.05, color: NAVY }}>
          3 leviers pour faire <em>grandir</em><br/>
          votre entreprise.
        </h1>
        <p className="text-base md:text-lg max-w-2xl leading-relaxed" style={{ color: MUTED }}>
          Ouverts à toutes et tous, sans condition. Tarifs préférentiels du groupement Zayado.
          <strong style={{ color: NAVY }}> Pas d'engagement,</strong> pas de frais cachés.
        </p>
      </section>

      {/* LES 3 SERVICES */}
      <section className="max-w-[1200px] mx-auto px-4 md:px-6 pb-16 space-y-8" data-testid="services-list">
        {SERVICES.map((s, idx) => {
          const Icon = s.icon;
          const reverse = idx % 2 === 1;
          return (
            <article key={s.title}
                     className={`bg-white border border-[var(--zayado-border)] rounded-3xl overflow-hidden grid lg:grid-cols-2 gap-0 ${reverse ? "lg:[&>div:first-child]:order-2" : ""}`}
                     data-testid={`service-pro-${idx}`}>
              {/* Colonne gauche : visuel + prix */}
              <div className="relative p-10 md:p-12 flex flex-col justify-center min-h-[300px] text-white"
                   style={{ background: s.color }}>
                <Icon size={32} className="mb-5 opacity-90" />
                <div className="text-[11px] uppercase tracking-[0.25em] opacity-80 mb-2">
                  Service {idx + 1}
                </div>
                <h2 className="font-bold mb-3"
                    style={{ fontFamily: "'DM Serif Display', serif",
                             fontSize: "clamp(1.8rem, 3.5vw, 2.6rem)", lineHeight: 1.1 }}>
                  {s.title}
                </h2>
                <p className="text-sm opacity-90 mb-6 max-w-sm">{s.tagline}</p>

                <div className="flex items-baseline gap-2 mb-1">
                  <span className="text-[11px] uppercase tracking-wider opacity-80">{s.priceLabel}</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="font-bold" style={{ fontFamily: "'DM Serif Display', serif", fontSize: "clamp(2.2rem, 4vw, 3rem)" }}>
                    {s.price}
                  </span>
                  <span className="text-sm opacity-80">/ {s.duration}</span>
                </div>
              </div>

              {/* Colonne droite : features + use cases + CTA */}
              <div className="p-10 md:p-12">
                <div className="text-[11px] uppercase tracking-[0.2em] mb-3 font-bold" style={{ color: NAVY }}>
                  Ce que vous obtenez
                </div>
                <ul className="space-y-2.5 mb-7">
                  {s.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm" style={{ color: "var(--zayado-text)" }}>
                      <Check size={15} className="shrink-0 mt-0.5" style={{ color: GOLD }} />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>

                <div className="text-[11px] uppercase tracking-[0.2em] mb-2.5 font-bold" style={{ color: NAVY }}>
                  Pour qui ?
                </div>
                <ul className="space-y-1.5 mb-7 text-xs" style={{ color: MUTED }}>
                  {s.use_cases.map((u) => <li key={u}>· {u}</li>)}
                </ul>

                <Link to={s.to}
                      className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-white text-sm font-medium"
                      style={{ background: NAVY }}
                      data-testid={`service-pro-cta-${idx}`}>
                  {s.cta} <ArrowRight size={13} />
                </Link>
              </div>
            </article>
          );
        })}
      </section>

      {/* BÉNÉFICES TRANSVERSAUX */}
      <section className="bg-white border-y border-[var(--zayado-border)] py-14" data-testid="services-benefits">
        <div className="max-w-[1100px] mx-auto px-4 md:px-6">
          <div className="text-[11px] uppercase tracking-[0.25em] mb-2 text-center" style={{ color: GOLD }}>
            — Pourquoi Zayado
          </div>
          <h2 className="font-bold text-center mb-10"
              style={{ fontFamily: "'DM Serif Display', serif",
                       fontSize: "clamp(1.7rem, 3.5vw, 2.4rem)", color: NAVY }}>
            La différence Zayado.
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {BENEFITS.map((b) => {
              const Icon = b.icon;
              return (
                <div key={b.label} className="text-center">
                  <div className="w-12 h-12 rounded-full mx-auto flex items-center justify-center mb-4"
                       style={{ background: "var(--zayado-cream)" }}>
                    <Icon size={20} style={{ color: NAVY }} />
                  </div>
                  <div className="font-bold text-base mb-2" style={{ color: NAVY }}>{b.label}</div>
                  <div className="text-sm leading-relaxed" style={{ color: MUTED }}>{b.desc}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA FINAL */}
      <section className="max-w-[900px] mx-auto px-4 md:px-6 py-16 text-center" data-testid="services-cta-final">
        <h2 className="font-bold mb-4"
            style={{ fontFamily: "'DM Serif Display', serif",
                     fontSize: "clamp(1.8rem, 4vw, 2.6rem)", lineHeight: 1.1, color: NAVY }}>
          Pas sûr de votre besoin ?
        </h2>
        <p className="text-base mb-7 max-w-xl mx-auto" style={{ color: MUTED }}>
          Réservez 20 minutes avec notre équipe — on cadrera ensemble le bon levier
          pour votre situation. Sans engagement, sans bullshit.
        </p>
        <Link to="/contact?subject=RDV+conseil+Services+Pro"
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-white text-base font-medium"
              style={{ background: GOLD }}>
          Prendre RDV (gratuit) <ArrowRight size={14} />
        </Link>
      </section>

      {!embedded && <TheSustainFooter />}
    </div>
  );
}
