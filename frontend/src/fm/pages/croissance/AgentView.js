import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@fm/context/AuthContext";
import { growthApi, integrationsApi } from "@fm/lib/api";
import { toast } from "sonner";
import {
  Loader2, Sparkles, Bot, Power, RefreshCw, Activity,
  Search, Zap, ArrowRight, Lock, CheckCircle2,
} from "lucide-react";
import ConversationsMetrics from "./ConversationsMetrics";

const FREQUENCIES = [
  { id: "realtime", label: "Temps réel" },
  { id: "hourly",   label: "Toutes les heures" },
  { id: "daily",    label: "Quotidien" },
  { id: "weekly",   label: "Hebdomadaire" },
];

function ScanField({ label, value, onChange, placeholder = "", select, options = [], testid }) {
  return (
    <label className="block">
      <span className="text-[11px] tracking-[0.18em] uppercase text-ink-soft font-semibold">{label}</span>
      {select ? (
        <select data-testid={testid} value={value} onChange={(e) => onChange(e.target.value)}
          className="mt-1 w-full rounded-xl bg-cream-soft border border-sand-300 px-3 py-2.5 text-[14px] text-ink focus:outline-none focus:border-navy">
          {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      ) : (
        <input data-testid={testid} value={value} onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="mt-1 w-full rounded-xl bg-cream-soft border border-sand-300 px-3 py-2.5 text-[14px] text-ink focus:outline-none focus:border-navy" />
      )}
    </label>
  );
}

function FreeScanView({ onUpgrade }) {
  const [step, setStep] = useState(0);
  const [target, setTarget] = useState({ persona: "", channel: "reddit", keywords: "" });
  const [leads, setLeads] = useState([]);
  const timerRef = React.useRef(null);

  React.useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current); }, []);

  const launch = () => {
    if (!target.persona || !target.keywords) { toast.error("Décris ta cible + 2-3 mots-clés"); return; }
    setStep(1);
    timerRef.current = setTimeout(() => {
      setLeads([
        { name: "Margaux R.", role: "Fondatrice solo · e-commerce", signal: "« Burn-out solo + galère pour structurer la journée »", source: "r/Entrepreneur", score: 92, blurred: false },
        { name: "Thomas L.", role: "Coach business · 1ʳᵉ année", signal: "Cherche un outil pour piloter ses 3 missions par jour…", source: "r/SaaS", score: 81, blurred: true },
        { name: "Sophie K.", role: "Consultante UX freelance", signal: "« Aimerait quelque chose comme Notion mais moins vide »", source: "r/freelance", score: 74, blurred: true },
        { name: "Karim B.", role: "Indie hacker", signal: "Vient de poster sur le burn-out de solopreneur…", source: "r/Entrepreneur", score: 68, blurred: true },
        { name: "Léa M.", role: "Auteure & coach", signal: "« J'ai 200 onglets ouverts, 0 décision »", source: "r/getmotivated", score: 64, blurred: true },
      ]);
      setStep(2);
    }, 3500);
  };

  return (
    <div className="space-y-6" data-testid="free-scan-view">
      <div className="flex items-center gap-2 text-[12.5px]">
        {["1. Ta cible", "2. Scan en cours", "3. Premier prospect"].map((label, i) => (
          <div key={i} className={`flex items-center gap-2 ${i <= step ? "text-navy" : "text-ink-soft"}`}>
            <span className={`w-7 h-7 grid place-items-center rounded-full text-[11.5px] font-semibold ${i < step ? "bg-emerald-600 text-cream" : i === step ? "bg-navy text-cream" : "bg-sand-200 text-ink-soft"}`}>
              {i < step ? <CheckCircle2 size={14} /> : i + 1}
            </span>
            <span>{label}</span>
            {i < 2 && <ArrowRight size={12} className="mx-1 text-ink-muted" />}
          </div>
        ))}
      </div>

      {step === 0 && (
        <div className="card-cream p-7 rise" data-testid="scan-step-1">
          <p className="uppercase-eyebrow">Étape 1 / 3</p>
          <h2 className="font-display text-[26px] text-navy mt-1 mb-1">Décris ta cible idéale.</h2>
          <p className="text-[13.5px] text-ink-soft mb-5">L&apos;IA scanne les conversations publiques pour trouver des gens qui matchent.</p>
          <div className="grid sm:grid-cols-2 gap-4">
            <ScanField label="Persona (1 phrase)" testid="scan-persona" value={target.persona} onChange={(v) => setTarget({ ...target, persona: v })} placeholder="Fondateur solo SaaS en burn-out…" />
            <ScanField label="Canal de scan" testid="scan-channel" value={target.channel} onChange={(v) => setTarget({ ...target, channel: v })} select options={[["reddit","Reddit"],["linkedin","LinkedIn (Pro)"],["twitter","Twitter / X (Pro)"]]} />
          </div>
          <div className="mt-4">
            <ScanField label="Mots-clés (séparés par virgules)" testid="scan-keywords" value={target.keywords} onChange={(v) => setTarget({ ...target, keywords: v })} placeholder="burn-out solo, 200 onglets, pas de structure" />
          </div>
          <button onClick={launch} data-testid="scan-launch" className="mt-6 inline-flex items-center gap-2 px-6 h-12 rounded-full bg-navy text-cream font-semibold hover:bg-navy-bright">
            <Zap size={15} /> Lancer le scan gratuit
          </button>
          <p className="text-[11.5px] text-ink-muted mt-3">Gratuit : 1 scan / mois · 1 lead non flouté. Pro : illimité.</p>
        </div>
      )}
      {step === 1 && (
        <div className="card-cream p-10 text-center rise" data-testid="scan-step-2">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-navy text-cream mb-4 animate-pulse">
            <Search size={26} />
          </div>
          <h2 className="font-display text-2xl text-navy mb-1">Scan en cours sur {target.channel === "reddit" ? "Reddit" : target.channel}…</h2>
          <p className="text-[13px] text-ink-soft mb-5">L&apos;IA lit les posts récents, croise avec ta cible et tes mots-clés.</p>
          <div className="max-w-md mx-auto space-y-2 text-left">
            {["📡 Connexion à l'API…","🔍 Lecture des derniers posts…","🧠 Croisement avec ta cible…","✨ Extraction des signaux faibles…"].map((s, i) => (
              <div key={i} className="px-4 py-2 rounded-xl bg-cream-soft border border-sand-200 text-[13px] text-ink fade-up" style={{ animationDelay: `${i * 600}ms` }}>{s}</div>
            ))}
          </div>
        </div>
      )}
      {step === 2 && (
        <div className="rise" data-testid="scan-step-3">
          <div className="card-cream p-6 mb-4">
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div>
                <p className="uppercase-eyebrow text-emerald-700">Scan terminé · {leads.length} prospects détectés</p>
                <h2 className="font-display text-xl text-navy mt-1">Ton premier lead chaud est prêt.</h2>
              </div>
              <button onClick={() => setStep(0)} className="inline-flex items-center gap-1.5 px-3 h-9 rounded-full bg-white border border-sand-300 text-ink text-[12.5px] hover:bg-cream-soft">
                <RefreshCw size={12} /> Nouveau scan
              </button>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {leads.map((l, i) => (
              <div key={i} className={`relative rounded-2xl border bg-white p-5 ${l.blurred ? "border-sand-200" : "border-emerald-300 shadow-soft"}`} data-testid={`scan-lead-${i}`}>
                <div className={l.blurred ? "blur-sm select-none pointer-events-none" : ""}>
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold text-navy text-[14.5px]">{l.name}</h3>
                    <span className="text-[11px] text-gold-deep font-semibold tabular-nums">Score {l.score}</span>
                  </div>
                  <p className="text-[12px] text-ink-soft mb-2">{l.role}</p>
                  <p className="text-[12.5px] text-ink italic mb-2 line-clamp-2">{l.signal}</p>
                  <p className="text-[11px] text-ink-muted">{l.source}</p>
                </div>
                {l.blurred && (
                  <div className="absolute inset-0 grid place-items-center bg-cream-soft/70 rounded-2xl">
                    <button onClick={onUpgrade} data-testid={`scan-unlock-${i}`} className="inline-flex items-center gap-1.5 px-4 h-10 rounded-full bg-navy text-cream text-[12.5px] font-medium hover:bg-navy-bright">
                      <Lock size={13} /> Débloquer (Pro)
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function AgentView() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isPremium = user?.plan === "premium" || user?.plan === "premium_yearly";
  const [cfg, setCfg] = useState(null);
  const [activity, setActivity] = useState([]);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const fallbackTimer = setTimeout(() => {
      if (cancelled) return;
      setCfg((prev) => prev || { enabled: true, channels: {}, tone: "Direct & bienveillant", frequency: "daily" });
      setLoading(false);
    }, 8000);
    (async () => {
      try {
        const [c, a, s] = await Promise.all([growthApi.config(), growthApi.activity(), integrationsApi.statusAll()]);
        if (cancelled) return;
        setCfg(c || { enabled: true, channels: {}, tone: "Direct & bienveillant", frequency: "daily" });
        setActivity(a?.items || []);
        setProviders((s?.providers || []).filter((p) => p.category === "growth"));
      } catch {
        if (!cancelled) setCfg({ enabled: true, channels: {}, tone: "Direct & bienveillant", frequency: "daily" });
      }
      if (!cancelled) setLoading(false);
    })();
    return () => { cancelled = true; clearTimeout(fallbackTimer); };
  }, []);

  const save = async (next) => {
    setSaving(true);
    try {
      const saved = await growthApi.saveConfig(next);
      setCfg(saved);
      toast.success("Configuration enregistrée");
    } catch (e) { toast.error(e.message); }
    finally { setSaving(false); }
  };

  if (loading || !cfg) return <div className="card-cream p-10 text-center rise"><Loader2 className="animate-spin inline" /> Chargement…</div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
      <div className="lg:col-span-2 card-cream p-7 rise">
        {/* Plan banner */}
        <div data-testid="agent-plan-banner" className={`mb-5 p-4 rounded-2xl border ${isPremium ? "bg-gold/10 border-gold/30" : "bg-cream-soft border-sand-300"}`}>
          {isPremium ? (
            <div className="flex items-start gap-3">
              <Sparkles size={16} className="text-gold-deep shrink-0 mt-0.5" />
              <div>
                <p className="font-display text-[16px] text-navy">Mode <span className="font-serif-italic text-gold-deep">Premium</span> · Agent IA WhatsApp 24/7</p>
                <p className="text-[12.5px] text-ink-soft mt-1 leading-relaxed">
                  L&apos;agent répond automatiquement à vos prospects via votre numéro WhatsApp Business.
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-start gap-3 flex-wrap">
              <Bot size={16} className="text-ink-soft shrink-0 mt-0.5" />
              <div className="flex-1 min-w-[260px]">
                <p className="font-display text-[16px] text-navy">Mode <strong>Free</strong> · Préparation manuelle</p>
                <p className="text-[12.5px] text-ink-soft mt-1 leading-relaxed">
                  L&apos;agent détecte les prospects et prépare les messages — vous validez et envoyez chaque réponse vous-même.
                  <strong className="text-navy"> Premium</strong> active la réponse 100 % automatique.
                </p>
              </div>
              <a data-testid="agent-upgrade-link" href="/settings"
                className="inline-flex items-center gap-1.5 px-3.5 h-9 rounded-full bg-navy text-cream text-[12px] font-semibold hover:bg-navy-bright transition-colors shrink-0">
                <Sparkles size={12} /> Passer Premium
              </a>
            </div>
          )}
        </div>

        {!isPremium && (
          <details className="mb-5 rounded-2xl bg-cream-soft border border-sand-300" data-testid="agent-free-scan-block">
            <summary className="cursor-pointer p-4 list-none flex items-center justify-between gap-3 hover:bg-cream-softer transition-colors rounded-2xl">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gold/15 grid place-items-center"><Zap size={15} className="text-gold-deep" /></div>
                <div>
                  <p className="font-display text-[15px] text-navy">Tester gratuitement — Free Scan</p>
                  <p className="text-[11.5px] text-ink-soft">Voir ce que l&apos;agent peut trouver · 0€ · sans engagement</p>
                </div>
              </div>
            </summary>
            <div className="p-5 pt-2 border-t border-sand-300">
              <FreeScanView onUpgrade={() => { window.location.href = "/settings"; }} />
            </div>
          </details>
        )}

        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <p className="uppercase-eyebrow">Votre agent</p>
            <h2 className="font-display text-[28px] text-navy mt-1 leading-tight flex items-center gap-3">
              Growth Agent
              <span className={`inline-flex items-center gap-1.5 text-[12px] font-semibold px-2.5 py-1 rounded-full ${cfg.enabled ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-sand-200 text-ink-soft border border-sand-300"}`}
                data-testid="agent-status-badge">
                <span className={`w-1.5 h-1.5 rounded-full ${cfg.enabled ? "bg-emerald-500" : "bg-ink-muted"}`} />
                {cfg.enabled ? "actif" : "en pause"}
              </span>
            </h2>
          </div>
          <button data-testid="agent-toggle" onClick={() => save({ ...cfg, enabled: !cfg.enabled })} disabled={saving}
            className={`inline-flex items-center gap-2 px-5 h-11 rounded-full font-semibold transition-colors disabled:opacity-50 ${cfg.enabled ? "bg-cream-soft text-navy border border-sand-300 hover:bg-sand-200" : "bg-navy text-cream hover:bg-navy-bright"}`}>
            <Power size={15} /> {cfg.enabled ? "Mettre en pause" : "Activer l'agent"}
          </button>
        </div>

        <div className="mt-6 grid grid-cols-3 gap-4">
          {[
            { l: "Prospects détectés", v: activity.length },
            { l: "Canaux actifs", v: Object.values(cfg.channels || {}).filter(Boolean).length },
            { l: "Fréquence", v: FREQUENCIES.find((f) => f.id === cfg.frequency)?.label.split(" ")[0] || "—" },
          ].map((s) => (
            <div key={s.l} className="p-4 rounded-2xl bg-cream-soft border border-sand-200">
              <p className="font-display text-[22px] text-navy">{s.v}</p>
              <p className="text-[11.5px] text-ink-soft mt-0.5">{s.l}</p>
            </div>
          ))}
        </div>

        <ConversationsMetrics />

        <div className="mt-7">
          <p className="uppercase-eyebrow">Canaux connectés</p>
          <p className="text-[12.5px] text-ink-soft mt-1 mb-3">
            Connectez-les depuis <button onClick={() => navigate("/integrations")} className="underline hover:text-navy font-semibold" data-testid="agent-go-integrations">Mes intégrations</button> — l&apos;agent les utilisera partout.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2.5" data-testid="agent-channels-grid">
            {providers.map((p) => {
              const on = !!cfg.channels?.[p.id];
              const canToggle = p.connected && p.supported;
              const handleClick = async () => {
                if (!p.connected) { navigate("/integrations"); return; }
                if (!canToggle) return;
                await save({ ...cfg, channels: { ...cfg.channels, [p.id]: !on } });
              };
              return (
                <button key={p.id} data-testid={`agent-channel-${p.id}`} onClick={handleClick} disabled={saving}
                  className={`flex items-center justify-between p-3 rounded-2xl border transition-all text-left ${p.connected && on ? "bg-emerald-50 border-emerald-200 text-emerald-800" : p.connected ? "bg-cream-soft border-sand-300 text-ink hover:border-navy/30" : "bg-cream-soft border-dashed border-sand-300 text-ink-soft hover:border-navy/30"}`}>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-semibold flex items-center gap-2">
                      {p.label}
                      {!p.supported && <span className="text-[9.5px] uppercase tracking-wider bg-sand-200 text-ink-soft px-1.5 py-0.5 rounded-full">Bientôt</span>}
                    </p>
                    <p className="text-[10.5px] text-ink-soft mt-0.5 truncate">{p.connected ? (p.email || "Connecté") : "Non connecté"}</p>
                  </div>
                  {p.connected ? (
                    <span className={`w-9 h-5 rounded-full relative transition-colors ${on ? "bg-emerald-500" : "bg-sand-300"}`}>
                      <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all ${on ? "left-[18px]" : "left-0.5"}`} />
                    </span>
                  ) : (
                    <span className="text-[11px] font-semibold text-navy">Connecter →</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="uppercase-eyebrow mb-2">Fréquence</p>
            <div className="flex gap-2 flex-wrap">
              {FREQUENCIES.map((f) => (
                <button key={f.id} data-testid={`agent-freq-${f.id}`} onClick={() => save({ ...cfg, frequency: f.id })} disabled={saving}
                  className={`px-3 h-9 rounded-full text-[12.5px] font-medium transition-colors ${cfg.frequency === f.id ? "bg-navy text-cream" : "bg-cream-soft text-ink-soft hover:bg-sand-200"}`}>
                  {f.label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="uppercase-eyebrow mb-2">Ton des messages</p>
            <input data-testid="agent-tone-input" value={cfg.tone || ""} onChange={(e) => setCfg({ ...cfg, tone: e.target.value })} onBlur={() => save({ ...cfg })}
              className="w-full h-10 px-3 rounded-xl bg-white border border-sand-300 text-[13.5px] focus:outline-none focus:border-navy/50" />
          </div>
        </div>
      </div>

      <div className="card-cream p-7 rise" style={{ animationDelay: "120ms" }}>
        <div className="flex items-center justify-between mb-3">
          <p className="uppercase-eyebrow">Activité récente</p>
          <button onClick={async () => { const a = await growthApi.activity(); setActivity(a.items || []); toast.success("Activité rafraîchie"); }}
            className="w-8 h-8 grid place-items-center rounded-full hover:bg-cream-soft text-ink-soft" data-testid="agent-refresh">
            <RefreshCw size={13} />
          </button>
        </div>
        {activity.length === 0 ? (
          <p className="text-[13px] text-ink-soft py-6 text-center">Aucune activité récente.</p>
        ) : (
          <ul className="space-y-2.5" data-testid="agent-activity-list">
            {activity.slice(0, 10).map((a, i) => (
              <li key={i} className="flex items-start gap-3 p-3 rounded-2xl bg-cream-soft border border-sand-200">
                <span className="w-7 h-7 rounded-full bg-navy text-cream grid place-items-center shrink-0"><Activity size={12} /></span>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] text-ink font-medium leading-tight">{a.title}</p>
                  <p className="text-[11.5px] text-ink-soft mt-0.5 truncate">{a.desc}</p>
                  {a.at && <p className="text-[10.5px] text-ink-muted mt-1">{new Date(a.at).toLocaleString()}</p>}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
