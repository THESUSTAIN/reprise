import React from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, Clock, TrendingUp } from "lucide-react";

/**
 * MissionHeroCard v2 — refonte "less-blue" demandée par utilisatrice.
 *
 * Avant : carte 100% navy géante qui "piquait les yeux".
 * Après : carte CRÈME claire avec accents navy et bordure dorée subtile.
 *   - Plus aérée (padding plus généreux, plus de respiration)
 *   - Texte sombre sur fond crème → lecture confortable
 *   - Score Business en pastille latérale propre (pas une grosse box navy)
 *   - Boutons : bordeaux (Démarrer) reste l'accent rouge signal,
 *               navy (Déléguer) en outline plus discret,
 *               ghost (Reporter) en text-button
 */
export default function MissionHeroCard({ mission, score, delta = "+4 cette sem.", verdict = "Build it — continue la trajectoire" }) {
  const navigate = useNavigate();
  const title = mission?.title || "Aujourd'hui : pose une décision simple, et libère ta journée.";
  const subtitle = mission?.description
    || "Ton co-pilote a préparé un brief : un signal clair pour avancer sans dispersion.";
  const scoreVal = typeof score === "number" ? score : (typeof score === "string" ? parseInt(score, 10) : null);

  const onStart = () => {
    // /taches n'existe pas — on délègue l'action au Collaborateur IA (ouverture panel)
    window.dispatchEvent(new CustomEvent("zayado:open-collab", { detail: { intent: "start-mission" } }));
  };
  const onDelegate = () => {
    window.dispatchEvent(new CustomEvent("zayado:open-collab", { detail: { intent: "delegate-mission" } }));
  };
  const onSnooze = async () => {
    try {
      const token = localStorage.getItem("mxai_token");
      await fetch(`${process.env.REACT_APP_BACKEND_URL || ""}/api/missions/snooze`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ snooze_days: 1 }),
      }).catch(() => {});
    } catch (e) { /* silent */ }
  };

  return (
    <section
      className="relative rounded-3xl overflow-hidden shadow-md mb-6 bg-white"
      style={{
        background: "linear-gradient(135deg, #fbfaf6 0%, #f3ece0 100%)",
        outline: "1px solid rgba(184,152,85,0.15)",
      }}
      data-testid="mission-hero-card"
    >
      {/* Filet doré supérieur (signature visuelle Zayado) */}
      <div className="h-1" style={{ background: "linear-gradient(90deg, transparent, #b89855 30%, #d4b982 70%, transparent)" }} />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 p-6 sm:p-8 lg:p-10">
        {/* Left : mission */}
        <div className="lg:col-span-8">
          <div className="flex items-center gap-3 flex-wrap mb-3">
            <span
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10.5px] font-bold tracking-[0.16em]"
              style={{ background: "#1a3a6e", color: "#f3e9d0" }}
            >
              <Sparkles size={11} /> STUDIO SÉRÉNITÉ
            </span>
            <span className="text-[10.5px] tracking-[0.18em] uppercase font-semibold" style={{ color: "#6b6358" }}>
              Mission du jour · posée par votre co-pilote
            </span>
          </div>

          <h2
            className="font-display text-[24px] sm:text-[28px] lg:text-[32px] leading-[1.12] mb-3"
            style={{ color: "#1a1815", letterSpacing: "-0.025em", fontWeight: 700 }}
            data-testid="mission-hero-title"
          >
            {title}
          </h2>
          <p className="text-[13.5px] leading-relaxed mb-6 max-w-2xl" style={{ color: "#6b6358" }}>
            {subtitle}
          </p>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={onStart}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-[13px] font-semibold transition shadow-md hover:shadow-lg"
              style={{ background: "#1a3a6e", color: "#f3e9d0" }}
              data-testid="mission-hero-start"
            >
              <Sparkles size={13} /> Démarrer cette mission
            </button>
            <button
              onClick={onDelegate}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-[13px] font-medium transition hover:bg-[#1a3a6e]/5"
              style={{ background: "transparent", color: "#1a3a6e", outline: "1.5px solid rgba(26,58,110,0.22)" }}
              data-testid="mission-hero-delegate"
            >
              <Sparkles size={13} /> Déléguer à l'IA
            </button>
            <button
              onClick={onSnooze}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-[12.5px] transition hover:bg-black/5"
              style={{ background: "transparent", color: "#6b6358" }}
              data-testid="mission-hero-snooze"
            >
              <Clock size={12} /> Reporter à demain
            </button>
          </div>
        </div>

        {/* Right : Score Business (pastille latérale, pas une grosse box) */}
        <div className="lg:col-span-4">
          <div
            className="rounded-2xl p-5 h-full flex flex-col bg-white shadow-md"
            data-testid="mission-hero-score"
          >
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg grid place-items-center"
                   style={{ background: "#f3e9d0", color: "#b89855" }}>
                <TrendingUp size={14} />
              </div>
              <div className="text-[10.5px] tracking-[0.22em] uppercase font-bold" style={{ color: "#6b6358" }}>
                Score business
              </div>
            </div>

            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-[42px] font-bold leading-none" style={{ color: "#1a3a6e" }}>
                {scoreVal == null ? "—" : scoreVal}
              </span>
              <span className="text-[13px]" style={{ color: "#6b6358" }}>/100</span>
              <span className="ml-auto text-[11px] font-semibold px-2 py-0.5 rounded-full"
                    style={{ background: "rgba(45,106,79,0.1)", color: "#2D6A4F" }}>{delta}</span>
            </div>
            <div className="text-[11.5px] italic mb-4" style={{ color: "#6b6358" }}>
              Verdict IA : <span className="font-semibold" style={{ color: "#1a3a6e" }}>{verdict}</span>
            </div>

            {/* Barre 70% IA / 30% HUMAIN */}
            <div className="mt-auto">
              <div className="flex h-1.5 rounded-full overflow-hidden mb-2" style={{ background: "#f0ebe0" }}>
                <div style={{ width: "70%", background: "#b89855" }} />
                <div style={{ width: "30%", background: "#d4b982" }} />
              </div>
              <div className="flex justify-between text-[9.5px] tracking-[0.18em] uppercase font-semibold">
                <span style={{ color: "#b89855" }}>● 70 % IA</span>
                <span style={{ color: "#6b6358" }}>30 % humain</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
