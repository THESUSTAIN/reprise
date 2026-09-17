/**
 * /valider-son-projet — Page conversion "Validez votre projet, avancez avec confiance".
 * Test interactif dans le hero : l'utilisateur saisit son idée + choisit canal,
 * la soumission le redirige vers le Cockpit qui lance la discovery IA.
 * Header local custom + UnifiedFooter partagé.
 */
import React, { useState } from "react";
import { SAAS_URL } from "@/lib/api";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import {
  ArrowRight, CheckCircle2, Edit3, Sparkles, PieChart, Check,
  Box, TrendingUp, Users, Heart, Globe, MapPin, Loader2,
} from "lucide-react";
import { UnifiedFooter } from "@/pages/LandingHub";


const WHATSSAAS_URL = "https://wa.me/33183643999?text=Bonjour%20Zayado";

const EXAMPLES = [
  "AI tutor pour développeurs seniors",
  "Box d'abonnement café de spécialité",
  "App de matching co-fondateurs",
  "CRM pour thérapeutes indépendants",
];

// ── Header local ───────────────────────────────────────
const PageHeader = () => (
  <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-[var(--zayado-border)]" data-testid="valider-header">
    <div className="max-w-[1280px] mx-auto px-4 md:px-6 py-4 flex items-center justify-between gap-6">
      <Link to="/" className="font-display italic text-2xl md:text-3xl tracking-tight shrink-0"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)", color: "var(--zayado-navy)" }}>
        Zayado
      </Link>
      <nav className="hidden md:flex items-center gap-6 text-sm" style={{ color: "var(--zayado-text)" }}>
        <a href="#methode" className="hover:opacity-70">Méthode</a>
        <a href="#solutions" className="hover:opacity-70">Solutions</a>
        <a href="#tarifs" className="hover:opacity-70">Tarifs</a>
      </nav>
      <a href={WHATSSAAS_URL} target="_blank" rel="noopener noreferrer" data-testid="header-whatsapp-contact"
         className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-white text-sm font-medium hover:opacity-90 transition"
         style={{ background: "#25D366" }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0 0 20.464 3.488"/></svg>
        Contact
      </a>
    </div>
  </header>
);

// ── HERO + Test interactif ────────────────────────────
const Hero = () => {
  const [idea, setIdea] = useState("");
  const [channel, setChannel] = useState("both");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!idea.trim() || idea.trim().length < 10) {
      setError("Décrivez votre idée en quelques phrases (10 caractères minimum).");
      return;
    }
    setError("");
    setLoading(true);
    // Redirige vers le Cockpit : l'utilisateur se connecte/inscrit, et le Cockpit
    // pré-remplit son formulaire de discovery avec idea + channel.
    const params = new URLSearchParams({
      next: "/app/valider-mon-projet",
      idea: idea.trim(),
      channel,
    });
    window.location.href = `${SAAS_URL}?${params.toString()}`;
  };

  return (
    <section id="hero" className="relative overflow-hidden pt-14 pb-20" style={{ background: "var(--zayado-cream)" }} data-testid="vp-hero">
      <div className="relative max-w-[1100px] mx-auto px-4 md:px-8">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--zayado-gold-bg)] border border-[var(--zayado-gold-soft)]/40 text-[11px] uppercase tracking-[0.22em] mb-6"
               style={{ color: "var(--zayado-gold)" }}>
            <CheckCircle2 size={13} /> Discovery · ~45s · 12 frameworks
          </div>
          <h1 className="font-display italic mb-5"
              style={{ fontSize: "clamp(2.4rem, 6vw, 4.4rem)", lineHeight: "1.02", color: "var(--zayado-navy)" }}>
            <em>Validez</em> avant de <em>construire.</em>
          </h1>
          <p className="text-base md:text-lg max-w-2xl mx-auto leading-relaxed" style={{ color: "var(--zayado-muted)" }}>
            Décrivez votre idée. Zayado exécute 12 frameworks de discovery, révèle les vrais signaux marché
            et cartographie le problème sous votre solution.
          </p>
        </div>

        {/* Formulaire test */}
        <form onSubmit={handleSubmit} className="max-w-2xl mx-auto" data-testid="vp-form">
          {/* Choix canal */}
          <div className="mb-5">
            <div className="text-xs uppercase tracking-[0.18em] mb-3" style={{ color: "var(--zayado-muted)" }}>
              Où chercher les signaux marché ?
            </div>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: "both", icon: Sparkles, label: "Les deux", desc: "En ligne + terrain" },
                { id: "online", icon: Globe, label: "En ligne", desc: "Reddit, HN, LinkedIn" },
                { id: "field", icon: MapPin, label: "Terrain", desc: "INSEE, BPI, presse" },
              ].map((c) => {
                const I = c.icon;
                const active = channel === c.id;
                return (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => setChannel(c.id)}
                    data-testid={`vp-channel-${c.id}`}
                    aria-pressed={active}
                    className="rounded-xl p-3 text-left transition-all border"
                    style={{
                      background: active ? "var(--zayado-navy)" : "white",
                      color: active ? "white" : "var(--zayado-text)",
                      borderColor: active ? "var(--zayado-navy)" : "var(--zayado-border)",
                      boxShadow: active ? "0 6px 16px rgba(26,58,110,0.18)" : "none",
                    }}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <I size={14} style={{ color: active ? "var(--zayado-gold-soft)" : "var(--zayado-gold)" }} />
                      <span className="text-sm font-medium">{c.label}</span>
                    </div>
                    <div className="text-[11px]" style={{ color: active ? "rgba(255,255,255,0.7)" : "var(--zayado-muted)" }}>{c.desc}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Textarea idée */}
          <div className="relative bg-white rounded-2xl border border-[var(--zayado-border)] shadow-[0_10px_40px_-20px_rgba(74,30,44,0.18)] overflow-hidden">
            <textarea
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              placeholder="Décrivez votre idée en quelques phrases — ce que vous voulez résoudre, pour qui, comment…"
              rows={4}
              className="w-full px-5 py-4 text-sm resize-none focus:outline-none placeholder:text-[var(--zayado-muted)]/70"
              style={{ color: "var(--zayado-text)" }}
              data-testid="vp-idea-input"
              autoFocus
            />
            <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--zayado-border)] bg-[var(--zayado-cream)]">
              <div className="text-[11px]" style={{ color: "var(--zayado-muted)" }}>
                {idea.length} caractères · gratuit · sans CB
              </div>
              <button
                type="submit"
                disabled={loading}
                data-testid="vp-cta-start"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-white font-medium text-sm hover:opacity-90 transition disabled:opacity-50"
                style={{ background: "var(--zayado-navy)" }}
              >
                {loading ? <><Loader2 size={14} className="animate-spin" /> Préparation…</> : <>Lancer la discovery <ArrowRight size={14} /></>}
              </button>
            </div>
          </div>

          {error && <div className="mt-3 text-xs text-red-600 text-center">{error}</div>}

          {/* Examples */}
          <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
            <span className="text-[11px] uppercase tracking-wider" style={{ color: "var(--zayado-muted)" }}>Inspirez-vous :</span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => setIdea(ex)}
                data-testid={`vp-example-${ex.slice(0, 12)}`}
                className="px-3 py-1 rounded-full text-[11px] bg-white border border-[var(--zayado-border)] hover:border-[var(--zayado-navy)]/40 transition"
                style={{ color: "var(--zayado-text)" }}
              >
                {ex}
              </button>
            ))}
          </div>

          {/* Trust */}
          <div className="mt-7 flex flex-wrap items-center justify-center gap-5 text-xs" style={{ color: "var(--zayado-muted)" }}>
            <span className="flex items-center gap-1.5"><Check size={13} style={{ color: "var(--zayado-gold)" }} /> Analyse complète en 45s</span>
            <span className="flex items-center gap-1.5"><Check size={13} style={{ color: "var(--zayado-gold)" }} /> Sans carte bancaire</span>
            <span className="flex items-center gap-1.5"><Check size={13} style={{ color: "var(--zayado-gold)" }} /> 100% privé et sécurisé</span>
          </div>
        </form>
      </div>
    </section>
  );
};

// ── EXEMPLE D'ANALYSE (preview) ───────────────────────
const PreviewExample = () => (
  <section className="py-16 bg-white border-y border-[var(--zayado-border)]" data-testid="vp-preview-example">
    <div className="max-w-[1100px] mx-auto px-4 md:px-8">
      <div className="text-center mb-10">
        <div className="text-xs uppercase tracking-[0.18em] mb-2" style={{ color: "var(--zayado-gold)" }}>Exemple d&apos;analyse</div>
        <h2 className="font-medium tracking-tight" style={{ fontSize: "clamp(1.5rem, 2.8vw, 2rem)", color: "var(--zayado-navy)" }}>
          Voici à quoi ressemble votre rapport.
        </h2>
      </div>
      <div className="bg-white rounded-3xl border border-[var(--zayado-border)] p-7 shadow-[0_20px_60px_-30px_rgba(74,30,44,0.12)] max-w-3xl mx-auto">
        <div className="text-[11px] uppercase tracking-wider mb-1" style={{ color: "var(--zayado-muted)" }}>Projet analysé</div>
        <h3 className="text-base font-medium mb-5" style={{ color: "var(--zayado-navy)" }}>Application de méditation pour les entreprises</h3>
        <div className="flex items-start gap-6 mb-6">
          <div className="relative shrink-0">
            <svg width="100" height="100" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" fill="none" stroke="var(--zayado-cream-dark)" strokeWidth="8" />
              <circle cx="50" cy="50" r="42" fill="none" stroke="var(--zayado-gold)" strokeWidth="8"
                      strokeDasharray={`${(82 / 100) * 264} 264`} strokeLinecap="round" transform="rotate(-90 50 50)" />
              <text x="50" y="48" textAnchor="middle" fontSize="22" fontWeight="500" fill="var(--zayado-navy)">82</text>
              <text x="50" y="65" textAnchor="middle" fontSize="9" fill="var(--zayado-muted)">/100</text>
            </svg>
          </div>
          <div className="flex-1">
            <div className="text-xs mb-1" style={{ color: "var(--zayado-muted)" }}>Potentiel du projet</div>
            <div className="text-sm font-medium mb-2" style={{ color: "#10b981" }}>Très bon potentiel</div>
            <p className="text-xs leading-relaxed" style={{ color: "var(--zayado-muted)" }}>
              Votre projet répond à un vrai besoin et dispose de solides atouts pour réussir.
            </p>
          </div>
        </div>
        <div className="grid sm:grid-cols-2 gap-4 mb-2">
          <div>
            <div className="text-xs font-medium mb-2" style={{ color: "var(--zayado-navy)" }}>Points forts</div>
            <div className="flex flex-wrap gap-2">
              {["Besoin croissant", "Marché porteur", "Impact positif"].map((p) => (
                <span key={p} className="px-3 py-1 rounded-full text-xs" style={{ background: "#e8f5e9", color: "#1f6c3a" }}>{p}</span>
              ))}
            </div>
          </div>
          <div>
            <div className="text-xs font-medium mb-2" style={{ color: "var(--zayado-navy)" }}>Axes d&apos;amélioration</div>
            <div className="flex flex-wrap gap-2">
              {["Acquisition", "Différenciation", "Modèle économique"].map((p) => (
                <span key={p} className="px-3 py-1 rounded-full text-xs" style={{ background: "var(--zayado-gold-bg)", color: "var(--zayado-gold)" }}>{p}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
);

// ── 4 ÉTAPES ─────────────────────────────────────────
const STEPS = [
  { icon: Edit3, title: "Décrivez votre projet", desc: "Répondez à quelques questions sur votre idée, votre marché et vos objectifs." },
  { icon: Sparkles, title: "L'IA analyse votre projet", desc: "Notre IA étudie votre projet sous tous les angles et le compare aux meilleures pratiques du marché." },
  { icon: PieChart, title: "Recevez votre analyse", desc: "Découvrez le score de potentiel, les points forts, les risques et des recommandations concrètes." },
  { icon: CheckCircle2, title: "Passez à l'action", desc: "Accédez à votre plan d'action personnalisé et aux prochaines étapes pour avancer." },
];

const Methode = () => (
  <section id="methode" className="py-20 bg-white" data-testid="vp-methode">
    <div className="max-w-[1280px] mx-auto px-4 md:px-8">
      <h2 className="text-center font-medium tracking-tight mb-2" style={{ fontSize: "clamp(1.6rem, 3vw, 2.2rem)", color: "var(--zayado-navy)" }}>
        Comment ça marche ?
      </h2>
      <p className="text-center text-sm mb-14" style={{ color: "var(--zayado-muted)" }}>
        Valider votre projet en 4 étapes simples
      </p>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 relative">
        {STEPS.map((s, i) => (
          <div key={s.title} className="bg-white rounded-2xl border border-[var(--zayado-border)] p-6 text-center relative">
            <div className="absolute -top-3 left-6 w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-medium"
                 style={{ background: "var(--zayado-navy)" }}>{i + 1}</div>
            <div className="mx-auto w-14 h-14 rounded-2xl flex items-center justify-center mb-4 mt-2"
                 style={{ background: "var(--zayado-gold-bg)", color: "var(--zayado-gold)" }}>
              <s.icon size={22} />
            </div>
            <h3 className="font-medium mb-2 text-sm md:text-base" style={{ color: "var(--zayado-navy)" }}>{s.title}</h3>
            <p className="text-xs leading-relaxed" style={{ color: "var(--zayado-muted)" }}>{s.desc}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

// ── ACCOMPAGNEMENT 4 piliers ─────────────────────────
const PILIERS = [
  { icon: Box, title: "Structuration", desc: "Clarifiez votre idée et votre vision." },
  { icon: TrendingUp, title: "Pilotage", desc: "Suivez vos KPI et prenez les bonnes décisions." },
  { icon: Users, title: "Mise en relation", desc: "Trouvez les bonnes personnes pour aller plus loin." },
  { icon: Heart, title: "Énergie & équilibre", desc: "Entreprenez durablement en prenant soin de votre énergie." },
];

const Accompagnement = () => (
  <section id="solutions" className="py-16" style={{ background: "var(--zayado-cream)" }} data-testid="vp-accompagnement">
    <div className="max-w-[1280px] mx-auto px-4 md:px-8">
      <div className="rounded-3xl p-8 md:p-12 border border-[var(--zayado-border)]" style={{ background: "var(--zayado-cream-dark)" }}>
        <div className="grid lg:grid-cols-12 gap-8 items-start">
          <div className="lg:col-span-4">
            <h3 className="font-medium tracking-tight mb-3" style={{ fontSize: "clamp(1.3rem, 2.2vw, 1.7rem)", color: "var(--zayado-navy)" }}>
              Un accompagnement<br />pensé pour les entrepreneurs
            </h3>
            <p className="text-sm leading-relaxed mb-6" style={{ color: "var(--zayado-muted)" }}>
              Zayado vous aide à transformer vos idées en projets viables et à impact.
            </p>
            <Link to="/myextension-ai" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-white text-sm font-medium hover:opacity-90"
                  style={{ background: "var(--zayado-navy)" }}>
              Découvrir nos solutions <ArrowRight size={14} />
            </Link>
          </div>
          <div className="lg:col-span-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {PILIERS.map((p) => (
              <div key={p.title} className="text-center">
                <div className="mx-auto w-12 h-12 rounded-full flex items-center justify-center mb-3"
                     style={{ background: "var(--zayado-gold-bg)", color: "var(--zayado-gold)" }}>
                  <p.icon size={20} />
                </div>
                <h4 className="font-medium text-sm mb-1" style={{ color: "var(--zayado-navy)" }}>{p.title}</h4>
                <p className="text-xs leading-relaxed" style={{ color: "var(--zayado-muted)" }}>{p.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  </section>
);

// ── CTA final beige ─────────────────────────────────
const FinalCTA = () => (
  <section id="tarifs" className="py-16" style={{ background: "var(--zayado-cream)" }} data-testid="vp-final-cta">
    <div className="max-w-[1280px] mx-auto px-4 md:px-8">
      <div className="rounded-3xl p-10 md:p-14 border border-[var(--zayado-border)] relative overflow-hidden"
           style={{ background: "var(--zayado-cream-dark)" }}>
        <div className="grid md:grid-cols-2 gap-8 items-center">
          <div>
            <h3 className="font-medium tracking-tight mb-3" style={{ fontSize: "clamp(1.5rem, 3vw, 2rem)", color: "var(--zayado-navy)" }}>
              Prêt à valider votre projet ?
            </h3>
            <p className="text-sm md:text-base" style={{ color: "var(--zayado-muted)" }}>
              Rejoignez des milliers d&apos;entrepreneurs qui utilisent déjà Zayado pour construire des projets à succès.
            </p>
          </div>
          <div className="md:text-right">
            <a href={SAAS_URL} className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-white font-medium text-sm hover:opacity-90 transition"
               style={{ background: "var(--zayado-navy)" }} data-testid="vp-final-cta-btn">
              Valider mon projet gratuitement <ArrowRight size={16} />
            </a>
            <p className="text-xs mt-3" style={{ color: "var(--zayado-muted)" }}>Aucune carte bancaire requise</p>
          </div>
        </div>
      </div>
    </div>
  </section>
);

export default function ValiderSonProjet() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--zayado-cream)" }} data-testid="valider-conversion">
      <Helmet>
        <title>Validez votre projet — Analyse IA gratuite en 2 minutes | Zayado</title>
        <meta name="description" content="Décrivez votre idée, recevez en 2 minutes une analyse IA : score de potentiel, points forts, axes d'amélioration, plan d'action. 100% gratuit." />
        <link rel="canonical" href="https://zayado.net/valider-son-projet" />
      </Helmet>
      <PageHeader />
      <main className="flex-1">
        <Hero />
        <PreviewExample />
        <Methode />
        <Accompagnement />
        <FinalCTA />
      </main>
      <UnifiedFooter />
    </div>
  );
}
