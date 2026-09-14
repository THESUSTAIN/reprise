/**
 * /vision — Page de conversion Vision Board (sans header/footer).
 * Inspirée de la maquette utilisateur (style violet → adapté en bleu Zayado).
 */
import React, { useState } from "react";
import { Helmet } from "react-helmet-async";
import { Sparkles, Lock, Gift, CheckCircle2, ArrowRight, Star, ShieldCheck, Globe, HeartHandshake } from "lucide-react";
import ZayadoLayout from "@/components/ZayadoLayout";

const APP_URL = "https://app.zayado.net/login";

const TESTIMONIALS = [
  { name: "Sarah L.", role: "Fondatrice · Agence Digitale", impact: "+1,8M€ de CA en 3 ans", initial: "S" },
  { name: "Marc D.", role: "CEO · SaaS B2B", impact: "Exit réussie en 2024", initial: "M" },
  { name: "Aïcha B.", role: "Consultante & Formatrice", impact: "Liberté géographique", initial: "A" },
  { name: "Thomas R.", role: "E-commerce", impact: "+700K€ de CA en 2 ans", initial: "T" },
  { name: "Julie T.", role: "Coach & Mentore", impact: "Impact sur +10K vies", initial: "J" },
];

export default function Vision() {
  const [priorite, setPriorite] = useState("");
  const [vision3, setVision3] = useState("");
  const [domaine, setDomaine] = useState("");

  const ready = priorite && vision3 && domaine;

  return (
    <ZayadoLayout>
      <div data-testid="vision-conversion">
      <Helmet>
        <title>Vision Board IA — Projetez votre avenir en 2 minutes | Zayado</title>
        <meta name="description" content="Générez votre Vision Board en 2 minutes. SWOT, 5 piliers, trajectoire. Aucun paiement requis pour l'aperçu. +2 000 entrepreneurs accompagnés." />
        <meta property="og:title" content="Vision Board IA — Zayado" />
        <meta property="og:description" content="Découvrez votre trajectoire entrepreneuriale par l'IA." />
        <link rel="canonical" href="https://zayado.net/vision" />
        <script type="application/ld+json">{JSON.stringify({
          "@context": "https://schema.org",
          "@type": "Product",
          name: "Vision Board IA Zayado",
          description: "Générez votre Vision Board entrepreneurial en 2 minutes",
          aggregateRating: { "@type": "AggregateRating", ratingValue: "4.9", reviewCount: "2000" },
        })}</script>
      </Helmet>

      {/* HERO — gradient navy */}
      <section className="relative overflow-hidden" style={{background: "var(--zayado-navy-gradient)"}}>
        <div className="absolute inset-0 opacity-10" style={{
          backgroundImage: "url('https://images.unsplash.com/photo-1499209974431-9dddcece7f88?auto=format&w=1800&q=80')",
          backgroundSize: "cover", mixBlendMode: "overlay",
        }} />
        <div className="relative max-w-7xl mx-auto px-6 lg:px-10 py-20 md:py-28 text-cream">
          <div className="grid lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-7">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cream/10 backdrop-blur border border-cream/20 text-[11px] uppercase tracking-[0.25em] mb-6 text-gold-soft">
                <Sparkles className="w-3 h-3" />
                Vision Board Public · Zayado
              </div>
              <h1 className="font-display italic leading-[1.02] mb-6" style={{fontSize: "clamp(2.4rem, 6vw, 4.4rem)"}}>
                Découvrez. Inspirez-vous.<br/>
                <em className="text-gold-soft not-italic font-display italic">Projetez</em> votre avenir.
              </h1>
              <p className="text-base md:text-xl text-cream/85 mb-8 max-w-xl leading-relaxed">
                Explorez les Vision Boards d&apos;entrepreneurs à succès qui ont défini leur vision… et la réalisent. Puis créez la vôtre en <b className="text-cream">2 minutes</b>.
              </p>
              <a
                href={APP_URL}
                data-testid="vision-hero-cta"
                className="inline-flex items-center gap-2 px-7 py-4 rounded-full bg-cream text-navy font-medium text-sm hover:bg-gold-soft transition"
              >
                <Sparkles className="w-4 h-4" />
                Générer un aperçu de mon Vision Board en 2 minutes
              </a>
              <p className="mt-3 text-xs text-cream/60 flex items-center gap-1.5">
                <Lock className="w-3 h-3" /> Aucun paiement requis pour l&apos;aperçu
              </p>
            </div>
            <div className="lg:col-span-5 hidden lg:block">
              {/* Decorative blurred cards */}
              <div className="relative">
                {[0,1,2].map((i) => (
                  <div key={i} className="absolute rounded-2xl bg-cream/10 backdrop-blur border border-cream/15 p-4"
                    style={{
                      top: `${i*40}px`, left: `${i*60}px`,
                      width: "240px", transform: `rotate(${(i-1)*4}deg)`,
                    }}>
                    <div className="text-[10px] uppercase tracking-wider text-gold-soft mb-2">Vision 3 ans</div>
                    <div className="space-y-1.5">
                      <div className="h-1.5 bg-cream/20 rounded-full w-3/4" />
                      <div className="h-1.5 bg-cream/20 rounded-full w-1/2" />
                      <div className="h-1.5 bg-cream/20 rounded-full w-2/3" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="py-20 bg-canvasSoft" data-testid="vision-testimonials">
        <div className="max-w-7xl mx-auto px-6 lg:px-10">
          <h2 className="text-center font-display italic mb-3" style={{fontSize: "clamp(1.6rem, 3.5vw, 2.4rem)", color: "var(--zayado-text)"}}>
            Des trajectoires <em className="text-aubergine">réelles</em>. Des résultats <em className="text-aubergine">concrets</em>.
          </h2>
          <p className="text-center text-inkMuted mb-12 max-w-2xl mx-auto">
            Vision Boards partagés par des entrepreneurs inspirants.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {TESTIMONIALS.map((t, i) => (
              <div key={i} className="bg-white rounded-2xl border border-outline overflow-hidden hover:border-aubergine/30 transition group" data-testid={`vision-card-${i}`}>
                <div className="aspect-[3/4] bg-gradient-to-br from-aubergine/15 via-aubergine/8 to-canvasSoft p-4 relative">
                  <div className="text-[10px] uppercase tracking-wider text-aubergine/70 mb-2">Vision 3 ans</div>
                  <div className="space-y-1.5 mb-3">
                    <div className="h-1.5 bg-aubergine/20 rounded-full w-3/4" />
                    <div className="h-1.5 bg-aubergine/20 rounded-full w-1/2" />
                    <div className="h-1.5 bg-aubergine/20 rounded-full w-2/3" />
                  </div>
                  <div className="absolute inset-x-4 bottom-3 bg-white/80 backdrop-blur rounded-lg p-2">
                    <div className="text-[9px] text-inkMuted">SWOT · 5 piliers · CA</div>
                  </div>
                </div>
                <div className="p-4 text-center border-t border-outline">
                  <div className="w-9 h-9 rounded-full bg-aubergine text-cream flex items-center justify-center mx-auto mb-2 text-sm font-medium">
                    {t.initial}
                  </div>
                  <div className="text-sm font-medium text-ink">{t.name}</div>
                  <div className="text-[11px] text-inkMuted mb-2">{t.role}</div>
                  <div className="text-[11px] text-aubergine font-medium border-t border-outline pt-2">{t.impact}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* INTERACTIVE PREVIEW */}
      <section className="py-20" data-testid="vision-form">
        <div className="max-w-6xl mx-auto px-6 lg:px-10">
          <div className="grid lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-4">
              <div className="text-xs uppercase tracking-[0.18em] text-aubergine/70 mb-2">Aperçu instantané</div>
              <h2 className="font-display italic mb-6" style={{fontSize: "clamp(1.6rem, 3vw, 2.2rem)", color: "var(--zayado-text)"}}>
                Votre Vision Board <em className="text-aubergine">en 3 questions</em>.
              </h2>
              <div className="space-y-5">
                {[
                  { n: 1, label: "Quelle est votre priorité n°1 aujourd'hui ?", placeholder: "Ex : Développer mon business", val: priorite, setVal: setPriorite },
                  { n: 2, label: "Où vous voyez-vous dans 3 ans ?", placeholder: "Ex : Indépendant avec une équipe", val: vision3, setVal: setVision3 },
                  { n: 3, label: "Quel domaine souhaitez-vous renforcer ?", placeholder: "Ex : Finance, Leadership, Santé", val: domaine, setVal: setDomaine },
                ].map((q) => (
                  <div key={q.n} className="flex gap-3">
                    <div className="w-7 h-7 shrink-0 rounded-full bg-aubergine/10 text-aubergine flex items-center justify-center text-xs font-medium">{q.n}</div>
                    <div className="flex-1">
                      <label className="block text-sm text-ink mb-2">{q.label}</label>
                      <input
                        value={q.val}
                        onChange={(e) => q.setVal(e.target.value)}
                        placeholder={q.placeholder}
                        className="w-full px-3 py-2 rounded-lg border border-outline bg-white text-sm focus:outline-none focus:border-aubergine/50"
                        data-testid={`vision-input-${q.n}`}
                      />
                    </div>
                  </div>
                ))}
                <a
                  href={APP_URL}
                  data-testid="vision-generate-cta"
                  className={`mt-2 w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-full font-medium text-sm transition ${ready ? "bg-aubergine text-cream hover:bg-aubergine-deep" : "bg-aubergine/30 text-cream/70 cursor-not-allowed"}`}
                >
                  <Sparkles className="w-4 h-4" />
                  Générer mon aperçu
                </a>
              </div>
            </div>
            <div className="lg:col-span-5">
              <div className="aspect-[3/4] rounded-2xl bg-gradient-to-br from-aubergine/15 to-canvasSoft border border-outline p-6 relative overflow-hidden">
                <div className="text-[10px] uppercase tracking-wider text-aubergine/70 mb-2">Vision 3 ans</div>
                <div className="space-y-2 mb-6">
                  {[80, 65, 70].map((w, i) => <div key={i} className="h-2 bg-aubergine/20 rounded-full" style={{width:`${w}%`}} />)}
                </div>
                <div className="bg-white/70 backdrop-blur rounded-xl p-4 mb-4">
                  <div className="text-[11px] uppercase tracking-wider text-inkMuted mb-2">SWOT</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div><div className="text-aubergine font-medium">Forces</div><div className="text-inkMuted">Déterminé · Créatif</div></div>
                    <div className="opacity-40"><div className="text-aubergine font-medium">Faiblesses</div><div className="text-inkMuted">●●● ●●●</div></div>
                  </div>
                </div>
                <div className="bg-white/70 backdrop-blur rounded-xl p-4">
                  <div className="text-[11px] uppercase tracking-wider text-inkMuted mb-2">Équilibre des 5 piliers</div>
                  <div className="flex justify-around items-end h-12">
                    {[70, 80, 60, 75, 65].map((h, i) => <div key={i} className="w-6 bg-aubergine/40 rounded-t" style={{height:`${h}%`}} />)}
                  </div>
                </div>
                <div className="absolute inset-0 bg-canvasSoft/40 backdrop-blur-sm flex items-center justify-center opacity-0 hover:opacity-100 transition">
                  <div className="text-center"><Lock className="w-6 h-6 text-aubergine mx-auto mb-2" /><div className="text-sm text-aubergine font-medium">Débloquez voir plus</div></div>
                </div>
              </div>
            </div>
            <div className="lg:col-span-3">
              <div className="bg-aubergine text-cream rounded-2xl p-6 text-center">
                <Gift className="w-10 h-10 mx-auto mb-3 text-gold-soft" />
                <div className="text-[11px] uppercase tracking-wider text-cream/70 mb-1">Votre aperçu est prêt !</div>
                <h3 className="font-display italic mb-2" style={{fontSize: "1.4rem"}}>Débloquez votre Co-Pilot Vision Board complet</h3>
                <ul className="text-xs text-cream/85 space-y-1.5 text-left mb-5">
                  {["Vision Board complet & personnalisé", "SWOT détaillé", "Équilibre des 5 piliers", "Lié à vos actions quotidiennes", "Suivi de progression intelligent"].map((b, i) => (
                    <li key={i} className="flex items-center gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-gold-soft shrink-0" />{b}</li>
                  ))}
                </ul>
                <a href={APP_URL} className="block w-full bg-cream text-aubergine text-sm font-medium py-2.5 rounded-full hover:bg-gold-soft transition" data-testid="vision-unlock-cta">
                  Rejoindre MyExtension AI
                </a>
                <p className="text-[10px] text-cream/60 mt-2">Essai gratuit · Sans engagement</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* TRUST */}
      <section className="py-16 bg-canvasSoft border-t border-outline" data-testid="vision-trust">
        <div className="max-w-7xl mx-auto px-6 lg:px-10">
          <p className="text-center font-display italic mb-10" style={{fontSize: "clamp(1.4rem, 2.5vw, 1.8rem)", color: "var(--zayado-text)"}}>
            Rejoignez les milliers d&apos;entrepreneurs qui construisent leur avenir avec clarté.
          </p>
          <div className="grid sm:grid-cols-4 gap-6 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <span className="text-2xl font-medium text-ink">4,9/5</span>
                <Star className="w-4 h-4 fill-gold text-gold" />
              </div>
              <div className="text-xs text-inkMuted">+2 000 entrepreneurs</div>
            </div>
            <div className="text-center"><ShieldCheck className="w-6 h-6 mx-auto mb-1 text-aubergine" /><div className="text-xs text-ink">Sécurisé & confidentiel</div></div>
            <div className="text-center"><Globe className="w-6 h-6 mx-auto mb-1 text-aubergine" /><div className="text-xs text-ink">Données hébergées en Europe</div></div>
            <div className="text-center"><HeartHandshake className="w-6 h-6 mx-auto mb-1 text-aubergine" /><div className="text-xs text-ink">Support humain 7j/7</div></div>
          </div>
        </div>
      </section>

      {/* Footer Zayado fourni par ZayadoLayout */}
      </div>
    </ZayadoLayout>
  );
}
