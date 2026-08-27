import React, { useEffect, useState, useCallback } from "react";
import {
  Sparkles, TrendingUp, Target, Zap, ArrowRight, ExternalLink,
  Loader2, ShieldCheck, Compass, RefreshCw, Landmark,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { visionBrainApi } from "../../lib/finalVisionModuleApi";
import useVisionEvents from "@/hooks/useVisionEvents";

const SOURCE_ICON = { urssaf: Landmark, gouv: ShieldCheck, insee: Landmark };

function ScoreDonut({ value = 0 }) {
  const r = 34, c = 2 * Math.PI * r, off = c - (value / 100) * c;
  return (
    <div className="relative h-24 w-24 shrink-0">
      <svg viewBox="0 0 80 80" className="h-24 w-24 -rotate-90">
        <circle cx="40" cy="40" r={r} fill="none" strokeWidth="8" stroke="rgba(255,255,255,0.10)" />
        <circle cx="40" cy="40" r={r} fill="none" strokeWidth="8" stroke="url(#brainGrad)"
          strokeLinecap="round" strokeDasharray={c} strokeDashoffset={off}
          style={{ transition: "stroke-dashoffset 1.1s cubic-bezier(0.22,1,0.36,1)" }} />
        <defs>
          <linearGradient id="brainGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#DEC2A3" />
            <stop offset="100%" stopColor="#DEC2A3" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center rotate-0">
        <span className="text-2xl font-bold leading-none text-white">{value}</span>
        <span className="text-[10px] text-white/50">/ 100</span>
      </div>
    </div>
  );
}

/**
 * Panneau IA persistant (toujours visible à droite du Vision Board).
 * Score d'alignement, analyse live, opportunités (sources conditionnelles),
 * actions recommandées, modules suggérés (sur signal réel).
 */
export default function VisionBrainPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const navigate = useNavigate();

  const load = useCallback(() => {
    visionBrainApi.panel()
      .then((d) => setData(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Backlog #2 — flux SSE temps réel : remplace l'ancien `setInterval(load, 60000)`.
  // - "tick" (~60s, même cadence qu'avant) : recalcule le panneau, pour les
  //   données pas encore branchées sur le bus d'événements (finance, leads…).
  // - "card_update" : une VisionCard a changé ailleurs → le score/les cartes
  //   liées peuvent en dépendre, donc on recharge aussi, sans attendre le tick.
  // Filet de sécurité : si SSE ne peut pas s'établir (proxy, ad-blocker…),
  // on retombe sur un polling lent (90s) plutôt que de rester figé.
  useVisionEvents({
    onTick: load,
    onCardUpdate: load,
    onFallbackPoll: load,
  });

  const runAnalysis = async () => {
    setAnalyzing(true);
    try {
      const res = await visionBrainApi.analyze(true);
      setAnalysis(res);
    } catch (e) { /* noop */ } finally { setAnalyzing(false); }
  };

  const goModule = (m) => {
    const map = { croissance: "/croissance", pilotage: "/pilotage", acquisition: "/croissance" };
    if (m && map[m]) navigate(map[m]);
  };

  if (loading) {
    return (
      <aside className="vbrain-panel" data-testid="vision-ai-panel">
        <div className="flex items-center gap-2 text-white/60"><Loader2 className="animate-spin" size={16} /> Analyse en cours…</div>
      </aside>
    );
  }
  if (!data) return null;

  return (
    <aside className="vbrain-panel" data-testid="vision-ai-panel">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-white/90">
          <Sparkles size={16} className="text-[#DEC2A3]" />
          <span className="text-sm font-semibold">Cerveau IA</span>
        </div>
        <button onClick={load} title="Rafraîchir" data-testid="vision-ai-refresh"
          className="rounded-full p-1.5 text-white/50 hover:bg-white/10 hover:text-white transition-colors">
          <RefreshCw size={13} />
        </button>
      </div>

      {/* Score d'alignement */}
      <div className="mt-3 flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-3" data-testid="vision-ai-score">
        <ScoreDonut value={data.alignment_score} />
        <div className="min-w-0">
          <div className="text-xs uppercase tracking-wide text-white/40">Alignement</div>
          <div className="text-sm font-medium text-white">{data.live_analysis?.label}</div>
          {data.delta_week === null || data.delta_week === undefined ? (
            <div className="mt-1 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold bg-white/10 text-white/50">
              Premier calcul
            </div>
          ) : (
            <div className={`mt-1 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${data.delta_week >= 0 ? "bg-emerald-500/15 text-emerald-300" : "bg-red-500/15 text-red-300"}`}>
              <TrendingUp size={12} /> {data.delta_week >= 0 ? "+" : ""}{data.delta_week} cette semaine
            </div>
          )}
        </div>
      </div>

      {/* Opportunités détectées */}
      <Section title="Opportunités détectées" testid="vision-ai-opportunities">
        {data.opportunities?.map((o, i) => (
          <div key={i} className="rounded-xl border border-white/10 bg-white/[0.03] p-2.5" data-testid={`vision-ai-opp-${i}`}>
            <div className="flex items-start gap-2">
              <span className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${o.kind === "news" ? "bg-amber-400" : "bg-[#DEC2A3]"} animate-pulse`} />
              <div className="min-w-0">
                <div className="text-sm font-medium text-white leading-snug">{o.title}</div>
                {o.sub && <div className="text-xs text-white/50">{o.sub}</div>}
                <button
                  type="button"
                  data-testid={`vision-ai-opp-${i}-talk`}
                  onClick={() => window.dispatchEvent(new CustomEvent("zayado:open-cockpit-chat", { detail: { ask: `Aide-moi à agir sur cette opportunité : ${o.title}` } }))}
                  className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-[#DEC2A3]/40 bg-[#DEC2A3]/10 px-2.5 py-1 text-[11px] font-semibold text-[#f0dca5] transition-colors hover:bg-[#DEC2A3]/20"
                >
                  <Sparkles size={11} /> En parler au Copilote
                </button>
                {/* Sources : uniquement pour les actualités liées à l'état de l'user */}
                {o.sources?.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1.5" data-testid={`vision-ai-opp-${i}-sources`}>
                    {o.sources.map((s, j) => {
                      const Icon = SOURCE_ICON[s.icon] || ExternalLink;
                      return (
                        <a key={j} href={s.url} target="_blank" rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 rounded-md border border-amber-400/30 bg-amber-400/10 px-1.5 py-0.5 text-[11px] text-amber-200 no-underline hover:bg-amber-400/20 transition-colors">
                          <Icon size={11} /> {s.label}
                        </a>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </Section>

      {/* Actions recommandées */}
      <Section title="Actions recommandées" testid="vision-ai-actions">
        {data.actions?.map((a, i) => (
          <button key={i} onClick={() => goModule(a.module)} data-testid={`vision-ai-action-${i}`}
            className="flex w-full items-center justify-between rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-left text-sm text-white/90 hover:border-[#DEC2A3]/50 hover:bg-white/[0.06] transition-colors">
            <span className="flex items-center gap-2"><Target size={13} className="text-[#DEC2A3]" /> {a.label}</span>
            <ArrowRight size={14} className="text-white/40" />
          </button>
        ))}
      </Section>

      {/* Modules suggérés — sur signal réel uniquement */}
      {data.suggested_modules?.length > 0 && (
        <Section title="Modules suggérés" testid="vision-ai-modules">
          <div className="flex flex-wrap gap-2">
            {data.suggested_modules.map((m, i) => (
              <button key={i} onClick={() => goModule(m.id)} data-testid={`vision-ai-module-${i}`}
                title={m.reason}
                className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.05] px-3 py-1.5 text-xs text-white/85 hover:border-[#DEC2A3]/50 transition-colors">
                <Compass size={12} className="text-[#DEC2A3]" /> {m.label}
              </button>
            ))}
          </div>
        </Section>
      )}

      {/* Analyse IA (SWOT + incohérences) */}
      <Section title="Analyse en direct" testid="vision-ai-analysis">
        <button onClick={runAnalysis} disabled={analyzing} data-testid="vision-ai-analyze-btn"
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#E7C67C] to-[#B0851F] px-3 py-2 text-sm font-semibold text-white hover:opacity-95 disabled:opacity-60 transition-opacity">
          {analyzing ? <Loader2 className="animate-spin" size={14} /> : <Zap size={14} />}
          {analyzing ? "Analyse…" : "Lancer l'analyse IA"}
        </button>
        {analysis && (
          <div className="mt-2 space-y-2" data-testid="vision-ai-analysis-result">
            {analysis.incoherences?.length > 0 && (
              <div className="rounded-xl border border-amber-400/30 bg-amber-400/10 p-2.5">
                <div className="text-xs font-semibold text-amber-200 mb-1">Incohérences détectées</div>
                {analysis.incoherences.slice(0, 3).map((x, i) => (
                  <div key={i} className="text-xs text-amber-100/90 leading-snug">• {x}</div>
                ))}
              </div>
            )}
            {analysis.recommandations?.length > 0 && (
              <div className="rounded-xl border border-white/10 bg-white/[0.03] p-2.5">
                <div className="text-xs font-semibold text-white/80 mb-1">Recommandations</div>
                {analysis.recommandations.slice(0, 3).map((x, i) => (
                  <div key={i} className="text-xs text-white/70 leading-snug">→ {x}</div>
                ))}
              </div>
            )}
          </div>
        )}
      </Section>
    </aside>
  );
}

function Section({ title, testid, children }) {
  return (
    <div className="mt-4" data-testid={testid}>
      <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-white/40">{title}</div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}
