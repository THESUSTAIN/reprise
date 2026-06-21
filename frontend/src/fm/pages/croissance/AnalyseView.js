import React, { useState, useEffect } from "react";
import { analyseApi } from "@fm/lib/api";
import { toast } from "sonner";
import { Loader2, Sparkles, ArrowRight } from "lucide-react";
import MomTestModal from "./MomTestModal";

export default function AnalyseView() {
  const [data, setData] = useState({ score: 0, sections: [], summary: "", verdict: "" });
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [openIdx, setOpenIdx] = useState(null);
  const [verdictLoading, setVerdictLoading] = useState(false);
  const [momTest, setMomTest] = useState(null);
  const [momLoading, setMomLoading] = useState(false);
  const [showMom, setShowMom] = useState(false);

  useEffect(() => {
    analyseApi.get()
      .then((d) => setData({
        score: d?.score ?? 0,
        sections: Array.isArray(d?.sections) ? d.sections : [],
        summary: d?.summary || "",
        verdict: d?.verdict || "",
        generated_at: d?.generated_at || null,
      }))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const runIA = async () => {
    setRunning(true);
    try {
      const d = await analyseApi.run();
      setData(d);
      toast.success("Analyse IA mise à jour");
    } catch (e) {
      toast.error(e.message || "Analyse IA indisponible");
    } finally {
      setRunning(false);
    }
  };

  const runVerdict = async () => {
    setVerdictLoading(true);
    try {
      const r = await analyseApi.verdict();
      setData((d) => ({ ...d, verdict: r.verdict }));
      toast.success("Verdict généré");
    } catch (e) {
      toast.error(e.message || "Verdict indisponible");
    } finally {
      setVerdictLoading(false);
    }
  };

  const runMomTest = async () => {
    setMomLoading(true);
    try {
      const r = await analyseApi.momTest();
      setMomTest(r);
      setShowMom(true);
      toast.success("Guide Mom Test prêt");
    } catch (e) {
      toast.error(e.message || "Mom Test indisponible");
    } finally {
      setMomLoading(false);
    }
  };

  const exportReport = async () => {
    try {
      const r = await analyseApi.export();
      const blob = new Blob([r.markdown], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = r.filename; a.click();
      URL.revokeObjectURL(url);
      toast.success("Rapport téléchargé");
    } catch (e) {
      toast.error(e.message || "Export indisponible");
    }
  };

  if (loading) return <div className="card-cream p-10 text-center rise"><Loader2 className="animate-spin inline" /> Chargement…</div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
      <div className="lg:col-span-2 card-cream p-7 rise">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <p className="uppercase-eyebrow">Validation marché</p>
            <h2 className="font-display text-[26px] text-navy mt-1">
              Score IA : <span className="text-gold-deep tabular-nums">{data.score}/100</span>
            </h2>
            <p className="text-[13px] text-ink-soft mt-2 max-w-lg leading-relaxed">{data.summary}</p>
          </div>
          <button data-testid="analyse-run-ia" onClick={runIA} disabled={running}
            className="inline-flex items-center gap-2 px-5 h-11 rounded-full bg-navy text-cream font-semibold hover:bg-navy-bright transition-colors disabled:opacity-50">
            {running ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
            {running ? "Analyse en cours…" : data.generated_at ? "Relancer l'analyse IA" : "Lancer l'analyse IA"}
          </button>
        </div>

        {data.generated_at && (
          <div className="mt-5 p-4 rounded-2xl bg-navy text-cream/95" data-testid="analyse-verdict">
            <div className="flex items-center justify-between gap-3 mb-2">
              <p className="text-[11px] tracking-[0.22em] uppercase text-gold/90 font-semibold">Verdict du copilote</p>
              <button onClick={runVerdict} disabled={verdictLoading} data-testid="analyse-verdict-run"
                className="text-[12px] inline-flex items-center gap-1.5 px-3 h-8 rounded-full bg-white/10 hover:bg-white/15 transition disabled:opacity-50">
                {verdictLoading && <Loader2 size={12} className="animate-spin" />}
                {data.verdict ? "Régénérer" : "Générer le verdict"}
              </button>
            </div>
            {data.verdict
              ? <p className="text-[13.5px] leading-relaxed whitespace-pre-line">{data.verdict}</p>
              : <p className="text-[12.5px] text-cream/70 italic">Demande un verdict pour avoir une lecture langage naturel de ton score.</p>
            }
          </div>
        )}

        {data.generated_at && (
          <div className="mt-4 flex items-center gap-2 flex-wrap" data-testid="analyse-actions">
            <button onClick={runMomTest} disabled={momLoading} data-testid="analyse-mom-test"
              className="inline-flex items-center gap-2 px-4 h-10 rounded-full bg-cream-soft border border-sand-300 text-navy text-[13px] font-medium hover:bg-sand-100 disabled:opacity-50">
              {momLoading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
              Générer guide Mom Test
            </button>
            <button onClick={exportReport} data-testid="analyse-export"
              className="inline-flex items-center gap-2 px-4 h-10 rounded-full bg-cream-soft border border-sand-300 text-navy text-[13px] font-medium hover:bg-sand-100">
              <ArrowRight size={13} /> Exporter le rapport (.md)
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 mt-6" data-testid="analyse-sections">
          {(data.sections || []).map((s, i) => {
            const isOpen = openIdx === i;
            return (
              <button key={s.name} data-testid={`analyse-section-${i}`} onClick={() => setOpenIdx(isOpen ? null : i)}
                className={`text-left p-3.5 rounded-2xl bg-cream-soft border transition-all ${isOpen ? "border-navy/40 shadow-soft" : "border-sand-200 hover:border-navy/30"}`}>
                <div className="flex items-center justify-between">
                  <p className="text-[13.5px] text-ink font-medium">{s.name}</p>
                  <span className="text-[12px] font-semibold text-navy tabular-nums">{s.score}/100</span>
                </div>
                <div className="h-1 mt-2 rounded-full bg-sand-200 overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-navy to-navy-bright rounded-full" style={{ width: `${s.score}%` }} />
                </div>
                {isOpen && s.tip && <p className="text-[12.5px] text-ink-soft mt-3 leading-relaxed">{s.tip}</p>}
                {isOpen && !s.tip && <p className="text-[12px] text-ink-muted italic mt-3">Lancez l&apos;analyse IA pour obtenir une recommandation.</p>}
              </button>
            );
          })}
        </div>
      </div>

      <div className="card-cream p-7 rise" style={{ animationDelay: "120ms" }}>
        <p className="uppercase-eyebrow">Concurrents suivis</p>
        <ul className="mt-4 space-y-3 text-[13.5px]">
          {["Notion", "ClickUp", "Sunsama", "Reclaim AI", "Motion"].map((c) => (
            <li key={c} className="flex items-center justify-between p-3 rounded-2xl bg-cream-soft border border-sand-200">
              <span className="text-ink font-medium">{c}</span>
              <ArrowRight size={14} className="text-ink-soft" />
            </li>
          ))}
        </ul>
        {data.generated_at && (
          <p className="text-[11px] text-ink-muted mt-5 italic">
            Dernière analyse IA : {new Date(data.generated_at).toLocaleString()}
          </p>
        )}
      </div>

      {showMom && momTest && <MomTestModal data={momTest} onClose={() => setShowMom(false)} />}
    </div>
  );
}
