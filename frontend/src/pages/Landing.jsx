/**
 * Landing — page d'accueil hub Zayado (style lean-journey).
 * 3 univers : Boutique · App MyExtension AI · Groupement.
 * Header + Footer partagés avec /myextension-ai (et avec /vision, /growth-agent…).
 *
 * Tout ce qui touche au shop est sur /boutique (layout dédié).
 */
import React from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  ArrowRight, Sparkles, ShoppingBag, LayoutDashboard, Users,
  Heart, ShieldCheck, Star, Quote, Mail, MessageCircle,
} from "lucide-react";

const APP_URL = "https://app.zayado.net/login";

// ──────────────────────────────────────────────────────
// Header & Footer (style lean-journey, à utiliser ailleurs aussi)
// ──────────────────────────────────────────────────────
const Header = () => (
  <header className="sticky top-0 z-50 bg-canvas/85 backdrop-blur border-b border-outline" data-testid="zayado-header">
    <div className="max-w-7xl mx-auto px-6 lg:px-10 h-16 flex items-center justify-between">
      <Link to="/" className="flex items-center gap-2.5" data-testid="logo-zayado">
        <div className="w-9 h-9 rounded-full bg-aubergine flex items-center justify-center">
          <div className="w-3.5 h-3.5 rounded-full border-2 border-cream" />
        </div>
        <span className="text-[19px] tracking-tight font-medium text-ink">
          Zayado<span className="text-aubergine">.</span>
        </span>
      </Link>
      <nav className="hidden md:flex items-center gap-7 text-sm text-ink/70">
        <Link to="/boutique" className="hover:text-aubergine transition" data-testid="nav-boutique">Boutique</Link>
        <Link to="/myextension-ai" className="hover:text-aubergine transition" data-testid="nav-app">App MyExtension AI</Link>
        <Link to="/expansion-agent" className="hover:text-aubergine transition" data-testid="nav-expansion">Expansion Agent</Link>
        <Link to="/vision" className="hover:text-aubergine transition" data-testid="nav-vision">Vision Board</Link>
        <Link to="/contact" className="hover:text-aubergine transition" data-testid="nav-contact">Contact</Link>
      </nav>
      <a
        href={APP_URL}
        data-testid="header-cta-join"
        className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm transition text-cream"
        style={{ background: "var(--zayado-navy-gradient)" }}
      >
        Rejoindre
        <ArrowRight className="w-4 h-4" />
      </a>
    </div>
  </header>
);

const Footer = () => (
  <footer className="bg-canvasSoft border-t border-outline mt-20" data-testid="zayado-footer">
    <div className="max-w-7xl mx-auto px-6 lg:px-10 py-12 grid gap-10 md:grid-cols-4">
      <div className="md:col-span-2">
        <Link to="/" className="flex items-center gap-2.5 mb-4">
          <div className="w-8 h-8 rounded-full bg-aubergine flex items-center justify-center">
            <div className="w-3 h-3 rounded-full border-2 border-cream" />
          </div>
          <span className="text-[17px] font-medium text-ink">Zayado<span className="text-aubergine">.</span></span>
        </Link>
        <p className="text-sm text-inkMuted max-w-xs leading-relaxed">
          La maison des entrepreneurs apaisés. Boutique, app IA, groupement —
          tout l&apos;écosystème pour entreprendre sans rester seul.
        </p>
      </div>
      <div>
        <div className="text-xs uppercase tracking-wider text-aubergine/70 mb-3">Explorer</div>
        <ul className="space-y-2 text-sm text-ink/75">
          <li><Link to="/boutique" className="hover:text-aubergine">Boutique</Link></li>
          <li><Link to="/myextension-ai" className="hover:text-aubergine">App MyExtension AI</Link></li>
          <li><Link to="/expansion-agent" className="hover:text-aubergine">Expansion Agent</Link></li>
          <li><Link to="/vision" className="hover:text-aubergine">Vision Board public</Link></li>
          <li><Link to="/valider-son-projet" className="hover:text-aubergine">Valider son projet</Link></li>
          <li><Link to="/tester-son-projet" className="hover:text-aubergine">Tester son projet</Link></li>
        </ul>
      </div>
      <div>
        <div className="text-xs uppercase tracking-wider text-aubergine/70 mb-3">Légal & contact</div>
        <ul className="space-y-2 text-sm text-ink/75">
          <li><Link to="/contact" className="hover:text-aubergine">Contact</Link></li>
          <li><Link to="/legal/mentions-legales" className="hover:text-aubergine">Mentions légales</Link></li>
          <li><Link to="/legal/confidentialite" className="hover:text-aubergine">Confidentialité</Link></li>
          <li><Link to="/legal/conditions-utilisation" className="hover:text-aubergine">CGU</Link></li>
          <li><Link to="/legal/cgv" className="hover:text-aubergine">CGV</Link></li>
        </ul>
      </div>
    </div>
    <div className="border-t border-outline">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 py-5 flex flex-wrap items-center justify-between gap-3 text-xs text-inkMuted">
        <span>© {new Date().getFullYear()} Zayado — entreprendre, sans rester seul.</span>
        <span className="italic">Fait avec calme, en France.</span>
      </div>
    </div>
  </footer>
);

// ──────────────────────────────────────────────────────
// HERO
// ──────────────────────────────────────────────────────
const Hero = () => (
  <section className="relative overflow-hidden pt-20 pb-24" data-testid="hub-hero">
    <div className="absolute top-20 -left-32 w-96 h-96 rounded-full bg-blush/35 blur-3xl" />
    <div className="absolute -bottom-32 -right-32 w-[30rem] h-[30rem] rounded-full bg-sky/35 blur-3xl" />
    <div className="absolute inset-0 dotted-bg opacity-50" />

    <div className="relative max-w-5xl mx-auto px-6 lg:px-10 text-center">
      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass border border-outline text-xs text-ink/70 mb-7" data-testid="hero-kicker">
        <span className="w-1.5 h-1.5 rounded-full bg-aubergine" />
        La maison des entrepreneurs apaisés
      </div>
      <h1
        className="font-display italic text-ink leading-[1.02] mb-7"
        style={{ fontSize: "clamp(2.6rem, 7vw, 5rem)" }}
        data-testid="hero-title"
      >
        Entreprendre <span className="text-aubergine">avec calme.</span>
      </h1>
      <p className="text-lg md:text-xl text-ink/70 max-w-2xl mx-auto leading-relaxed mb-10" data-testid="hero-subtitle">
        Trois territoires complémentaires pour bâtir, sans s&apos;épuiser :
        une <b className="text-ink">boutique</b> d&apos;outils &amp; rituels,
        une <b className="text-ink">app IA</b> qui prépare 70 % du travail,
        un <b className="text-ink">groupement</b> qui rompt l&apos;isolement.
      </p>
      <div className="flex flex-wrap items-center justify-center gap-4">
        <Link
          to="/boutique"
          data-testid="hero-cta-shop"
          className="group inline-flex items-center gap-2.5 bg-aubergine hover:bg-aubergine-deep text-cream pl-5 pr-3 py-3 rounded-full transition-all hover:translate-y-[-1px]"
        >
          Découvrir la boutique
          <span className="w-8 h-8 rounded-full bg-cream/15 flex items-center justify-center group-hover:bg-cream/25 transition">
            <ArrowRight className="w-4 h-4" />
          </span>
        </Link>
        <Link to="/myextension-ai" data-testid="hero-cta-app" className="text-ink/80 hover:text-aubergine text-sm underline underline-offset-4 decoration-aubergine/30">
          Essayer l&apos;app gratuitement →
        </Link>
      </div>
    </div>
  </section>
);

// ──────────────────────────────────────────────────────
// 3 UNIVERS (Boutique · App · Groupement)
// ──────────────────────────────────────────────────────
const UNIVERSES = [
  {
    icon: ShoppingBag,
    chip: "bg-blush",
    kicker: "Univers 01",
    title: "Boutique",
    desc: "Outils de l\u2019entrepreneur apaisé : carnets, posters, rituels, sons binauraux, accompagnement pro.",
    cta: { label: "Visiter la boutique", to: "/boutique" },
    points: ["Livraison soignée France & UE", "Paiement Mollie sécurisé", "Produits limités en stock"],
  },
  {
    icon: LayoutDashboard,
    chip: "bg-sky",
    kicker: "Univers 02",
    title: "App MyExtension AI",
    desc: "Le cockpit business des fondateurs solos. Vision board IA, mission du jour, growth agents, bien-être.",
    cta: { label: "Essayer l\u2019app", to: "/myextension-ai" },
    points: ["IA Mammouth (Claude Haiku)", "Make/Zapier · webhooks universels", "RGPD strict — données en Europe"],
  },
  {
    icon: Users,
    chip: "bg-sage",
    kicker: "Univers 03",
    title: "Groupement Zayado",
    desc: "Une communauté de fondateurs qui s\u2019entraident. Co-working live, masterminds mensuels, prêt d\u2019expertise.",
    cta: { label: "Rejoindre le groupement", to: "/contact" },
    points: ["Mastermind mensuel en visio", "Co-working live hebdomadaire", "Annuaire & prêt d\u2019expertise"],
  },
];

const Universes = () => (
  <section className="py-24 bg-canvasSoft border-y border-outline" data-testid="three-universes">
    <div className="max-w-7xl mx-auto px-6 lg:px-10">
      <div className="text-center mb-14 max-w-2xl mx-auto">
        <div className="text-xs uppercase tracking-[0.18em] text-aubergine/70 mb-3">Trois territoires</div>
        <h2 className="font-display italic" style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", color: "var(--zayado-text)" }}>
          Une maison, <span className="text-aubergine">trois portes d&apos;entrée.</span>
        </h2>
      </div>
      <div className="grid lg:grid-cols-3 gap-5">
        {UNIVERSES.map((u, i) => (
          <div key={u.title} className="bg-white border border-outline rounded-3xl p-7 flex flex-col hover:border-aubergine/30 transition" data-testid={`universe-${i}`}>
            <div className={`inline-flex w-fit items-center gap-2 px-3 py-1 rounded-full ${u.chip} text-[11px] tracking-wider text-aubergine mb-5`}>
              <u.icon className="w-3.5 h-3.5" />
              {u.kicker}
            </div>
            <h3 className="text-2xl text-ink tracking-tight mb-3">{u.title}</h3>
            <p className="text-ink/65 text-[15px] leading-relaxed mb-5 flex-1">{u.desc}</p>
            <ul className="space-y-2 mb-7">
              {u.points.map((p) => (
                <li key={p} className="text-[13px] text-ink/75 flex items-start gap-2">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-aubergine shrink-0" /> {p}
                </li>
              ))}
            </ul>
            <Link
              to={u.cta.to}
              className="inline-flex items-center gap-2 text-aubergine text-sm font-medium hover:gap-3 transition-all"
              data-testid={`universe-cta-${i}`}
            >
              {u.cta.label} <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        ))}
      </div>
    </div>
  </section>
);

// ──────────────────────────────────────────────────────
// INTÉGRATIONS marquee
// ──────────────────────────────────────────────────────
const INTEGRATIONS = ["Mammouth AI", "Stripe", "Mollie", "WooCommerce", "Brevo", "Make", "Zapier", "WhatsApp", "Google Drive", "Notion", "Microsoft 365", "Shopify"];

const Integrations = () => (
  <section className="py-20 overflow-hidden" data-testid="integrations-marquee">
    <div className="max-w-7xl mx-auto px-6 lg:px-10 text-center mb-10">
      <div className="text-xs uppercase tracking-[0.18em] text-aubergine/70 mb-3">Écosystème</div>
      <h2 className="font-display italic" style={{ fontSize: "clamp(1.4rem, 2.5vw, 2rem)", color: "var(--zayado-text)" }}>
        Connecté à votre <span className="text-aubergine">stack existante.</span>
      </h2>
    </div>
    <div className="flex gap-3 flex-wrap items-center justify-center max-w-5xl mx-auto px-6">
      {INTEGRATIONS.map((name) => (
        <span key={name} className="px-4 py-2 rounded-full bg-white border border-outline text-sm text-ink/80 hover:border-aubergine/40 transition">
          {name}
        </span>
      ))}
    </div>
  </section>
);

// ──────────────────────────────────────────────────────
// TESTIMONIALS
// ──────────────────────────────────────────────────────
const TESTIS = [
  { name: "Sarah L.", role: "Agence digitale", quote: "J\u2019ai trouvé un écosystème complet : la boutique, l\u2019app et la communauté. Plus jamais isolée." },
  { name: "Marc D.", role: "SaaS B2B", quote: "Le cockpit MyExtension AI m\u2019a fait gagner 12h par semaine. C\u2019est plus qu\u2019un outil, c\u2019est une boussole." },
  { name: "Aïcha B.", role: "Coach indépendante", quote: "Le groupement a changé mon rapport au métier. Je décide mieux, je m\u2019épuise moins." },
];

const Testimonials = () => (
  <section className="py-24 bg-canvasSoft border-y border-outline" data-testid="testimonials">
    <div className="max-w-7xl mx-auto px-6 lg:px-10">
      <div className="text-center mb-12 max-w-2xl mx-auto">
        <div className="text-xs uppercase tracking-[0.18em] text-aubergine/70 mb-3">Ils nous font confiance</div>
        <h2 className="font-display italic" style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", color: "var(--zayado-text)" }}>
          Des entrepreneurs <span className="text-aubergine">apaisés.</span>
        </h2>
      </div>
      <div className="grid md:grid-cols-3 gap-5">
        {TESTIS.map((t, i) => (
          <div key={i} className="bg-white border border-outline rounded-3xl p-7" data-testid={`testimonial-${i}`}>
            <Quote className="w-6 h-6 text-aubergine/60 mb-4" />
            <p className="text-ink/85 text-[15px] leading-relaxed mb-6">&laquo;&nbsp;{t.quote}&nbsp;&raquo;</p>
            <div className="flex items-center gap-3 pt-3 border-t border-outline">
              <div className="w-10 h-10 rounded-full bg-aubergine text-cream flex items-center justify-center text-sm">{t.name[0]}</div>
              <div>
                <div className="text-sm text-ink">{t.name}</div>
                <div className="text-xs text-inkMuted">{t.role}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="text-center mt-10 flex items-center justify-center gap-2 text-sm text-inkMuted">
        <Star className="w-4 h-4 fill-gold text-gold" /> 4,9/5 · +2 000 entrepreneurs accompagnés ·
        <ShieldCheck className="w-4 h-4 text-aubergine" /> RGPD strict
      </div>
    </div>
  </section>
);

// ──────────────────────────────────────────────────────
// FINAL CTA (gradient navy)
// ──────────────────────────────────────────────────────
const FinalCTA = () => (
  <section className="py-24" data-testid="final-cta">
    <div className="max-w-5xl mx-auto px-6">
      <div
        className="relative rounded-[36px] text-cream p-12 lg:p-16 overflow-hidden"
        style={{ background: "var(--zayado-navy-gradient)" }}
      >
        <div className="absolute -top-20 -right-20 w-72 h-72 rounded-full bg-gold-soft/15 blur-3xl" />
        <div className="absolute -bottom-10 -left-10 w-48 h-48 rounded-full bg-cream/5 blur-3xl" />
        <div className="relative">
          <h2 className="font-display italic max-w-2xl leading-[1.02]" style={{ fontSize: "clamp(2rem, 5vw, 3.5rem)" }}>
            Trois portes. <span className="text-gold-soft">Un seul foyer.</span>
          </h2>
          <p className="mt-5 text-cream/75 max-w-md text-lg">
            Commencez par celle qui vous attire le plus aujourd&apos;hui. Les trois communiquent entre elles.
          </p>
          <div className="mt-10 flex flex-wrap gap-3">
            <Link to="/boutique" data-testid="final-cta-shop" className="inline-flex items-center gap-2.5 bg-cream text-navy pl-5 pr-3 py-3 rounded-full hover:bg-gold-soft transition group">
              Boutique
              <span className="w-8 h-8 rounded-full bg-navy text-cream flex items-center justify-center group-hover:translate-x-1 transition">
                <ArrowRight className="w-4 h-4" />
              </span>
            </Link>
            <Link to="/myextension-ai" data-testid="final-cta-app" className="inline-flex items-center gap-2.5 border border-cream/30 text-cream pl-5 pr-3 py-3 rounded-full hover:bg-cream/10 transition group">
              App MyExtension AI
              <span className="w-8 h-8 rounded-full bg-cream/10 flex items-center justify-center">
                <ArrowRight className="w-4 h-4" />
              </span>
            </Link>
            <Link to="/contact" data-testid="final-cta-group" className="inline-flex items-center gap-2.5 border border-cream/30 text-cream pl-5 pr-3 py-3 rounded-full hover:bg-cream/10 transition group">
              Groupement
              <span className="w-8 h-8 rounded-full bg-cream/10 flex items-center justify-center">
                <ArrowRight className="w-4 h-4" />
              </span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  </section>
);

// ──────────────────────────────────────────────────────
// EXPORT
// ──────────────────────────────────────────────────────
export default function Landing() {
  return (
    <div className="min-h-screen bg-canvas" data-testid="landing-hub-page">
      <Helmet>
        <title>Zayado — Entreprendre avec calme. Boutique · App IA · Groupement</title>
        <meta name="description" content="La maison des entrepreneurs apaisés : boutique d'outils, app IA MyExtension AI, groupement. Trois territoires complémentaires pour bâtir sans s'épuiser." />
        <meta property="og:title" content="Zayado — Entreprendre avec calme" />
        <meta property="og:description" content="Boutique · App MyExtension AI · Groupement. Trois portes, un seul foyer." />
        <link rel="canonical" href="https://zayado.net/" />
      </Helmet>
      <Header />
      <main>
        <Hero />
        <Universes />
        <Integrations />
        <Testimonials />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}

// Re-exports pour réutilisation sur les autres pages publiques
export { Header as LeanJourneyHeader, Footer as LeanJourneyFooter };
