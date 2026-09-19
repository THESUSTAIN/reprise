import React, { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, ArrowRight, BarChart3, Check, ChevronRight,
  CloudSun, Compass, FileText, Focus, Link2, Loader2, Plus, Quote,
  Share2, Sparkles, Target, TrendingUp, Users, Wallet, Zap,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { visionBrainApi } from "../../lib/finalVisionModuleApi";
import { getCopilotBrief } from "../../lib/api";
import { KeyInsights, QuoteBar } from "../../components/CockpitSections";
import AlignmentCelebration from "../../components/AlignmentCelebration";

const PILLAR_COLOR = {
  Vision: "#E08A4A", Exécution: "#3B6FE0", Finance: "#2FB89A",
  Impact: "#DEC2A3", Énergie: "#E0669A", Croissance: "#4AC0E0",
};

const CARD_ICON = { Vision: Compass, Objectif: Target, CA: Wallet, Impact: TrendingUp, Client: Users };

function PillarRing({ name, value }) {
  const numericValue = Number.isFinite(Number(value)) ? Number(value) : 0;
  const r = 25;
  const circumference = 2 * Math.PI * r;
  const color = PILLAR_COLOR[name] || "#DEC2A3";
  return (
    <div className="vision-pillar-ring" data-testid={`pillar-${name}`}>
      <div className="vision-pillar-ring-graphic">
        <svg viewBox="0 0 60 60" aria-hidden="true">
          <circle cx="30" cy="30" r={r} fill="none" stroke="rgba(255,255,255,0.10)" strokeWidth="5" />
          <circle cx="30" cy="30" r={r} fill="none" stroke={color} strokeWidth="5" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={circumference - (numericValue / 100) * circumference} />
        </svg>
        <strong>{Number.isFinite(Number(value)) ? numericValue : "—"}</strong>
      </div>
      <span>{name}</span>
    </div>
  );
}

function LinkedCard({ card }) {
  const Icon = CARD_ICON[card.type] || Sparkles;
  return (
    <article className="vision-linked-card" data-testid={`linked-card-${card.key}`}>
      <div className="vision-linked-card-type"><Icon size={14} /> {card.type || "Signal"}</div>
      <strong>{card.title || "Donnée à préciser"}</strong>
      <b>{card.value ?? "—"}</b>
      {card.sub && <span>{card.sub}</span>}
      {card.progress != null && <div className="vision-progress"><i style={{ width: `${Math.min(100, Math.max(0, Number(card.progress) || 0))}%` }} /></div>}
    </article>
  );
}

function ClimateCard({ data }) {
  const score = data?.alignment_score;
  const label = data?.live_analysis?.label || "Climat en attente de données";
  const description = data?.live_analysis?.description || "Les connexions réelles préciseront l’état de votre trajectoire.";
  return (
    <section className="vision-climate-card" data-testid="vision-climate-card">
      <div className="vision-climate-atmosphere"><span /><i /><b /></div>
      <div className="vision-climate-content">
        <div className="vision-climate-topline"><span><CloudSun size={15} /> CLIMAT STRATÉGIQUE DU JOUR</span><small>Mis à jour par les données du cockpit</small></div>
        <div className="vision-climate-main"><div><h3>{label}</h3><p>{description}</p></div><div className="vision-climate-score"><strong>{score ?? "—"}</strong><span>{score == null ? "" : "/100"}</span></div></div>
        <div className="vision-climate-bottom"><span><i className="climate-dot" /> Cap stratégique</span><span><AlertTriangle size={13} /> {data?.opportunities?.length || 0} signal{(data?.opportunities?.length || 0) > 1 ? "s" : ""}</span></div>
      </div>
    </section>
  );
}

function MeaningCue({ action, onOpenDecisions }) {
  const hasAction = Boolean(action?.label || action?.title);
  return (
    <article data-testid="vision-meaning-cue">
      <span className="focus-label focus-gold"><Quote size={14} /> REPÈRE DE SENS</span>
      <strong>{hasAction ? "Une priorité utile respecte votre Cap et votre capacité." : "Le Cap reste utile lorsqu’il éclaire une décision concrète."}</strong>
      <p>{hasAction ? "Avant d’agir, vérifiez l’impact recherché, l’énergie disponible et ce que vous choisissez de ne pas faire aujourd’hui." : "Commencez par clarifier ce qui compte, puis choisissez un jalon réaliste plutôt qu’une liste supplémentaire."}</p>
      <button onClick={onOpenDecisions}>{hasAction ? "Relire la décision" : "Clarifier mon Cap"} <ArrowRight size={13} /></button>
    </article>
  );
}

export default function AccueilVision({ onGoCanvas, onNavigateTab }) {
  const [data, setData] = useState(null);
  const [brief, setBrief] = useState(null);
  const [mirror, setMirror] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;
    Promise.allSettled([visionBrainApi.panel(), visionBrainApi.connections(), getCopilotBrief()]).then(([panel, connections, copilot]) => {
      if (!active) return;
      if (panel.status === "fulfilled") setData(panel.value);
      if (connections.status === "fulfilled") setMirror(connections.value);
      if (copilot.status === "fulfilled") setBrief(copilot.value);
    }).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  const pillars = data?.score_business?.pillars || [];
  const linkedCards = data?.linked_cards || [];
  const objectives = data?.objectives || data?.active_objectives || [];
  const opportunities = data?.opportunities || [];
  const actions = data?.actions || data?.next_actions || [];
  const score = data?.alignment_score;
  const delta = data?.delta_week;
  const connectionChain = mirror?.chain || [];
  const hasRealData = Boolean(data);

  const openInspiration = (ask) => {
    window.dispatchEvent(new CustomEvent("cours:open-copilot", { detail: { ask } }));
  };

  const progressLabel = useMemo(() => {
    if (delta == null) return "Premier calcul — pas encore d’historique";
    return `${delta >= 0 ? "+" : ""}${delta} cette semaine`;
  }, [delta]);

  if (loading) return <div className="vision-loading"><Loader2 className="animate-spin" size={17} /> Chargement de votre maison stratégique…</div>;
  if (!hasRealData) return <div className="vision-empty-state"><Sparkles size={20} /><strong>Votre maison stratégique attend ses premières données.</strong><span>Configurez votre Vision et vos objectifs pour commencer.</span><button onClick={onGoCanvas}>Ouvrir le board <ArrowRight size={14} /></button></div>;

  return (
    <div className="vision-home" data-testid="accueil-vision">
      <section className="vision-home-hero" data-testid="accueil-hero">
        <div className="vision-home-hero-copy"><span className="vision-eyebrow"><span /> MAISON STRATÉGIQUE</span></div>
        <div className="vision-home-hero-actions" aria-label="Actions Vision">
          <button className="vision-studio-cta" onClick={onGoCanvas} data-testid="accueil-open-canvas"><Compass size={16} /> Créer dans le Studio <ArrowRight size={15} /></button>
          <button className="vision-action-secondary" onClick={() => onNavigateTab?.("decisions")}><Activity size={15} /> Décisions</button>
          <button className="vision-action-secondary" onClick={() => onNavigateTab?.("pillars")}><Target size={15} /> Piliers</button>
          <button className="vision-action-secondary" onClick={() => navigate("/")}><Focus size={15} /> Mode Focus</button>
        </div>
      </section>

      <section className="vision-trajectory" data-testid="vision-trajectory">
        <div className="vision-section-title"><div><span>Votre trajectoire stratégique</span><small>Vision → Décision → Action</small></div></div>
        <div className="vision-trajectory-grid">
          <article><span className="trajectory-number">01</span><strong>VISION</strong><small>Clarifier le cap</small><div className="trajectory-icon"><CrosshairIcon /></div><div className="trajectory-card"><b>{pillars.length ? `${pillars.length} piliers actifs` : "Piliers à définir"}</b><span>{pillars.length ? pillars.map((p) => p.name).join(" · ") : "Structurez vos axes de décision dans votre Vision."}</span></div></article>
          <article><span className="trajectory-number">02</span><strong>DÉCISION</strong><small>Choisir vos priorités</small><div className="trajectory-icon"><ScaleIcon /></div><div className="trajectory-card"><b>{opportunities.length ? `${opportunities.length} décisions à traiter` : "Décisions à clarifier"}</b><span>Le Copilote aide à hiérarchiser, vous gardez la validation.</span></div></article>
          <article><span className="trajectory-number">03</span><strong>ACTION</strong><small>Exécuter et mesurer</small><div className="trajectory-icon"><Zap size={19} /></div><div className="trajectory-card"><b>{actions.length ? `${actions.length} missions recommandées` : "Missions à préparer"}</b><span>Les missions validées font avancer votre Vision.</span></div></article>
        </div>
        <div className="vision-alignment-row">
          <div><span>ALIGNEMENT GLOBAL</span><strong>{score ?? "—"}<small>{score == null ? "" : "%"}</small></strong><em><Activity size={12} /> {progressLabel}</em></div>
          <div><span>PILIERS STRATÉGIQUES</span><div className="vision-pillar-rings">{pillars.length ? pillars.slice(0, 6).map((p) => <PillarRing key={p.name} name={p.name} value={p.value} />) : <small>Données à renseigner</small>}</div></div>
          <div><span>OBJECTIFS ACTIFS</span>{objectives.length ? objectives.slice(0, 2).map((o, index) => <p key={o.id || index}><i /> {o.title || o.label || "Objectif"}<b>{o.progress ?? "—"}{o.progress != null ? "%" : ""}</b></p>) : <p className="vision-muted">Aucun objectif connecté</p>}</div>
        </div>
        <button className="vision-primary-cta" onClick={onGoCanvas}><Sparkles size={16} /> Piloter depuis ma Vision <ArrowRight size={15} /></button>
      </section>

      <ClimateCard data={data} />

      <section className="vision-focus-grid" data-testid="vision-focus-grid">
        <article><span className="focus-label focus-green"><TrendingUp size={14} /> CE QUI AVANCE</span><strong>{data.live_analysis?.label || "À mesurer"}</strong><p>{data.activity?.[0]?.text || "Les premiers signaux apparaîtront avec vos connexions."}</p><button onClick={() => navigate("/pilotage")}>Voir les indicateurs <ArrowRight size={13} /></button></article>
        <article><span className="focus-label focus-amber"><AlertTriangle size={14} /> CE QUI DÉRIVE</span><strong>{opportunities[0]?.title || "Aucun écart identifié"}</strong><p>{opportunities[0]?.sub || "Le Copilote signalera les écarts dès qu’une donnée réelle sera disponible."}</p><button onClick={() => navigate("/")}>Voir dans le Copilote <ArrowRight size={13} /></button></article>
        <article><span className="focus-label focus-blue"><Target size={14} /> PROCHAINE DÉCISION</span><strong>{actions[0]?.label || actions[0]?.title || "Aucune décision en attente"}</strong><p>{actions[0]?.reason || "Les recommandations seront basées sur votre Vision."}</p><button onClick={() => navigate("/")}>Ouvrir le Copilote <ArrowRight size={13} /></button></article>
        <MeaningCue action={actions[0]} onOpenDecisions={() => onNavigateTab?.("decisions")} />
      </section>

      {linkedCards.length > 0 && <section className="vision-linked-strip" data-testid="accueil-linked-cards"><div className="vision-section-title"><div><span>Cartes intelligentes reliées</span><small>Les données de vos modules alimentent la Vision</small></div><Link2 size={16} /></div><div className="vision-linked-list">{linkedCards.slice(0, 4).map((card) => <LinkedCard key={card.key} card={card} />)}</div></section>}

      {connectionChain.length > 0 && <section className="vision-mirror" data-testid="accueil-mirror"><div className="vision-section-title"><div><span>Miroir dynamique</span><small>Vos connexions alimentent la trajectoire</small></div><Link2 size={16} /></div><div className="vision-mirror-chain">{connectionChain.map((node) => <div key={node.key}><span className={node.connected ? "connected" : ""}>{node.provider}</span><small>{node.connected ? node.value : "Non connecté"}</small></div>)}</div></section>}

      <KeyInsights data={brief} />
      <AlignmentCelebration score={score || 0} />

      <section className="vision-resources" data-testid="vision-resources-inspiration">
        <div className="vision-section-title">
          <div><span>Ressources &amp; Inspiration</span><small>Des angles de travail à ouvrir avec le Copilote, sans contenu fabriqué</small></div>
          <Sparkles size={16} />
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {[
            { key: "life-design", icon: Focus, title: "Design de vie", text: "Clarifier un mode de réussite soutenable et cohérent avec votre énergie.", ask: "Aide-moi à clarifier un design de vie entrepreneurial cohérent avec ma Vision, mes contraintes et mon énergie actuelle." },
            { key: "strategy", icon: TrendingUp, title: "Stratégies", text: "Mettre à l’épreuve une priorité, un positionnement ou une décision.", ask: "Challenge ma stratégie actuelle à partir de ma Vision et propose trois options réalistes avec leurs risques." },
            { key: "tools", icon: Target, title: "Outils utiles", text: "Identifier les outils réellement pertinents avant d’ajouter une nouvelle connexion.", ask: "Quels outils simples et proportionnés pourraient soutenir ma prochaine priorité, sans complexifier mon système ?" },
            { key: "visual-references", icon: Quote, title: "Références visuelles", text: "Transformer une intention de Vision en brief visuel exploitable.", ask: "Transforme mon intention de Vision en brief visuel précis : ambiance, symboles, palette et usages possibles." },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.key} type="button" onClick={() => openInspiration(item.ask)} data-testid={`vision-resource-${item.key}`} className="group rounded-2xl border border-white/10 bg-white/[0.04] p-4 text-left transition hover:border-[#DEC2A3]/50 hover:bg-white/[0.07]">
                <span className="mb-3 inline-flex h-9 w-9 items-center justify-center rounded-xl bg-[#DEC2A3]/15 text-[#E8C96A]"><Icon size={16} /></span>
                <strong className="block text-sm text-white">{item.title}</strong>
                <span className="mt-1 block text-xs leading-relaxed text-white/55">{item.text}</span>
                <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-[#E8C96A]">Ouvrir dans le Copilote <ArrowRight size={13} /></span>
              </button>
            );
          })}
        </div>
      </section>
      <QuoteBar data={brief} />
    </div>
  );
}

function CrosshairIcon() { return <Target size={19} />; }
function ScaleIcon() { return <span className="vision-scale-icon">⚖</span>; }
