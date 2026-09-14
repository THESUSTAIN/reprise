/**
 * /anti-burnout — Landing Ads : l'angle « anti-surcharge ».
 * Promesse : avancer sur sa vision sans se cramer.
 * Style Zayado (ZayadoLayout + tokens Tailwind + Helmet SEO).
 */
import React from "react";
import { Helmet } from "react-helmet-async";
import {
  Sparkles, ArrowRight, Lock, ShieldCheck, Globe, HeartHandshake,
  BatteryLow, BrainCircuit, CalendarCheck, Sunrise, CheckCircle2, Star,
} from "lucide-react";
import ZayadoLayout from "@/components/ZayadoLayout";

const APP_URL = "https://app.zayado.net/login";

const SYMPTOMS = [
  { icon: BrainCircuit, title: "Charge mentale permanente", text: "Trop de décisions, trop d'onglets ouverts dans la tête. Vous ne débranchez jamais vraiment." },
  { icon: BatteryLow, title: "Énergie en chute libre", text: "Vous travaillez plus mais avancez moins. Le carburant baisse et vous l'ignorez." },
  { icon: CalendarCheck, title: "Le flou sur les priorités", text: "Chaque jour commence sans cap clair. Vous éteignez des feux au lieu de construire." },
];

const PILLARS = [
  { icon: Sunrise, title: "Le Point du jour", text: "Chaque matin, votre copilote vous accueille avec vos 3 priorités, vos échéances et votre niveau d'énergie. En 30 secondes, vous savez où mettre votre focus." },
  { icon: HeartHandshake, title: "Check-in bien-être", text: "Un rituel de 10 secondes mesure votre énergie et votre risque de burn-out. L'IA adapte votre charge quand vous approchez de la ligne rouge." },
  { icon: BrainCircuit, title: "L'IA porte le poids", text: "Rédaction, relances, organisation, veille : ce qui vous épuise est délégué. Vous gardez la vision, l'IA gère l'exécution." },
];

export default function AntiBurnout() {
  return (
    <ZayadoLayout>
      <div data-testid="anti-burnout-page">
        <Helmet>
          <title>Anti-burnout entrepreneur — Avancez sans vous cramer | MyExtension AI</title>
          <meta name="description" content="Le copilote IA qui transforme votre vision en actions quotidiennes sans burn-out. Check-in bien-être, priorités claires, l'IA porte la charge. Essai gratuit." />
          <meta property="og:title" content="Anti-burnout entrepreneur — MyExtension AI" />
          <meta property="og:description" content="Avancez sur votre vision sans vous épuiser. Le copilote IA anti-surcharge des indépendants." />
          <link rel="canonical" href="https://zayado.net/anti-burnout" />
        </Helmet>

        {/* HERO */}
        <section className="relative overflow-hidden" style={{ background: "var(--zayado-navy-gradient)" }}>
          <div className="relative max-w-7xl mx-auto px-6 lg:px-10 py-20 md:py-24 text-cream grid lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cream/10 backdrop-blur border border-cream/20 text-[11px] uppercase tracking-[0.25em] mb-6 text-gold-soft">
                <HeartHandshake className="w-3 h-3" /> Anti-surcharge · MyExtension AI
              </div>
              <h1 className="font-display leading-[1.05] mb-6 font-semibold" style={{ fontSize: "clamp(2.2rem, 5vw, 3.8rem)" }}>
                Avancez sur votre vision<br />
                <span className="text-gold-soft">sans vous cramer.</span>
              </h1>
              <p className="text-base md:text-xl text-cream/85 mb-8 max-w-xl leading-relaxed">
                MyExtension AI est le copilote qui transforme votre vision en actions quotidiennes —
                en préservant votre énergie. Moins de charge mentale, plus d'impact.
              </p>
              <a href={APP_URL} data-testid="ab-hero-cta"
                className="inline-flex items-center gap-2 px-7 py-4 rounded-full bg-cream text-navy font-medium text-sm hover:bg-gold-soft transition">
                <Sparkles className="w-4 h-4" /> Reprendre le contrôle — essai gratuit
              </a>
              <p className="mt-3 text-xs text-cream/60 flex items-center gap-1.5">
                <Lock className="w-3 h-3" /> Sans engagement · Sans carte bancaire
              </p>
            </div>

            {/* Mock produit fidèle : check-in bien-être du cockpit */}
            <div className="lg:col-span-5">
              <div className="relative bg-white rounded-3xl shadow-2xl p-6 text-ink max-w-sm mx-auto" data-testid="ab-hero-mock">
                <div className="absolute -top-3 -right-3 w-16 h-16 rounded-2xl bg-gold/15 blur-xl" />
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-10 h-10 rounded-full bg-aubergine text-cream flex items-center justify-center font-medium">M</div>
                  <div>
                    <div className="text-sm font-medium text-ink">Bonjour Margaux 👋</div>
                    <div className="text-xs text-inkMuted">Check-in du matin · 7h12</div>
                  </div>
                </div>
                <div className="rounded-2xl bg-canvasSoft p-4 mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs uppercase tracking-wide text-inkMuted">Énergie du jour</span>
                    <span className="text-sm font-semibold text-aubergine">7,2/10</span>
                  </div>
                  <div className="h-2.5 rounded-full bg-outline overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: "72%", background: "linear-gradient(90deg,#b89855,#d4b982)" }} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div className="rounded-xl border border-outline p-3">
                    <div className="text-[11px] text-inkMuted mb-1">Score bien-être</div>
                    <div className="text-xl font-semibold text-ink">75<span className="text-sm text-inkMuted">/100</span></div>
                  </div>
                  <div className="rounded-xl border border-outline p-3">
                    <div className="text-[11px] text-inkMuted mb-1">Charge du jour</div>
                    <div className="text-sm font-semibold text-aubergine flex items-center gap-1"><CheckCircle2 className="w-4 h-4" /> Équilibrée</div>
                  </div>
                </div>
                <div className="rounded-xl bg-aubergine/5 border border-aubergine/15 p-3 flex items-start gap-2">
                  <BrainCircuit className="w-4 h-4 text-aubergine mt-0.5 shrink-0" />
                  <p className="text-xs text-ink leading-relaxed">L'IA a allégé votre journée : 2 relances et votre veille sont déjà prêtes à valider.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* SYMPTÔMES */}
        <section className="py-20 bg-canvasSoft" data-testid="ab-symptoms">
          <div className="max-w-7xl mx-auto px-6 lg:px-10">
            <h2 className="text-center font-display font-semibold mb-3" style={{ fontSize: "clamp(1.6rem, 3.5vw, 2.4rem)", color: "var(--zayado-text)" }}>
              La croissance ne devrait pas coûter votre santé.
            </h2>
            <p className="text-center text-inkMuted mb-12 max-w-2xl mx-auto">
              Si vous vous reconnaissez ici, vous n'êtes pas seul — et ce n'est pas une fatalité.
            </p>
            <div className="grid md:grid-cols-3 gap-5">
              {SYMPTOMS.map((s, i) => (
                <div key={i} className="bg-white rounded-2xl border border-outline p-6" data-testid={`ab-symptom-${i}`}>
                  <div className="w-11 h-11 rounded-xl bg-aubergine/10 text-aubergine flex items-center justify-center mb-4">
                    <s.icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-medium text-ink mb-2">{s.title}</h3>
                  <p className="text-sm text-inkMuted leading-relaxed">{s.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* SOLUTION */}
        <section className="py-20" data-testid="ab-pillars">
          <div className="max-w-7xl mx-auto px-6 lg:px-10">
            <div className="text-center mb-12">
              <div className="text-xs uppercase tracking-[0.18em] text-aubergine/70 mb-2">Comment ça marche</div>
              <h2 className="font-display font-semibold" style={{ fontSize: "clamp(1.6rem, 3vw, 2.4rem)", color: "var(--zayado-text)" }}>
                Un copilote qui protège votre énergie.
              </h2>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {PILLARS.map((p, i) => (
                <div key={i} className="rounded-2xl border border-outline bg-white p-7" data-testid={`ab-pillar-${i}`}>
                  <div className="w-12 h-12 rounded-2xl bg-aubergine text-cream flex items-center justify-center mb-4">
                    <p.icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-medium text-ink mb-2">{p.title}</h3>
                  <p className="text-sm text-inkMuted leading-relaxed">{p.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* SÉCURITÉ */}
        <section className="py-16 bg-navy text-cream" data-testid="ab-security">
          <div className="max-w-6xl mx-auto px-6 lg:px-10">
            <div className="grid md:grid-cols-2 gap-10 items-center">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cream/10 border border-cream/20 text-[11px] uppercase tracking-[0.25em] mb-5 text-gold-soft">
                  <ShieldCheck className="w-3 h-3" /> Confidentialité
                </div>
                <h2 className="font-display font-semibold mb-4" style={{ fontSize: "clamp(1.6rem, 3vw, 2.2rem)" }}>
                  Vos données de bien-être vous appartiennent.
                </h2>
                <p className="text-cream/80 leading-relaxed">
                  Le module bien-être manipule des données sensibles. Elles sont chiffrées au repos,
                  hébergées en Europe et jamais revendues. Vous consentez explicitement, et vous
                  pouvez tout exporter ou supprimer en un clic.
                </p>
              </div>
              <div className="grid sm:grid-cols-2 gap-4">
                {[
                  { icon: Lock, t: "Chiffrement au repos", d: "Données sensibles protégées (RGPD Art. 9)." },
                  { icon: Globe, t: "Hébergé en Europe", d: "Serveurs européens, conformité RGPD." },
                  { icon: ShieldCheck, t: "Consentement explicite", d: "Vous décidez de ce qui est collecté." },
                  { icon: HeartHandshake, t: "Support humain 7j/7", d: "Une équipe, pas seulement un bot." },
                ].map((x, i) => (
                  <div key={i} className="rounded-2xl bg-cream/5 border border-cream/15 p-5" data-testid={`ab-sec-${i}`}>
                    <x.icon className="w-5 h-5 text-gold-soft mb-3" />
                    <div className="text-sm font-medium mb-1">{x.t}</div>
                    <div className="text-xs text-cream/70">{x.d}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* CTA FINAL */}
        <section className="py-20 bg-canvasSoft border-t border-outline" data-testid="ab-cta">
          <div className="max-w-3xl mx-auto px-6 text-center">
            <div className="flex items-center justify-center gap-1 mb-3">
              <span className="text-2xl font-medium text-ink">4,9/5</span>
              <Star className="w-4 h-4 fill-gold text-gold" />
              <span className="text-sm text-inkMuted ml-2">+2 000 indépendants accompagnés</span>
            </div>
            <h2 className="font-display font-semibold mb-4" style={{ fontSize: "clamp(1.8rem, 4vw, 2.6rem)", color: "var(--zayado-text)" }}>
              Reprenez votre souffle. Gardez votre cap.
            </h2>
            <p className="text-inkMuted mb-8 max-w-xl mx-auto">
              Rejoignez les entrepreneurs qui avancent chaque jour sans s'épuiser.
            </p>
            <ul className="flex flex-wrap justify-center gap-x-6 gap-y-2 mb-8 text-sm text-ink">
              {["Priorités claires chaque matin", "Charge portée par l'IA", "Alerte anti-burn-out"].map((b, i) => (
                <li key={i} className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-aubergine" />{b}</li>
              ))}
            </ul>
            <a href={APP_URL} data-testid="ab-final-cta"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-aubergine text-cream font-medium text-sm hover:bg-aubergine-deep transition">
              Commencer gratuitement <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </section>
      </div>
    </ZayadoLayout>
  );
}
