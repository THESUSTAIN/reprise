/**
 * /instance-dediee — Offre « Instance Dédiée (Pro/Souverain) ».
 * Cockpit MyExtension AI isolé, MANAGÉ par nous (déploiement 1-clic à venir),
 * abonnement récurrent + BYOK. Style Zayado + Helmet SEO + partie douleur forte.
 */
import React from "react";
import { Helmet } from "react-helmet-async";
import {
  Sparkles, ArrowRight, Lock, ShieldCheck, Globe, ServerCog, Users,
  DatabaseZap, KeyRound, CheckCircle2, Zap, EyeOff, Gauge,
} from "lucide-react";
import ZayadoLayout from "@/components/ZayadoLayout";

const CONTACT = "mailto:contact@zayado.net?subject=Demande%20d'instance%20d%C3%A9di%C3%A9e%20MyExtension%20AI&body=Bonjour%2C%20je%20souhaite%20une%20instance%20d%C3%A9di%C3%A9e.%20Voici%20mon%20activit%C3%A9%20%3A%20";

const PAINS = [
  { icon: EyeOff, title: "Vos données mélangées aux autres", text: "En SaaS classique, vos infos stratégiques cohabitent avec celles de milliers d'inconnus. Pour un pro, ça coince — surtout face à des clients exigeants." },
  { icon: Gauge, title: "Des limites que vous ne maîtrisez pas", text: "Ressources partagées, quotas communs, ralentissements aux heures de pointe : vous subissez la charge des autres." },
  { icon: KeyRound, title: "Zéro contrôle sur vos clés & coûts IA", text: "Vous payez une IA opaque, sans voir ni maîtriser la consommation réelle. Difficile de piloter la dépense." },
];

const PILLARS = [
  { icon: DatabaseZap, title: "Vos données, murées", text: "Une base isolée rien qu'à vous. Rien ne fuit vers d'autres comptes. Idéal pour la confidentialité client et les secteurs réglementés." },
  { icon: ServerCog, title: "Managé par nous, zéro DevOps", text: "On déploie, on met à jour, on sauvegarde, on surveille. Vous n'installez rien, vous ne touchez à aucun serveur." },
  { icon: KeyRound, title: "BYOK — votre clé IA", text: "Branchez votre propre clé (Mammouth, OpenAI…). Vous ne payez que votre consommation réelle, en toute transparence." },
];

export default function InstanceDediee() {
  return (
    <ZayadoLayout>
      <div data-testid="instance-dediee-page">
        <Helmet>
          <title>Instance Dédiée — Votre cockpit MyExtension AI isolé & managé | Zayado</title>
          <meta name="description" content="Une instance MyExtension AI rien qu'à vous : données isolées, hébergée en Europe, managée par nos soins (zéro DevOps), avec votre propre clé IA (BYOK). Setup 149 € + 89 €/mois. Confidentialité niveau pro." />
          <meta name="keywords" content="instance dédiée IA, cockpit business isolé, SaaS entrepreneur souverain, hébergement IA Europe RGPD, BYOK entreprise" />
          <meta property="og:title" content="Instance Dédiée MyExtension AI — isolée & managée | Zayado" />
          <meta property="og:description" content="Votre cockpit IA isolé, hébergé en Europe et managé par nous. Confidentialité pro, zéro DevOps, votre propre clé IA." />
          <link rel="canonical" href="https://zayado.net/instance-dediee" />
        </Helmet>

        {/* HERO */}
        <section className="relative overflow-hidden" style={{ background: "var(--zayado-navy-gradient)" }}>
          <div className="relative max-w-7xl mx-auto px-6 lg:px-10 py-20 md:py-24 text-cream grid lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cream/10 backdrop-blur border border-cream/20 text-[11px] uppercase tracking-[0.25em] mb-6 text-gold-soft">
                <ShieldCheck className="w-3 h-3" /> Offre Pro · Souveraineté
              </div>
              <h1 className="font-display leading-[1.05] mb-6 font-semibold" style={{ fontSize: "clamp(2.2rem, 5vw, 3.8rem)" }}>
                Votre cockpit IA,<br />
                <span className="text-gold-soft">rien qu'à vous.</span>
              </h1>
              <p className="text-base md:text-xl text-cream/85 mb-8 max-w-xl leading-relaxed">
                Une instance MyExtension AI <b className="text-cream">isolée</b>, hébergée en Europe et
                <b className="text-cream"> managée par nous</b>. Vos données murées, votre propre clé IA,
                zéro serveur à gérer. La confidentialité d'un outil sur-mesure, sans le DevOps.
              </p>
              <a href={CONTACT} data-testid="id-hero-cta"
                className="inline-flex items-center gap-2 px-7 py-4 rounded-full bg-cream text-navy font-medium text-sm hover:bg-gold-soft transition">
                <Sparkles className="w-4 h-4" /> Demander mon instance
              </a>
              <p className="mt-3 text-xs text-cream/60 flex items-center gap-1.5">
                <Lock className="w-3 h-3" /> Déploiement accompagné · Résiliable à tout moment
              </p>
            </div>

            {/* Mock : instance isolée */}
            <div className="lg:col-span-5">
              <div className="relative bg-white rounded-3xl shadow-2xl p-6 text-ink max-w-sm mx-auto" data-testid="id-hero-mock">
                <div className="flex items-center gap-3 mb-4">
                  <span className="w-10 h-10 rounded-xl bg-aubergine text-cream flex items-center justify-center"><ServerCog className="w-5 h-5" /></span>
                  <div>
                    <div className="text-sm font-semibold text-ink">votre-marque.myextension.app</div>
                    <div className="text-[11px] text-inkMuted flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-[#5DA271]" /> Instance active · EU</div>
                  </div>
                </div>
                <div className="space-y-2.5">
                  {[
                    { icon: DatabaseZap, t: "Base de données isolée", v: "privée" },
                    { icon: KeyRound, t: "Clé IA (BYOK)", v: "connectée" },
                    { icon: Globe, t: "Hébergement", v: "Europe 🇪🇺" },
                    { icon: ShieldCheck, t: "MAJ & backups", v: "auto" },
                  ].map((x, i) => (
                    <div key={i} className="flex items-center justify-between rounded-xl border border-outline px-3.5 py-2.5">
                      <span className="flex items-center gap-2.5 text-sm text-ink"><x.icon className="w-4 h-4 text-aubergine" />{x.t}</span>
                      <span className="text-xs font-medium text-aubergine">{x.v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* DOULEUR */}
        <section className="py-20 bg-canvasSoft" data-testid="id-pains">
          <div className="max-w-7xl mx-auto px-6 lg:px-10">
            <h2 className="text-center font-display font-semibold mb-3" style={{ fontSize: "clamp(1.6rem, 3.5vw, 2.4rem)", color: "var(--zayado-text)" }}>
              Un SaaS partagé, ça finit par coincer.
            </h2>
            <p className="text-center text-inkMuted mb-12 max-w-2xl mx-auto">
              Quand votre activité devient sérieuse, la mutualisation montre ses limites.
            </p>
            <div className="grid md:grid-cols-3 gap-5">
              {PAINS.map((p, i) => (
                <div key={i} className="bg-white rounded-2xl border border-outline p-6" data-testid={`id-pain-${i}`}>
                  <div className="w-11 h-11 rounded-xl bg-aubergine/10 text-aubergine flex items-center justify-center mb-4"><p.icon className="w-5 h-5" /></div>
                  <h3 className="text-lg font-medium text-ink mb-2">{p.title}</h3>
                  <p className="text-sm text-inkMuted leading-relaxed">{p.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* SOLUTION */}
        <section className="py-20" data-testid="id-pillars">
          <div className="max-w-7xl mx-auto px-6 lg:px-10">
            <div className="text-center mb-12">
              <div className="text-xs uppercase tracking-[0.18em] text-aubergine/70 mb-2">La solution</div>
              <h2 className="font-display font-semibold" style={{ fontSize: "clamp(1.6rem, 3vw, 2.4rem)", color: "var(--zayado-text)" }}>
                L'isolation d'un outil sur-mesure. Sans le DevOps.
              </h2>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {PILLARS.map((p, i) => (
                <div key={i} className="rounded-2xl border border-outline bg-white p-7" data-testid={`id-pillar-${i}`}>
                  <div className="w-12 h-12 rounded-2xl bg-aubergine text-cream flex items-center justify-center mb-4"><p.icon className="w-6 h-6" /></div>
                  <h3 className="text-xl font-medium text-ink mb-2">{p.title}</h3>
                  <p className="text-sm text-inkMuted leading-relaxed">{p.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* PRIX */}
        <section className="py-16" data-testid="id-pricing">
          <div className="max-w-2xl mx-auto px-6">
            <div className="rounded-3xl border-2 border-aubergine/20 bg-white shadow-lg p-8 text-center">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-aubergine/10 text-aubergine text-[11px] uppercase tracking-wider font-semibold mb-4">
                <Zap className="w-3 h-3" /> Instance Dédiée
              </div>
              <div className="flex items-end justify-center gap-1 mb-1">
                <span className="font-display text-6xl leading-none" style={{ color: "var(--zayado-text)" }}>89</span>
                <span className="font-display text-3xl" style={{ color: "var(--zayado-text)" }}>€</span>
                <span className="text-[15px] mb-1 ml-1 text-inkMuted">/ mois</span>
              </div>
              <p className="text-sm text-inkMuted mb-1">+ 149 € de mise en service (déploiement accompagné)</p>
              <p className="text-xs text-inkMuted mb-6">Engagement annuel : −20 % · Clé IA (BYOK) à votre charge · Résiliable à tout moment</p>
              <ul className="text-left space-y-3 mb-8 max-w-sm mx-auto">
                {[
                  "Instance & base de données 100 % isolées",
                  "Hébergement Europe (RGPD)",
                  "Déploiement, mises à jour, backups & supervision par nos soins",
                  "Votre propre clé IA (transparence des coûts)",
                  "Cockpit complet : Vision, Pilotage, Bien-être, Le Point du jour",
                  "Support prioritaire",
                ].map((f, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-ink" data-testid={`id-feat-${i}`}>
                    <span className="w-5 h-5 shrink-0 rounded-md bg-gold/15 text-gold flex items-center justify-center mt-0.5"><CheckCircle2 className="w-3.5 h-3.5" /></span>
                    {f}
                  </li>
                ))}
              </ul>
              <a href={CONTACT} data-testid="id-pricing-cta"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-aubergine text-cream font-medium text-sm hover:bg-aubergine-deep transition">
                Demander mon instance <ArrowRight className="w-4 h-4" />
              </a>
              <p className="text-[11px] text-inkMuted mt-3">Places limitées au lancement — déploiement sous 48-72 h ouvrées.</p>
            </div>
          </div>
        </section>

        {/* SÉCURITÉ */}
        <section className="py-16 bg-navy text-cream" data-testid="id-security">
          <div className="max-w-6xl mx-auto px-6 lg:px-10">
            <div className="grid sm:grid-cols-3 gap-6 text-center">
              {[
                { icon: Lock, t: "Données isolées", d: "Une base rien qu'à vous, chiffrée." },
                { icon: Globe, t: "Hébergé en Europe", d: "Conformité RGPD, serveurs EU." },
                { icon: Users, t: "Managé par nous", d: "Zéro serveur à administrer." },
              ].map((x, i) => (
                <div key={i} data-testid={`id-sec-${i}`}>
                  <x.icon className="w-6 h-6 mx-auto mb-2 text-gold-soft" />
                  <div className="text-sm font-medium mb-1">{x.t}</div>
                  <div className="text-xs text-cream/70">{x.d}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </ZayadoLayout>
  );
}
