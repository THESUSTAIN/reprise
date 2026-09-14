/**
 * /echeances — Landing Ads : l'angle « zéro échéance ratée ».
 * Promesse : ne plus jamais oublier une échéance fiscale/sociale.
 * Style Zayado (ZayadoLayout + tokens Tailwind + Helmet SEO).
 */
import React from "react";
import { Helmet } from "react-helmet-async";
import {
  Sparkles, ArrowRight, Lock, ShieldCheck, Globe, CalendarClock,
  BellRing, FileWarning, ListChecks, CheckCircle2, Star, Sunrise,
} from "lucide-react";
import ZayadoLayout from "@/components/ZayadoLayout";

const APP_URL = "https://app.zayado.net/login";

const RISKS = [
  { icon: FileWarning, title: "Pénalités évitables", text: "Une déclaration TVA ou URSSAF oubliée, et c'est majorations et intérêts de retard. De l'argent perdu bêtement." },
  { icon: CalendarClock, title: "La date qui vous échappe", text: "CFE, acomptes IS, cotisations… chaque statut a son calendrier. Impossible de tout garder en tête." },
  { icon: BellRing, title: "Le stress de fin de mois", text: "Cette petite angoisse : « est-ce que j'ai oublié quelque chose ? ». Elle vous suit en permanence." },
];

const DEADLINES = [
  { label: "Déclaration & paiement de la TVA", freq: "Mensuel / trimestriel" },
  { label: "Cotisations URSSAF", freq: "Mensuel ou trimestriel" },
  { label: "Acomptes d'impôt sur les sociétés (IS)", freq: "Trimestriel" },
  { label: "Cotisation Foncière des Entreprises (CFE)", freq: "15 décembre" },
  { label: "Déclaration de revenus", freq: "Mai / juin" },
];

export default function Echeances() {
  return (
    <ZayadoLayout>
      <div data-testid="echeances-page">
        <Helmet>
          <title>Zéro échéance ratée — Rappels fiscaux fiables | MyExtension AI</title>
          <meta name="description" content="Ne ratez plus jamais une échéance fiscale ou sociale. Le Point du jour vous rappelle TVA, URSSAF, CFE, IS au bon moment. Rappels fiables, pas d'hallucination. Essai gratuit." />
          <meta property="og:title" content="Zéro échéance ratée — MyExtension AI" />
          <meta property="og:description" content="Le copilote qui vous rappelle vos échéances fiscales et sociales au bon moment." />
          <link rel="canonical" href="https://zayado.net/echeances" />
        </Helmet>

        {/* HERO */}
        <section className="relative overflow-hidden" style={{ background: "var(--zayado-navy-gradient)" }}>
          <div className="relative max-w-7xl mx-auto px-6 lg:px-10 py-20 md:py-24 text-cream grid lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cream/10 backdrop-blur border border-cream/20 text-[11px] uppercase tracking-[0.25em] mb-6 text-gold-soft">
                <CalendarClock className="w-3 h-3" /> Le Point du jour · MyExtension AI
              </div>
              <h1 className="font-display leading-[1.05] mb-6 font-semibold" style={{ fontSize: "clamp(2.2rem, 5vw, 3.8rem)" }}>
                Zéro échéance ratée.<br />
                <span className="text-gold-soft">Zéro stress fiscal.</span>
              </h1>
              <p className="text-base md:text-xl text-cream/85 mb-8 max-w-xl leading-relaxed">
                TVA, URSSAF, CFE, acomptes IS… Votre copilote vous rappelle chaque échéance
                au bon moment, dès votre connexion. Des rappels <b className="text-cream">fiables</b>,
                jamais inventés.
              </p>
              <a href={APP_URL} data-testid="ec-hero-cta"
                className="inline-flex items-center gap-2 px-7 py-4 rounded-full bg-cream text-navy font-medium text-sm hover:bg-gold-soft transition">
                <Sparkles className="w-4 h-4" /> Ne plus rien oublier — essai gratuit
              </a>
              <p className="mt-3 text-xs text-cream/60 flex items-center gap-1.5">
                <Lock className="w-3 h-3" /> Sans engagement · Sans carte bancaire
              </p>
            </div>

            {/* Mock produit fidèle : bannière « Le Point du jour » du cockpit */}
            <div className="lg:col-span-5">
              <div className="relative bg-white rounded-3xl shadow-2xl p-5 text-ink max-w-sm mx-auto" data-testid="ec-hero-mock">
                <div className="absolute -top-3 -left-3 w-16 h-16 rounded-2xl bg-gold/15 blur-xl" />
                <div className="flex items-center gap-2 mb-4">
                  <span className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: "linear-gradient(135deg,#b89855,#d4b982)", color: "#0c1d33" }}>
                    <Sparkles className="w-4 h-4" />
                  </span>
                  <div>
                    <div className="text-sm font-semibold text-ink">Le Point du jour</div>
                    <div className="text-[11px] text-inkMuted">Vos échéances · lundi 15 juin</div>
                  </div>
                </div>
                <ul className="space-y-2.5">
                  {[
                    { c: "#C7372F", t: "Déclaration TVA", d: "dans 3 jours" },
                    { c: "#E0913A", t: "Cotisations URSSAF", d: "dans 9 jours" },
                    { c: "#5DA271", t: "Acompte IS", d: "dans 21 jours" },
                  ].map((x, i) => (
                    <li key={i} className="flex items-center justify-between rounded-xl border border-outline px-3.5 py-2.5">
                      <span className="flex items-center gap-2.5 text-sm text-ink">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ background: x.c }} />
                        {x.t}
                      </span>
                      <span className="text-xs text-inkMuted">{x.d}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-4 flex items-center justify-between rounded-xl bg-aubergine px-4 py-2.5 text-cream text-sm font-medium">
                  Ouvrir dans le chat <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* RISQUES */}
        <section className="py-20 bg-canvasSoft" data-testid="ec-risks">
          <div className="max-w-7xl mx-auto px-6 lg:px-10">
            <h2 className="text-center font-display font-semibold mb-3" style={{ fontSize: "clamp(1.6rem, 3.5vw, 2.4rem)", color: "var(--zayado-text)" }}>
              Une échéance oubliée coûte cher.
            </h2>
            <p className="text-center text-inkMuted mb-12 max-w-2xl mx-auto">
              Gérer seul son calendrier fiscal, c'est jouer avec le feu. Voici ce que ça évite.
            </p>
            <div className="grid md:grid-cols-3 gap-5">
              {RISKS.map((r, i) => (
                <div key={i} className="bg-white rounded-2xl border border-outline p-6" data-testid={`ec-risk-${i}`}>
                  <div className="w-11 h-11 rounded-xl bg-aubergine/10 text-aubergine flex items-center justify-center mb-4">
                    <r.icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-medium text-ink mb-2">{r.title}</h3>
                  <p className="text-sm text-inkMuted leading-relaxed">{r.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* SOLUTION + LISTE */}
        <section className="py-20" data-testid="ec-solution">
          <div className="max-w-6xl mx-auto px-6 lg:px-10 grid lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-5">
              <div className="text-xs uppercase tracking-[0.18em] text-aubergine/70 mb-2">La solution</div>
              <h2 className="font-display font-semibold mb-4" style={{ fontSize: "clamp(1.6rem, 3vw, 2.4rem)", color: "var(--zayado-text)" }}>
                Toutes vos échéances, au même endroit.
              </h2>
              <p className="text-inkMuted leading-relaxed mb-6">
                Chaque matin, « Le Point du jour » vous accueille avec les échéances qui approchent,
                classées par urgence. Les dates proviennent d'un moteur de règles fiable — jamais
                d'une IA qui hallucine. Vous précisez votre statut, on affine.
              </p>
              <ul className="space-y-2.5">
                {[
                  { icon: Sunrise, t: "Rappel proactif dès la connexion" },
                  { icon: ListChecks, t: "Priorisé par urgence (rouge / orange / vert)" },
                  { icon: ShieldCheck, t: "Sources fiables, pas d'invention" },
                ].map((x, i) => (
                  <li key={i} className="flex items-center gap-3 text-sm text-ink" data-testid={`ec-feat-${i}`}>
                    <span className="w-8 h-8 rounded-lg bg-aubergine/10 text-aubergine flex items-center justify-center shrink-0"><x.icon className="w-4 h-4" /></span>
                    {x.t}
                  </li>
                ))}
              </ul>
            </div>
            <div className="lg:col-span-7">
              <div className="rounded-2xl border border-outline bg-white overflow-hidden shadow-sm">
                <div className="px-5 py-3 border-b border-outline flex items-center gap-2 bg-canvasSoft">
                  <CalendarClock className="w-4 h-4 text-aubergine" />
                  <span className="text-sm font-medium text-ink">Le Point du jour — vos échéances</span>
                </div>
                <ul>
                  {DEADLINES.map((d, i) => (
                    <li key={i} className="flex items-center justify-between px-5 py-3.5 border-b border-outline last:border-0" data-testid={`ec-deadline-${i}`}>
                      <div className="flex items-center gap-3">
                        <span className={`w-2.5 h-2.5 rounded-full ${i === 0 ? "bg-gold" : "bg-aubergine/40"}`} />
                        <span className="text-sm text-ink">{d.label}</span>
                      </div>
                      <span className="text-xs text-inkMuted">{d.freq}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <p className="text-xs text-inkMuted mt-3 flex items-center gap-1.5">
                <ShieldCheck className="w-3 h-3 text-aubergine" /> Dates indicatives adaptées à votre régime dans l'app.
              </p>
            </div>
          </div>
        </section>

        {/* SÉCURITÉ */}
        <section className="py-16 bg-navy text-cream" data-testid="ec-security">
          <div className="max-w-6xl mx-auto px-6 lg:px-10">
            <div className="grid sm:grid-cols-3 gap-6 text-center">
              {[
                { icon: Lock, t: "Données chiffrées", d: "Vos informations sont protégées au repos." },
                { icon: Globe, t: "Hébergé en Europe", d: "Conformité RGPD, serveurs européens." },
                { icon: ShieldCheck, t: "Rappels fiables", d: "Moteur de règles, pas d'hallucination IA." },
              ].map((x, i) => (
                <div key={i} data-testid={`ec-sec-${i}`}>
                  <x.icon className="w-6 h-6 mx-auto mb-2 text-gold-soft" />
                  <div className="text-sm font-medium mb-1">{x.t}</div>
                  <div className="text-xs text-cream/70">{x.d}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA FINAL */}
        <section className="py-20 bg-canvasSoft border-t border-outline" data-testid="ec-cta">
          <div className="max-w-3xl mx-auto px-6 text-center">
            <div className="flex items-center justify-center gap-1 mb-3">
              <span className="text-2xl font-medium text-ink">4,9/5</span>
              <Star className="w-4 h-4 fill-gold text-gold" />
              <span className="text-sm text-inkMuted ml-2">+2 000 indépendants sereins</span>
            </div>
            <h2 className="font-display font-semibold mb-4" style={{ fontSize: "clamp(1.8rem, 4vw, 2.6rem)", color: "var(--zayado-text)" }}>
              Laissez votre copilote gérer le calendrier.
            </h2>
            <p className="text-inkMuted mb-8 max-w-xl mx-auto">
              Concentrez-vous sur votre business. On s'occupe de vous rappeler l'essentiel.
            </p>
            <a href={APP_URL} data-testid="ec-final-cta"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-aubergine text-cream font-medium text-sm hover:bg-aubergine-deep transition">
              Commencer gratuitement <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </section>
      </div>
    </ZayadoLayout>
  );
}
