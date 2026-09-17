/**
 * /expansion-agent — Landing conversion (design beige "MyExtension AI" maquette).
 * Header custom : ancres sections + bouton WhatsApp Contact.
 * Pied de page : UnifiedFooter (partagé avec / et /myextension-ai).
 */
import React from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  ArrowRight, Sparkles, Rocket, Lightbulb, Crosshair, MessageCircle, BarChart3,
  Search, ClipboardCheck, TrendingUp, ShieldCheck, Target, CreditCard, Lock,
} from "lucide-react";
import { UnifiedFooter } from "@/pages/LandingHub";

const APP_URL = "https://app.zayado.net/login";
const WHATSAPP_URL = "https://wa.me/33183643999?text=Bonjour%20Zayado%2C%20je%20suis%20intéressé(e)%20par%20Expansion%20Agent.";

// ── Header local ───────────────────────────────────────
const PageHeader = () => (
  <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-[var(--zayado-border)]" data-testid="expansion-header">
    <div className="max-w-[1280px] mx-auto px-4 md:px-6 py-4 flex items-center justify-between gap-6">
      <Link to="/" className="flex items-center gap-1 shrink-0" data-testid="expansion-logo">
        <span className="text-[19px] md:text-[21px] tracking-tight font-medium" style={{ color: "var(--zayado-navy)" }}>
          Zayado<span style={{ color: "#b89855" }}>.</span>
        </span>
      </Link>
      <nav className="hidden md:flex items-center gap-6 text-sm" style={{ color: "var(--zayado-text)" }}>
        <a href="#hero" className="hover:opacity-70" data-testid="hdr-hero">Aperçu</a>
        <a href="#leviers" className="hover:opacity-70" data-testid="hdr-leviers">5 leviers</a>
        <a href="#methode" className="hover:opacity-70" data-testid="hdr-methode">Méthode</a>
        <a href="#temoignages" className="hover:opacity-70" data-testid="hdr-temoignages">Témoignages</a>
        <a href="#tarifs" className="hover:opacity-70" data-testid="hdr-tarifs">Tarifs</a>
      </nav>
      <a href={WHATSAPP_URL} target="_blank" rel="noopener noreferrer" data-testid="header-whatsapp-contact"
         className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-white text-sm font-medium transition hover:opacity-90"
         style={{ background: "var(--zayado-navy)" }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0 0 20.464 3.488"/>
        </svg>
        Contact
      </a>
    </div>
  </header>
);

// ── HERO beige ─────────────────────────────────────────
const Hero = () => (
  <section id="hero" className="relative overflow-hidden pt-14 pb-20" style={{ background: "var(--zayado-cream)" }} data-testid="exp-hero">
    {/* mountains svg suggestion */}
    <div className="absolute inset-x-0 bottom-0 h-1/2 opacity-20"
         style={{ backgroundImage: "url('https://images.unsplash.com/photo-1465056836041-7f43ac27dcb5?auto=format&w=2000&q=70')", backgroundSize: "cover", backgroundPosition: "center" }} />
    <div className="relative max-w-[1280px] mx-auto px-4 md:px-8 grid lg:grid-cols-12 gap-10 items-center">
      {/* LEFT */}
      <div className="lg:col-span-6">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--zayado-gold-bg)] border border-[var(--zayado-gold-soft)]/40 text-[11px] uppercase tracking-[0.22em] mb-6"
             style={{ color: "var(--zayado-gold)" }}>
          <Sparkles size={13} /> Expansion Agent
        </div>
        <h1 className="font-medium tracking-tight mb-6 text-[var(--zayado-navy)]"
            style={{ fontSize: "clamp(2.2rem, 5vw, 3.6rem)", lineHeight: "1.05" }}>
          Votre copilote IA<br />pour une croissance<br />
          <span className="text-[var(--zayado-navy)]">durable et intelligente.</span>
        </h1>
        <p className="text-base md:text-lg max-w-lg mb-8 leading-relaxed" style={{ color: "var(--zayado-muted)" }}>
          Expansion Agent analyse votre activité, identifie les leviers les plus impactants
          et vous propose un plan d&apos;action personnalisé pour accélérer votre croissance.
        </p>
        <div className="flex flex-wrap items-center gap-3 mb-7">
          <a href={APP_URL} data-testid="exp-cta-start"
             className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-white font-medium text-sm hover:opacity-90 transition"
             style={{ background: "var(--zayado-navy)" }}>
            Démarrer gratuitement <ArrowRight size={16} />
          </a>
          <a href="#methode" className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-white border border-[var(--zayado-border)] text-sm font-medium hover:bg-[var(--zayado-cream)] transition"
             style={{ color: "var(--zayado-text)" }}>
            ▸ Voir une démo
          </a>
        </div>
        <div className="flex flex-wrap items-center gap-5 text-xs" style={{ color: "var(--zayado-muted)" }}>
          <span className="flex items-center gap-1.5"><ShieldCheck size={14} style={{ color: "var(--zayado-gold)" }} /> IA 100% alignée</span>
          <span className="flex items-center gap-1.5"><BarChart3 size={14} style={{ color: "var(--zayado-gold)" }} /> Résultats mesurables</span>
          <span className="flex items-center gap-1.5"><CreditCard size={14} style={{ color: "var(--zayado-gold)" }} /> Sans carte bancaire</span>
        </div>
      </div>

      {/* RIGHT - mockup stats (sans robot) */}
      <div className="lg:col-span-6 relative">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white rounded-2xl border border-[var(--zayado-border)] p-4 shadow-sm">
            <div className="text-[11px] uppercase tracking-wider mb-1" style={{ color: "var(--zayado-muted)" }}>Croissance en cours</div>
            <div className="font-display italic text-3xl" style={{ color: "var(--zayado-navy)" }}>+ 37<span className="text-xl">%</span></div>
            <div className="text-[10px] mt-0.5" style={{ color: "#10b981" }}>vs mois dernier</div>
          </div>
          <div className="bg-white rounded-2xl border border-[var(--zayado-border)] p-4 shadow-sm">
            <div className="text-[11px] uppercase tracking-wider mb-1" style={{ color: "var(--zayado-muted)" }}>Impact potentiel</div>
            <div className="font-display italic text-3xl" style={{ color: "var(--zayado-navy)" }}>+24<span className="text-xl">%</span></div>
            <div className="text-[10px] mt-0.5" style={{ color: "var(--zayado-muted)" }}>de conversions</div>
          </div>
          <div className="bg-white rounded-2xl border border-[var(--zayado-border)] p-4 shadow-sm col-span-2">
            <div className="text-[11px] uppercase tracking-wider mb-1" style={{ color: "var(--zayado-muted)" }}>Levier principal · Action recommandée</div>
            <div className="flex items-center gap-2 mb-1">
              <Target size={16} style={{ color: "var(--zayado-gold)" }} />
              <span className="font-medium" style={{ color: "var(--zayado-navy)" }}>Acquisition</span>
              <span className="text-xs" style={{ color: "var(--zayado-muted)" }}>—</span>
              <span className="text-sm" style={{ color: "var(--zayado-text)" }}>Optimiser votre page d&apos;accueil</span>
            </div>
            <div className="text-xs" style={{ color: "var(--zayado-muted)" }}>Améliorez votre tunnel d&apos;acquisition pour gagner plus de clients.</div>
          </div>
        </div>
      </div>
    </div>

    {/* 5 chips */}
    <div className="relative max-w-[1280px] mx-auto px-4 md:px-8 mt-10 flex flex-wrap justify-center gap-3">
      {[
        { icon: Target, label: "Acquisition" },
        { icon: Rocket, label: "Activation" },
        { icon: MessageCircle, label: "Rétention" },
        { icon: Lightbulb, label: "Recommandation" },
        { icon: BarChart3, label: "Revenus" },
      ].map(({ icon: Icon, label }) => (
        <span key={label} className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-[var(--zayado-border)] text-sm" style={{ color: "var(--zayado-text)" }}>
          <Icon size={15} style={{ color: "var(--zayado-gold)" }} /> {label}
        </span>
      ))}
    </div>
  </section>
);

// ── 5 LEVIERS ──────────────────────────────────────────
const LEVIERS = [
  { icon: Rocket, title: "Acquisition", desc: "Attirez plus de visiteurs qualifiés sur vos canaux les plus performants." },
  { icon: Lightbulb, title: "Activation", desc: "Transformez vos visiteurs en utilisateurs actifs grâce à la bonne expérience." },
  { icon: Crosshair, title: "Rétention", desc: "Fidélisez vos utilisateurs et augmentez leur engagement." },
  { icon: MessageCircle, title: "Recommandation", desc: "Faites de vos clients vos meilleurs ambassadeurs naturellement." },
  { icon: BarChart3, title: "Revenus", desc: "Optimisez votre modèle économique pour plus d'impact et de profit." },
];

const Leviers = () => (
  <section id="leviers" className="py-20 bg-white" data-testid="exp-leviers">
    <div className="max-w-[1280px] mx-auto px-4 md:px-8 text-center mb-14">
      <h2 className="font-medium tracking-tight mb-3" style={{ fontSize: "clamp(1.6rem, 3vw, 2.2rem)", color: "var(--zayado-navy)" }}>
        Un Expansion Agent. 5 leviers. Des résultats.
      </h2>
      <p className="text-sm md:text-base" style={{ color: "var(--zayado-muted)" }}>
        Notre IA travaille sur les 5 leviers de croissance essentiels pour votre business.
      </p>
    </div>
    <div className="max-w-[1280px] mx-auto px-4 md:px-8 grid grid-cols-2 md:grid-cols-5 gap-6 md:gap-8">
      {LEVIERS.map(({ icon: Icon, title, desc }) => (
        <div key={title} className="text-center">
          <div className="mx-auto w-14 h-14 rounded-full flex items-center justify-center mb-4"
               style={{ background: "var(--zayado-gold-bg)", color: "var(--zayado-gold)" }}>
            <Icon size={22} />
          </div>
          <h3 className="font-medium mb-2" style={{ color: "var(--zayado-navy)" }}>{title}</h3>
          <p className="text-xs md:text-sm leading-relaxed" style={{ color: "var(--zayado-muted)" }}>{desc}</p>
        </div>
      ))}
    </div>
  </section>
);

// ── COMMENT ÇA MARCHE ─────────────────────────────────
const STEPS = [
  { icon: Search, title: "1. Analyse IA", desc: "Expansion Agent analyse vos données, votre marché et vos objectifs." },
  { icon: Lightbulb, title: "2. Insights clés", desc: "Il identifie les opportunités à fort impact pour votre croissance." },
  { icon: ClipboardCheck, title: "3. Plan d'action", desc: "Vous recevez un plan d'action clair, priorisé et personnalisé." },
  { icon: TrendingUp, title: "4. Suivi & optimisation", desc: "Suivez vos résultats et laissez l'IA ajuster vos actions." },
];

const Methode = () => (
  <section id="methode" className="py-20" style={{ background: "var(--zayado-cream)" }} data-testid="exp-methode">
    <div className="max-w-[1280px] mx-auto px-4 md:px-8">
      <h2 className="text-center font-medium tracking-tight mb-14" style={{ fontSize: "clamp(1.6rem, 3vw, 2.2rem)", color: "var(--zayado-navy)" }}>
        Comment ça marche ?
      </h2>
      <div className="grid md:grid-cols-4 gap-8 relative">
        {STEPS.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="text-center bg-white rounded-2xl border border-[var(--zayado-border)] p-6">
            <div className="mx-auto w-14 h-14 rounded-full flex items-center justify-center mb-4"
                 style={{ background: "var(--zayado-gold-bg)", color: "var(--zayado-gold)" }}>
              <Icon size={22} />
            </div>
            <h3 className="font-medium mb-2" style={{ color: "var(--zayado-navy)" }}>{title}</h3>
            <p className="text-xs md:text-sm leading-relaxed" style={{ color: "var(--zayado-muted)" }}>{desc}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

// ── TÉMOIGNAGES ────────────────────────────────────────
const TESTIS = [
  { quote: "Expansion Agent m'a permis d'identifier les bons leviers. +42% de clients en 2 mois seulement.", name: "Thomas D.", role: "Fondateur, Agence Digitale", init: "T" },
  { quote: "Les recommandations sont ultra pertinentes. Je gagne un temps précieux chaque semaine.", name: "Sarah L.", role: "CEO, E-commerce", init: "S" },
  { quote: "Une IA qui comprend vraiment mon business et m'aide à prendre les meilleures décisions.", name: "Julien M.", role: "Entrepreneur", init: "J" },
];

const Temoignages = () => (
  <section id="temoignages" className="py-20 bg-white" data-testid="exp-temoignages">
    <div className="max-w-[1280px] mx-auto px-4 md:px-8">
      <h2 className="text-center font-medium tracking-tight mb-12" style={{ fontSize: "clamp(1.6rem, 3vw, 2.2rem)", color: "var(--zayado-navy)" }}>
        Ils accélèrent leur croissance avec Expansion Agent
      </h2>
      <div className="grid md:grid-cols-3 gap-5">
        {TESTIS.map((t, i) => (
          <div key={i} className="bg-white border border-[var(--zayado-border)] rounded-2xl p-6">
            <p className="text-sm leading-relaxed mb-5" style={{ color: "var(--zayado-text)" }}>
              &laquo;&nbsp;{t.quote}&nbsp;&raquo;
            </p>
            <div className="flex items-center gap-3 pt-4 border-t border-[var(--zayado-border)]">
              <div className="w-10 h-10 rounded-full flex items-center justify-center font-medium text-white"
                   style={{ background: "var(--zayado-navy)" }}>{t.init}</div>
              <div>
                <div className="text-sm font-medium" style={{ color: "var(--zayado-navy)" }}>{t.name}</div>
                <div className="text-xs" style={{ color: "var(--zayado-muted)" }}>{t.role}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-10 flex flex-wrap items-center justify-center gap-6 text-xs" style={{ color: "var(--zayado-muted)" }}>
        <span className="flex items-center gap-1.5">★★★★★ 4,9/5 sur plus de 500 avis</span>
        <span>+2 000 entrepreneurs accompagnés</span>
        <span className="flex items-center gap-1.5"><Lock size={12} /> Sécurisé et confidentiel</span>
      </div>
    </div>
  </section>
);

// ── CTA FINAL beige (avec section navy en plus comme demandé) ──────────────
const FinalCTA = () => (
  <>
    {/* Section bleue (gradient navy zayado) */}
    <section className="py-20" style={{ background: "var(--zayado-navy-gradient)" }} data-testid="exp-navy-section">
      <div className="max-w-3xl mx-auto px-6 text-center text-white">
        <h2 className="font-display italic mb-5" style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)" }}>
          Pourquoi nos clients <em style={{ color: "var(--zayado-gold-soft)" }}>ne reviennent jamais en arrière.</em>
        </h2>
        <p className="text-white/80 max-w-xl mx-auto mb-8">
          Expansion Agent ne remplace pas votre intuition — il l&apos;amplifie avec de la donnée et 5 leviers prouvés.
          Vous décidez. Il prépare, mesure, ajuste.
        </p>
        <a href={APP_URL} className="inline-flex items-center gap-2 px-7 py-4 rounded-full bg-white text-sm font-medium hover:bg-[var(--zayado-gold-soft)] transition"
           style={{ color: "var(--zayado-navy)" }} data-testid="exp-navy-cta">
          Activer Expansion Agent <ArrowRight size={16} />
        </a>
      </div>
    </section>

    {/* CTA beige final */}
    <section id="tarifs" className="py-20" style={{ background: "var(--zayado-cream)" }} data-testid="exp-final-cta">
      <div className="max-w-4xl mx-auto px-6">
        <div className="rounded-3xl p-10 md:p-14 text-center relative overflow-hidden border border-[var(--zayado-border)]"
             style={{ background: "var(--zayado-cream-dark)" }}>
          <h2 className="font-medium tracking-tight mb-4" style={{ fontSize: "clamp(1.6rem, 3vw, 2.4rem)", color: "var(--zayado-navy)" }}>
            Prêt à accélérer votre croissance ?
          </h2>
          <p className="text-sm md:text-base mb-8 max-w-lg mx-auto" style={{ color: "var(--zayado-muted)" }}>
            Rejoignez des milliers d&apos;entrepreneurs qui utilisent déjà Expansion Agent
            pour scaler leur business intelligemment.
          </p>
          <a href={APP_URL} className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-white font-medium text-sm hover:opacity-90 transition"
             style={{ background: "var(--zayado-navy)" }} data-testid="exp-final-cta-btn">
            Démarrer gratuitement <ArrowRight size={16} />
          </a>
          <p className="text-xs mt-3" style={{ color: "var(--zayado-muted)" }}>Aucune carte bancaire requise</p>
        </div>
      </div>
    </section>
  </>
);

export default function ExpansionAgent() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--zayado-cream)" }} data-testid="expansion-agent-conversion">
      <Helmet>
        <title>Expansion Agent IA — Votre copilote pour une croissance durable | Zayado</title>
        <meta name="description" content="Expansion Agent analyse votre activité, identifie les 5 leviers de croissance (Acquisition, Activation, Rétention, Recommandation, Revenus) et vous propose un plan d'action IA personnalisé." />
        <link rel="canonical" href="https://zayado.net/expansion-agent" />
      </Helmet>
      <PageHeader />
      <main className="flex-1">
        <Hero />
        <Leviers />
        <Methode />
        <Temoignages />
        <FinalCTA />
      </main>
      <UnifiedFooter />
    </div>
  );
}
