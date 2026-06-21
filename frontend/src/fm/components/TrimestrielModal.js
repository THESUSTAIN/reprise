import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  X,
  Download,
  Sparkles,
  Quote,
  ArrowRight,
  Crown,
  Lock,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from "lucide-react";

const FALLBACK_BILAN = {
  id: "q4-2025",
  label: "Bilan Q4 2025",
  highlight: "Trimestre en cours",
  period: "Oct — Déc 2025",
  locked: false,
  numbers: [
    { label: "Décisions clés", value: "—" },
    { label: "Énergie moyenne", value: "—" },
    { label: "Stress moyen", value: "—" },
    { label: "Jours suivis", value: "—" },
  ],
  energy: [],
  decisions: [],
  paragraph: "Ton co-pilote prépare ton bilan dès que tu auras suffisamment de données.",
  nextStep: "Continue tes check-ins quotidiens — le prochain bilan arrive bientôt.",
};

const normalizeBilan = (b) => {
  if (!b) return FALLBACK_BILAN;
  return {
    ...FALLBACK_BILAN,
    ...b,
    label: b.label || b.title || FALLBACK_BILAN.label,
    highlight: b.highlight || b.verdict || FALLBACK_BILAN.highlight,
    period: b.period || FALLBACK_BILAN.period,
    locked: b.locked ?? (b.status === "archived"),
    numbers: b.numbers && b.numbers.length ? b.numbers : [
      { label: "Décisions clés", value: String(b.decisionsCount ?? "—") },
      { label: "Énergie moyenne", value: b.energieMoyenne != null ? `${b.energieMoyenne}/10` : "—" },
      { label: "Stress moyen", value: b.stressMoyen != null ? `${b.stressMoyen}/10` : "—" },
      { label: "Jours suivis", value: String(b.daysTracked ?? "—") },
    ],
    energy: b.energy || [],
    decisions: b.decisions || [],
    paragraph: b.paragraph || b.verdict || FALLBACK_BILAN.paragraph,
    nextStep: b.nextStep || FALLBACK_BILAN.nextStep,
  };
};
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

const TrimestrielModal = ({ onClose, initialQuarterId = "q4-2025", bilanHistory = [], user = { name: "" } }) => {
  const [quarterId, setQuarterId] = useState(initialQuarterId);
  const [exporting, setExporting] = useState(false);
  const sheetRef = useRef(null);

  const history = bilanHistory.length ? bilanHistory : [FALLBACK_BILAN];
  const idx = history.findIndex((b) => b.id === quarterId);
  const safeIdx = idx === -1 ? 0 : idx;
  const bilan = normalizeBilan(history[safeIdx]);
  const prev = history[safeIdx + 1] ? normalizeBilan(history[safeIdx + 1]) : null; // older
  const next = history[safeIdx - 1] ? normalizeBilan(history[safeIdx - 1]) : null; // newer

  useEffect(() => {
    const onEsc = (e) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onEsc);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onEsc);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const handleDownloadPDF = async () => {
    if (!sheetRef.current || exporting) return;
    setExporting(true);
    try {
      const pages = sheetRef.current.querySelectorAll(".pdf-page");
      const pdf = new jsPDF({ unit: "mm", format: "a4", orientation: "portrait" });
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();

      for (let i = 0; i < pages.length; i++) {
        const canvas = await html2canvas(pages[i], {
          scale: 2,
          useCORS: true,
          backgroundColor: "#FDFBF7",
          logging: false,
        });
        const imgData = canvas.toDataURL("image/jpeg", 0.92);
        const imgRatio = canvas.height / canvas.width;
        const imgHeight = pageWidth * imgRatio;

        if (i > 0) pdf.addPage();
        if (imgHeight <= pageHeight) {
          pdf.addImage(imgData, "JPEG", 0, 0, pageWidth, imgHeight);
        } else {
          // scale down to fit
          const fittedHeight = pageHeight;
          const fittedWidth = (canvas.width * fittedHeight) / canvas.height;
          const xOffset = (pageWidth - fittedWidth) / 2;
          pdf.addImage(imgData, "JPEG", xOffset, 0, fittedWidth, fittedHeight);
        }
      }
      pdf.save(`Zayado-Bilan-${bilan.label.replace(/\s+/g, "-")}.pdf`);
    } catch (e) {
      console.error(e);
      alert("Erreur lors de la génération du PDF. Réessaye dans un instant.");
    } finally {
      setExporting(false);
    }
  };

  return createPortal(
    <div
      className="fixed inset-0 z-[100] bg-[rgba(20,38,74,0.65)] backdrop-blur-sm overflow-y-auto fade-up"
      onClick={onClose}
      data-testid="trim-modal"
    >
      <div className="min-h-full grid place-items-center p-4 md:p-10">
        <div className="w-full max-w-[920px]" onClick={(e) => e.stopPropagation()}>
          {/* Toolbar */}
          <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
            <div className="flex items-center gap-2 text-[var(--bg)]" data-testid="trim-quarter-nav">
              <button
                onClick={() => prev && setQuarterId(prev.id)}
                disabled={!prev}
                className="w-9 h-9 rounded-full grid place-items-center bg-white/10 border border-white/20 hover:bg-white/20 disabled:opacity-30 disabled:cursor-not-allowed transition"
                data-testid="trim-prev"
                aria-label="Trimestre précédent"
              >
                <ChevronLeft size={16} />
              </button>
              <div className="px-4">
                <div className="text-[10px] tracking-[0.22em] uppercase opacity-70">
                  Trimestre
                </div>
                <div className="font-semibold text-[14px] flex items-center gap-2">
                  {bilan.locked && <Lock size={11} className="opacity-70" />}
                  {bilan.label}
                </div>
              </div>
              <button
                onClick={() => next && setQuarterId(next.id)}
                disabled={!next}
                className="w-9 h-9 rounded-full grid place-items-center bg-white/10 border border-white/20 hover:bg-white/20 disabled:opacity-30 disabled:cursor-not-allowed transition"
                data-testid="trim-next"
                aria-label="Trimestre suivant"
              >
                <ChevronRight size={16} />
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleDownloadPDF}
                disabled={exporting}
                className="btn-cta !py-2 !px-4 text-[13px] disabled:opacity-70"
                data-testid="trim-download"
              >
                {exporting ? (
                  <><Loader2 size={14} className="animate-spin" /> Génération…</>
                ) : (
                  <><Download size={14} /> Télécharger en PDF</>
                )}
              </button>
              <button
                onClick={onClose}
                className="w-9 h-9 rounded-full grid place-items-center bg-white/10 border border-white/20 text-[var(--bg)] hover:bg-white/20"
                data-testid="trim-close"
                aria-label="Fermer"
              >
                <X size={14} />
              </button>
            </div>
          </div>

          {/* PDF sheets */}
          <div ref={sheetRef} className="space-y-6">
            {/* PAGE 1 */}
            <article
              className="bg-[var(--bg)] rounded-2xl overflow-hidden shadow-2xl pdf-page"
              data-testid="trim-page-1"
            >
              <div
                className="relative grain-overlay px-10 md:px-14 py-12 md:py-16"
                style={{ background: "var(--navy-deep)", color: "var(--bg)" }}
              >
                <div className="relative flex items-center justify-between mb-12 flex-wrap gap-3">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-full grid place-items-center"
                      style={{ background: "var(--gold)", color: "var(--navy-deep)" }}
                    >
                      <span className="font-bold text-[18px] leading-none">Z</span>
                    </div>
                    <div className="leading-tight">
                      <div className="font-bold text-[16px]">Zayado</div>
                      <div className="text-[10px] tracking-[0.22em] uppercase opacity-75">
                        MyExtension AI
                      </div>
                    </div>
                  </div>
                  <span
                    className="chip"
                    style={{
                      background: "rgba(255,255,255,0.08)",
                      borderColor: "rgba(255,255,255,0.2)",
                      color: "var(--bg)",
                    }}
                  >
                    Privé · {user.name}
                  </span>
                </div>

                <div className="relative">
                  <div className="text-[11px] tracking-[0.22em] uppercase opacity-75 mb-4">
                    Bilan trimestriel — préparé par votre co-pilote
                  </div>
                  <h1
                    className="text-[34px] md:text-[44px] leading-[1.08] mb-6 font-bold"
                    style={{ color: "var(--bg)", letterSpacing: "-0.03em" }}
                  >
                    « {bilan.highlight} »
                  </h1>
                  <div className="text-[13px] opacity-80 max-w-[640px] leading-relaxed">
                    {bilan.period}
                  </div>
                </div>

                <div className="relative mt-12 grid grid-cols-2 md:grid-cols-4 gap-3">
                  {bilan.numbers.map((n) => (
                    <div
                      key={n.label}
                      className="rounded-xl p-4"
                      style={{
                        background: "rgba(255,255,255,0.06)",
                        border: "1px solid rgba(201,166,107,0.25)",
                      }}
                    >
                      <div className="text-[10px] tracking-[0.22em] uppercase opacity-70 mb-2">
                        {n.label}
                      </div>
                      <div
                        className="text-[22px] md:text-[26px] leading-none font-bold"
                        style={{ color: "var(--gold)", letterSpacing: "-0.02em" }}
                      >
                        {n.value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Energy curve */}
              <div className="px-10 md:px-14 py-10">
                <div className="text-[11px] tracking-[0.22em] uppercase text-[#6B7280] mb-2">
                  Courbe d&apos;énergie · 90 derniers jours
                </div>
                <h2 className="text-[22px] md:text-[26px] leading-none mb-5 font-bold">
                  Ta trajectoire interne.
                </h2>
                <div className="h-[180px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={bilan.energy}
                      margin={{ top: 8, right: 8, left: -14, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient id="quarterGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#1F3A6A" stopOpacity={0.4} />
                          <stop offset="100%" stopColor="#1F3A6A" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E8E2D9" vertical={false} />
                      <XAxis
                        dataKey="label"
                        tick={{ fill: "#5C6B7B", fontSize: 9 }}
                        axisLine={false}
                        tickLine={false}
                        interval={14}
                      />
                      <YAxis
                        domain={[0, 10]}
                        tick={{ fill: "#5C6B7B", fontSize: 10 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Area
                        type="monotone"
                        dataKey="energie"
                        stroke="#1F3A6A"
                        strokeWidth={2}
                        fill="url(#quarterGrad)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-4 text-[12px] text-[#6B7280] italic leading-relaxed">
                  {bilan.locked
                    ? "Données partielles — reconstituées avant ton arrivée chez Zayado."
                    : "Ce que tu n'as pas vu en vivant ces 90 jours : ta courbe trace une histoire."}
                </div>
              </div>
            </article>

            {/* PAGE 2 */}
            <article
              className="bg-[var(--bg)] rounded-2xl overflow-hidden shadow-2xl pdf-page"
              data-testid="trim-page-2"
            >
              <div className="px-10 md:px-14 py-12 md:py-14">
                <div className="text-[11px] tracking-[0.22em] uppercase text-[#6B7280] mb-2">
                  {bilan.decisions.length} décision{bilan.decisions.length > 1 ? "s" : ""} clé{bilan.decisions.length > 1 ? "s" : ""} validée{bilan.decisions.length > 1 ? "s" : ""} · le 30 % qui t&apos;appartient
                </div>
                <h2 className="text-[26px] md:text-[32px] leading-[1.1] mb-8 font-bold">
                  Ce que toi seule pouvais trancher.
                </h2>

                <div className="space-y-5 mb-12">
                  {bilan.decisions.map((d, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-5 pb-5 border-b border-[var(--border)] last:border-b-0"
                      data-testid={`trim-decision-${i}`}
                    >
                      <div
                        className="w-11 h-11 rounded-full grid place-items-center shrink-0 font-bold text-[18px]"
                        style={{
                          background: "var(--gold-soft)",
                          color: "#1F3B73",
                        }}
                      >
                        {i + 1}
                      </div>
                      <div className="flex-1">
                        <div className="text-[10px] tracking-[0.22em] uppercase text-[#6B7280] mb-1">
                          {d.date}
                        </div>
                        <h3 className="text-[18px] md:text-[20px] leading-tight mb-2 font-bold">
                          {d.title}
                        </h3>
                        <div className="text-[13px] leading-relaxed mb-1">
                          <span className="font-semibold">Impact —</span> {d.impact}
                        </div>
                        <div className="text-[12px] text-[#6B7280] italic">
                          {d.framing}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Verdict block */}
                <div
                  className="relative rounded-2xl p-8 md:p-10 mb-10"
                  style={{
                    background: "var(--gold-soft)",
                    border: "1px solid var(--gold)",
                  }}
                  data-testid="trim-verdict"
                >
                  <Quote
                    size={28}
                    className="absolute top-6 right-6 opacity-30"
                    style={{ color: "#1F3B73" }}
                  />
                  <div className="text-[11px] tracking-[0.22em] uppercase text-[#1F3B73] opacity-70 mb-3">
                    Verdict du co-pilote
                  </div>
                  <p className="text-[16px] md:text-[18px] leading-[1.55] text-[#1F3B73] mb-5 font-medium">
                    {bilan.paragraph}
                  </p>
                  <div className="pt-4 border-t border-[var(--gold)] border-opacity-40">
                    <div className="text-[11px] tracking-[0.22em] uppercase text-[#1F3B73] opacity-70 mb-2">
                      Pour le prochain trimestre
                    </div>
                    <div className="text-[14px] leading-relaxed text-[#1F3B73] italic">
                      {bilan.nextStep}
                    </div>
                  </div>
                </div>

                {/* Upsell */}
                <div
                  className="relative rounded-2xl overflow-hidden"
                  style={{ background: "var(--navy-deep)", color: "var(--bg)" }}
                  data-testid="trim-upsell"
                >
                  <div className="relative p-8 md:p-10 flex items-center gap-6 flex-wrap">
                    <div
                      className="w-14 h-14 rounded-full grid place-items-center shrink-0"
                      style={{ background: "var(--gold)", color: "var(--navy-deep)" }}
                    >
                      <Crown size={20} />
                    </div>
                    <div className="flex-1 min-w-[280px]">
                      <div
                        className="text-[10px] tracking-[0.22em] uppercase mb-1"
                        style={{ color: "var(--gold)" }}
                      >
                        Inclus dans Sérénité · 89 €
                      </div>
                      <h3
                        className="text-[20px] md:text-[24px] leading-tight mb-2 font-bold"
                        style={{ color: "var(--bg)" }}
                      >
                        Reçois ce bilan imprimé chez toi, chaque trimestre.
                      </h3>
                      <p className="text-[13px] opacity-80 leading-relaxed">
                        Papier épais, reliure cousue, livré à Lyon. Un objet
                        physique pour mesurer ta trajectoire sans dépendre d&apos;un écran.
                      </p>
                    </div>
                    <button
                      className="btn-cta shrink-0"
                      data-testid="trim-upsell-cta"
                      onClick={() => alert("Mockup — bascule vers Sérénité 89 €/mois")}
                    >
                      Passer à Sérénité <ArrowRight size={14} />
                    </button>
                  </div>
                </div>

                <div className="mt-10 flex items-center justify-between text-[11px] text-[#6B7280]">
                  <div className="flex items-center gap-2">
                    <Sparkles size={11} className="text-[var(--gold)]" />
                    Généré par votre co-pilote · données privées, jamais partagées.
                  </div>
                  <div>Page 2 / 2 — {bilan.label}</div>
                </div>
              </div>
            </article>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default TrimestrielModal;