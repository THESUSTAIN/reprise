import React, { useState } from "react";
import { Bot, Users, Megaphone, Mail, Target, Flame, TrendingUp, ArrowRight, X, ExternalLink } from "lucide-react";

// Modale "Bientôt disponible" pour outils non encore connectés
function ComingSoonModal({ tool, onClose }) {
  if (!tool) return null;
  const Icon = tool.icon;
  return (
    <div className="fixed inset-0 z-50 bg-navy-deep/60 backdrop-blur-sm grid place-items-center p-4" onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} className="bg-cream rounded-3xl p-8 max-w-sm w-full border border-sand-200 shadow-soft text-center">
        <div className="w-14 h-14 rounded-2xl bg-navy text-cream grid place-items-center mx-auto mb-4">
          <Icon size={22} />
        </div>
        <h3 className="font-display text-[22px] text-navy mb-2">{tool.l}</h3>
        <p className="text-[13.5px] text-ink-soft leading-relaxed mb-2">{tool.sub}</p>
        {tool.cta ? (
          <p className="text-[13px] text-ink leading-relaxed mb-5">{tool.cta}</p>
        ) : (
          <p className="text-[13px] text-ink-soft italic mb-5">Fonctionnalité en cours de développement — disponible prochainement.</p>
        )}
        {tool.route ? (
          <button onClick={() => { onClose(); tool.onNav && tool.onNav(tool.route); }} className="w-full px-4 h-11 rounded-full bg-navy text-cream text-[13px] font-semibold hover:bg-navy-bright transition">
            Accéder <ArrowRight size={14} className="inline ml-1" />
          </button>
        ) : null}
        <button onClick={onClose} className="mt-2 w-full px-4 h-10 rounded-full bg-cream-soft text-ink text-[13px]">Fermer</button>
      </div>
    </div>
  );
}

export default function HubView({ data, onOpenChat, onChangeTab }) {
  const [activeModal, setActiveModal] = useState(null);
  const kpis = data?.kpis || { prospects: 0, conversations: 0, leads: 0, rdv: 0 };
  const KPIS = [
    { l: "Prospects",     v: kpis.prospects     ?? 0, d: 0 },
    { l: "Conversations", v: kpis.conversations ?? 0, d: 0 },
    { l: "Leads",         v: kpis.leads         ?? 0, d: 0 },
    { l: "RDV",           v: kpis.rdv           ?? 0, d: 0 },
  ];
  const SOURCES = data?.sources || [];
  const TOOLS = [
    {
      l: "CRM",       icon: Users,     sub: "Gérer prospects & clients",
      cta: "Accédez à vos leads, créez des fiches prospects et suivez votre pipeline depuis l'onglet Terrain.",
      route: "terrain",
    },
    {
      l: "Campagnes", icon: Megaphone, sub: "Emails & relances",
      cta: "Créez des campagnes email via Brevo dans Paramètres → Intégrations → CRM · Leads.",
    },
    {
      l: "Séquences", icon: Mail,      sub: "Automatisations",
      cta: "Activez les automatisations préconfigurées (email bienvenue, relance leads…) dans Paramètres → Automatisations.",
    },
    {
      l: "FAQ Bot",   icon: Bot,       sub: "Réponses auto",
      cta: "Configurez votre Growth Agent pour répondre automatiquement aux questions fréquentes.",
      route: "agent",
    },
    {
      l: "Landing",   icon: Target,    sub: "Pages de conversion",
      cta: "Connectez vos pages de capture via le webhook universel Make/Zapier dans Paramètres.",
    },
    {
      l: "Annonces",  icon: Flame,     sub: "Ads ciblées",
      cta: "Branchez Facebook Ads, Google Ads ou TikTok Ads via un scénario Make vers le webhook universel.",
    },
  ];

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
        {KPIS.map((k) => (
          <div key={k.l} className="card-cream p-5 rise">
            <p className="text-[11.5px] uppercase tracking-[0.2em] text-ink-soft font-semibold">{k.l}</p>
            <p className="font-display text-[34px] text-navy leading-tight mt-1.5">{k.v}</p>
            {k.d ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 mt-1.5 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-semibold">
                <TrendingUp size={11} /> +{k.d}
              </span>
            ) : null}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">
        <div className="lg:col-span-2 card-cream p-7 rise">
          <div className="flex items-center justify-between mb-5">
            <p className="uppercase-eyebrow">Top sources de leads</p>
            <span className="text-[11px] text-ink-soft">7 derniers jours</span>
          </div>
          <ul className="space-y-3">
            {SOURCES.map((s) => (
              <li key={s.name}>
                <div className="flex justify-between text-[13px] mb-1.5">
                  <span className="text-ink font-medium">{s.name}</span>
                  <span className="text-navy font-semibold tabular-nums">{s.count} · {s.pct}%</span>
                </div>
                <div className="h-2 rounded-full bg-sand-200 overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-navy to-navy-bright rounded-full transition-all" style={{ width: `${s.pct}%` }} />
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="card-cream p-7 rise" style={{ animationDelay: "120ms" }}>
          <div className="flex items-center gap-2 mb-3">
            <Bot size={16} className="text-navy" />
            <p className="uppercase-eyebrow">Growth Agent</p>
          </div>
          <p className="font-display text-[20px] text-navy leading-tight">
            Travaille pour vous <span className="font-serif-italic text-gold-deep">en silence</span>.
          </p>
          <ul className="space-y-2 mt-4 text-[13px] text-ink">
            <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-navy" /> En attente de connexion à votre CRM</li>
            <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-navy" /> Activez la veille pour démarrer</li>
            <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-navy" /> Premier rapport sous 24h</li>
          </ul>
          <button onClick={() => onChangeTab("agent")} className="mt-5 w-full inline-flex items-center justify-between px-4 h-11 rounded-2xl bg-cream-soft hover:bg-sand-200 text-navy text-[13.5px] font-semibold transition-colors">
            Voir l&apos;agent <ArrowRight size={15} />
          </button>
        </div>
      </div>

      <div className="card-cream p-7 rise">
        <p className="uppercase-eyebrow mb-4">Outils de croissance</p>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {TOOLS.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.l}
                data-testid={`hub-tool-${t.l.toLowerCase()}`}
                onClick={() => setActiveModal({ ...t, onNav: onChangeTab })}
                className="text-left p-4 rounded-2xl bg-cream-soft border border-sand-200 hover:border-navy/30 transition-all group"
              >
                <span className="w-9 h-9 rounded-xl bg-navy text-cream grid place-items-center group-hover:bg-navy-bright transition-colors">
                  <Icon size={15} />
                </span>
                <p className="font-display text-[15px] text-navy mt-2.5">{t.l}</p>
                <p className="text-[11.5px] text-ink-soft mt-0.5">{t.sub}</p>
              </button>
            );
          })}
        </div>
      </div>

      <ComingSoonModal tool={activeModal} onClose={() => setActiveModal(null)} />
    </>
  );
}
