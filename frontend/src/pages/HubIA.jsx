import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Sun, Shield, UserPlus, Moon, ArrowUp,
  MessageCircle, Eye, TrendingUp, Wallet, LayoutGrid,
} from "lucide-react";
import "./hubia.css";

/*
  Page "Hub IA" — copie fidèle de la démo Kairos, RECOLORÉE aux couleurs ZAYADO :
    noir → bleu #0B1F3A, boutons → beige #DEC2A3.
  Contenu statique identique à la démo (mêmes horodatages).
  Les interactions (boutons, envoi) seront branchées lors de la fusion complète.
*/

const CONVERSATION = [
  {
    id: "m1", type: "assistant-text", author: "MyExtension AI", time: "08:12",
    text: "Bonjour Alexandre. J'ai veillé sur votre activité cette nuit. Voici votre point du jour.",
  },
  {
    id: "m2", type: "card-day", author: "MyExtension AI", time: "08:12", icon: "sun",
    title: "Point du jour", subtitle: "Mardi 16 juin", badge: "IA",
    body: "3 événements traités automatiquement. 1 décision requiert votre validation.",
    stats: [
      { label: "Prospects", value: "+4", hint: "+18%", tone: "gold" },
      { label: "Trésorerie", value: "84 320 €", hint: "+2 100 €", tone: "gold" },
      { label: "Focus", value: "2h40", hint: "objectif 3h", tone: "muted" },
    ],
  },
  {
    id: "m3", type: "card", author: "MyExtension AI", time: "08:13", icon: "shield",
    title: "Validation requise", subtitle: "Virement fournisseur — Notion Labs",
    body: "Un paiement récurrent de 1 250 € est prêt à être exécuté. Dois-je le confirmer ?",
    primary: "Approuver", secondary: "Reporter",
  },
  {
    id: "m4", type: "user-text", time: "08:14",
    text: "Ajoute Camille Rousseau à mon pipeline de prospection.",
  },
  {
    id: "m5", type: "card", author: "MyExtension AI", time: "08:15", icon: "user",
    title: "Prospect ajouté", subtitle: "Camille Rousseau · CMO @ Lumen", badge: "IA",
    body: "Détecté via LinkedIn. Voulez-vous que je génère une séquence d’approche en 3 messages ?",
    primary: "Générer la séquence", secondary: "Plus tard",
  },
];

const TABS = [
  { id: "hub", label: "Hub IA", Icon: MessageCircle },
  { id: "vision", label: "Vision", Icon: Eye },
  { id: "croissance", label: "Croissance", Icon: TrendingUp },
  { id: "daf", label: "DAF IA", Icon: Wallet },
  { id: "espace", label: "Espace", Icon: LayoutGrid },
];

const CARD_ICONS = { sun: Sun, shield: Shield, user: UserPlus };

function Meta({ author, time }) {
  return (
    <div className="hubia-meta">
      <span className="hubia-dot" />
      <span>{author} · {time}</span>
    </div>
  );
}

function StatTile({ label, value, hint, tone }) {
  return (
    <div className="hubia-tile">
      <div className="hubia-tile-label">{label}</div>
      <div className="hubia-tile-value">{value}</div>
      {hint && <div className={`hubia-tile-hint hubia-tile-hint--${tone}`}>{hint}</div>}
    </div>
  );
}

function ActionCard({ m }) {
  const Icon = CARD_ICONS[m.icon] || Sun;
  return (
    <div className="hubia-block">
      <Meta author={m.author} time={m.time} />
      <div className="hubia-card">
        <div className="hubia-card-head">
          <div className="hubia-card-icon"><Icon size={18} strokeWidth={1.8} /></div>
          <div className="hubia-card-head__text">
            <div className="hubia-card-title">{m.title}</div>
            <div className="hubia-card-subtitle">{m.subtitle}</div>
          </div>
          {m.badge && <span className="hubia-badge">{m.badge}</span>}
        </div>
        {m.body && <p className="hubia-card-body">{m.body}</p>}
        {m.stats && (
          <div className="hubia-stats">
            {m.stats.map((s, i) => <StatTile key={i} {...s} />)}
          </div>
        )}
        {m.primary && (
          <div className="hubia-actions">
            <button className="hubia-btn hubia-btn--primary">{m.primary}</button>
            <button className="hubia-btn hubia-btn--outline">{m.secondary}</button>
          </div>
        )}
      </div>
    </div>
  );
}

function Message({ m }) {
  if (m.type === "user-text") {
    return (
      <div className="hubia-block hubia-block--right">
        <div className="hubia-bubble hubia-bubble--user">{m.text}</div>
      </div>
    );
  }
  if (m.type === "assistant-text") {
    return (
      <div className="hubia-block">
        <Meta author={m.author} time={m.time} />
        <div className="hubia-bubble hubia-bubble--assistant">{m.text}</div>
      </div>
    );
  }
  return <ActionCard m={m} />;
}

export default function HubIA() {
  const navigate = useNavigate();
  const [dark, setDark] = useState(false);
  const [value, setValue] = useState("");
  const [activeTab, setActiveTab] = useState("hub");

  const goTab = (id) => {
    setActiveTab(id);
    const routes = { vision: "/vision", croissance: "/croissance", daf: "/pilotage", espace: "/contexte" };
    if (routes[id]) navigate(routes[id]);
  };

  return (
    <div className="hubia-root">
      <div className="hubia-page">
        <header className="hubia-header">
          <div className="hubia-header__left">
            <div className="hubia-logo" aria-hidden="true"><span /><span /><span /></div>
            <div>
              <div className="hubia-title">Hub IA</div>
              <div className="hubia-subtitle">Votre extension intelligente</div>
            </div>
          </div>
          <button className="hubia-toggle" onClick={() => setDark((d) => !d)} aria-label="Thème">
            {dark ? <Sun size={18} strokeWidth={1.8} /> : <Moon size={18} strokeWidth={1.8} />}
          </button>
        </header>

        <main className="hubia-thread">
          {CONVERSATION.map((m) => <Message key={m.id} m={m} />)}
        </main>

        <div className="hubia-input">
          <div className="hubia-pill">
            <input
              className="hubia-field"
              placeholder="Écrivez à votre assistant…"
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
            <button className="hubia-send" aria-label="Envoyer"><ArrowUp size={20} strokeWidth={2} /></button>
          </div>
        </div>

        <nav className="hubia-tabs">
          {TABS.map(({ id, label, Icon }) => {
            const active = activeTab === id;
            return (
              <button key={id} className={`hubia-tab ${active ? "hubia-tab--active" : ""}`} onClick={() => goTab(id)}>
                <Icon size={21} strokeWidth={active ? 2 : 1.7} />
                <span className="hubia-tab-label">{label}</span>
                {active && <span className="hubia-tab-dot" />}
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
