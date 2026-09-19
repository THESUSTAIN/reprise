import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Palette } from "lucide-react";
import { getVision, getStrategicMilestones, getStrategicDecisions } from "../lib/api";

const openCopilot = (ask) =>
  window.dispatchEvent(new CustomEvent("cours:open-copilot", { detail: ask ? { ask } : {} }));

// Ma Vision — refonte C+ : la clarté d'abord, l'atelier (canvas) un cran plus loin.
// Toutes les données sont réelles (vision, jalons, décisions). Un bloc sans
// donnée dit honnêtement comment le remplir — jamais de chiffre fabriqué.

const Num = ({ n }) => (
  <span className="inline-grid place-items-center w-8 h-8 rounded-lg border border-[#DEC2A3]/35 bg-[#DEC2A3]/12 font-head italic text-sm text-[#E8D5BC] mb-3">{n}</span>
);
const Eyebrow = ({ children }) => (
  <p className="text-[11px] font-semibold uppercase tracking-[.16em] text-[#DEC2A3] mb-2">{children}</p>
);
const Callout = ({ mot, children }) => (
  <div className="mt-4 rounded-xl border border-dashed border-[#DEC2A3]/40 bg-[#DEC2A3]/[.06] px-3.5 py-2.5 text-[12.5px] text-[#E8D5BC]">
    <span className="font-head italic font-semibold">{mot}</span> — {children}
  </div>
);
const Vide = ({ texte, cta, ask }) => (
  <div className="mt-2">
    <p className="text-[13px] text-white/50 leading-relaxed">{texte}</p>
    <button onClick={() => openCopilot(ask)}
      className="mt-3 inline-flex items-center gap-1.5 rounded-xl gold-bg px-4 py-2 text-sm font-semibold text-[#0A1128]">
      {cta} <ArrowRight size={14} />
    </button>
  </div>
);

const milestoneDone = (m) => {
  const s = String(m.status || m.statut || "").toLowerCase();
  return m.done === true || ["done", "atteint", "achieved", "completed", "terminé"].some((k) => s.includes(k));
};
const decisionTitle = (d) => d.title || d.question || d.titre || d.label || "Décision";
const decisionDone = (d) => {
  const s = String(d.status || d.statut || "").toLowerCase();
  return d.decided === true || d.applied === true || ["decided", "tranchée", "tranche", "applied", "done"].some((k) => s.includes(k));
};

export default function MaVision() {
  const navigate = useNavigate();
  const [vision, setVision] = useState(null);
  const [jalons, setJalons] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getVision().catch(() => null),
      getStrategicMilestones().catch(() => []),
      getStrategicDecisions().catch(() => []),
    ]).then(([v, j, d]) => {
      setVision(v);
      setJalons(Array.isArray(j) ? j : []);
      setDecisions(Array.isArray(d) ? d : []);
    }).finally(() => setLoading(false));
  }, []);

  const jalonsFaits = jalons.filter(milestoneDone).length;
  const decisionsOuvertes = decisions.filter((d) => !decisionDone(d));
  const progressPct = vision?.progress != null ? Math.round(Number(vision.progress)) : null;
  const alignPct = vision?.alignment_score != null ? Math.round(Number(vision.alignment_score)) : null;

  return (
    <div className="space-y-4" data-testid="page-ma-vision">
      {/* En-tête */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[.16em] text-[#DEC2A3]">Ma Vision · Pyramide de clarté</p>
          <h1 className="font-head text-2xl sm:text-3xl font-semibold text-white mt-1">
            D'abord le <em className="gold-text">pourquoi.</em>
          </h1>
          <p className="text-white/55 text-sm mt-1 max-w-xl">La vision ne sert à rien si elle ne descend pas jusqu'à la décision d'aujourd'hui.</p>
        </div>
      </div>

      {/* Synthèse chiffrée — uniquement des mesures réelles */}
      <div className="glass px-5 py-4 flex flex-wrap items-center gap-x-7 gap-y-3" data-testid="vision-synthese">
        <div>
          <p className="font-head text-lg font-semibold text-white">{loading ? "…" : progressPct != null ? `${progressPct}%` : "—"}</p>
          <p className="text-[10px] uppercase tracking-[.1em] text-white/45">Progression de la vision</p>
        </div>
        <div className="w-px h-8 bg-white/10 hidden sm:block" />
        <div>
          <p className="font-head text-lg font-semibold text-white">{loading ? "…" : `${jalonsFaits}/${jalons.length || 0}`}</p>
          <p className="text-[10px] uppercase tracking-[.1em] text-white/45">Jalons réalisés</p>
        </div>
        <div className="w-px h-8 bg-white/10 hidden sm:block" />
        <div>
          <p className="font-head text-lg font-semibold text-white">{loading ? "…" : decisionsOuvertes.length}</p>
          <p className="text-[10px] uppercase tracking-[.1em] text-white/45">Décisions à trancher</p>
        </div>
        <div className="w-px h-8 bg-white/10 hidden sm:block" />
        <div>
          <p className="font-head text-lg font-semibold text-white">{loading ? "…" : alignPct != null ? `${alignPct}%` : "—"}</p>
          <p className="text-[10px] uppercase tracking-[.1em] text-white/45">Alignement</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
        {/* 01 — Raison d'être */}
        <section className="glass p-6 md:col-span-4 relative overflow-hidden" data-testid="vision-raison-etre">
          <span className="absolute right-4 -top-8 font-head text-[130px] leading-none text-[#DEC2A3]/10 select-none" aria-hidden="true">“</span>
          <Num n="01" />
          <Eyebrow>Raison d'être · intemporel</Eyebrow>
          {vision?.why ? (
            <p className="font-head italic text-xl sm:text-2xl leading-relaxed text-[#F3E9DB] max-w-xl">« {vision.why} »</p>
          ) : (
            <Vide
              texte="Ta raison d'être n'est pas encore écrite. Une phrase suffit — c'est elle qui triera tes priorités."
              cta="L'écrire avec le Copilote"
              ask="Aide-moi à formuler ma raison d'être en une phrase, en partant de ce que je fais."
            />
          )}
          <Callout mot="Pourquoi">Pourquoi tu te lèves le matin ? C'est elle qui tient quand tout vacille.</Callout>
        </section>

        {/* 02 — Vision long terme */}
        <section className="glass p-6 md:col-span-2" data-testid="vision-long-terme">
          <Num n="02" />
          <Eyebrow>Vision long terme · 3 à 20 ans</Eyebrow>
          <h3 className="font-head font-semibold text-white">Qui tu deviens</h3>
          {vision?.where ? (
            <p className="text-[13px] text-white/60 leading-relaxed mt-2">{vision.where}</p>
          ) : (
            <p className="text-[13px] text-white/50 leading-relaxed mt-2">Pas encore écrite. Où veux-tu être dans 10 ans — sans t'épuiser ?</p>
          )}
        </section>

        {/* 03 — Stratégie */}
        <section className="glass p-6 md:col-span-3" data-testid="vision-strategie">
          <Num n="03" />
          <Eyebrow>Stratégie · 2 à 4 ans</Eyebrow>
          <h3 className="font-head font-semibold text-white">Comment tu y vas</h3>
          {vision?.how ? (
            <p className="text-[13px] text-white/60 leading-relaxed mt-2">{vision.how}</p>
          ) : (
            <p className="text-[13px] text-white/50 leading-relaxed mt-2">Pas encore définie. Un pilier à la fois, jamais trois.</p>
          )}
          <Callout mot="Comment">Comment tu y vas ? La stratégie est un choix de rythme autant que de moyens.</Callout>
        </section>

        {/* 04 — Jalons 90 jours (vraie donnée : jalons stratégiques) */}
        <section className="glass p-6 md:col-span-3" data-testid="vision-jalons">
          <Num n="04" />
          <Eyebrow>Objectifs · horizon 90 jours</Eyebrow>
          <h3 className="font-head font-semibold text-white">Les jalons du moment</h3>
          {jalons.length > 0 ? (
            <>
              <div className="mt-3 space-y-1">
                {jalons.slice(0, 4).map((j) => (
                  <div key={j.id || j.title || j.titre} className="flex items-center gap-2.5 py-1.5 border-b border-white/[.07] last:border-0 text-[13px]">
                    <span className={`w-2 h-2 rounded-full shrink-0 ${milestoneDone(j) ? "bg-emerald-400" : "bg-[#DEC2A3]"}`} />
                    <span className="text-white/80 truncate">{j.title || j.titre || j.name || "Jalon"}</span>
                    <span className={`ml-auto text-[10px] uppercase tracking-wide shrink-0 ${milestoneDone(j) ? "text-emerald-300" : "text-white/40"}`}>
                      {milestoneDone(j) ? "Atteint ✓" : (j.status || j.statut || "En cours")}
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <div className="flex justify-between text-[10.5px] text-white/50 mb-1.5">
                  <span>Jalons réalisés</span><span>{jalonsFaits} / {jalons.length}</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full rounded-full gold-bg" style={{ width: `${Math.round((jalonsFaits / jalons.length) * 100)}%` }} />
                </div>
              </div>
            </>
          ) : (
            <Vide
              texte="Aucun jalon pour l'instant. Trois jalons mesurables suffisent pour un trimestre — reliés à ton énergie réelle."
              cta="Préparer mes jalons"
              ask="Propose-moi 3 jalons mesurables pour les 90 prochains jours, adaptés à ma capacité actuelle."
            />
          )}
          <Callout mot="Quoi">Quel plan pour démarrer ? Mesurable, et à ton rythme.</Callout>
        </section>

        {/* 05 — Décisions à clarifier (vraie donnée : décisions stratégiques) */}
        <section className="glass p-6 md:col-span-3" data-testid="vision-decisions">
          <Num n="05" />
          <Eyebrow>Décisions à clarifier</Eyebrow>
          {decisions.length > 0 ? (
            <div className="mt-2 space-y-1">
              {decisions.slice(0, 4).map((d) => (
                <div key={d.id || decisionTitle(d)} className="flex items-center gap-2.5 py-2 border-b border-white/[.07] last:border-0 text-[13px]">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${decisionDone(d) ? "bg-emerald-400" : "bg-rose-300"}`} />
                  <span className="text-white/80 truncate">{decisionTitle(d)}</span>
                  <span className={`ml-auto text-[10px] uppercase tracking-wide shrink-0 ${decisionDone(d) ? "text-emerald-300" : "text-white/40"}`}>
                    {decisionDone(d) ? "Tranchée ✓" : "À trancher"}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <Vide
              texte="Aucune décision en attente. Quand quelque chose te turlupine, pose-le ici — on le clarifie avec tes propres variables (coût, rendement, risque, alignement)."
              cta="Clarifier une décision"
              ask="J'ai une décision à clarifier. Pose-moi les bonnes questions : coût, rendement, risque, scalabilité, alignement avec ma vision."
            />
          )}
        </section>

        {/* 06 — Idées en réserve (honnête : la réserve arrive) */}
        <section className="glass p-6 md:col-span-3" data-testid="vision-idees">
          <Num n="06" />
          <Eyebrow>Idées en réserve</Eyebrow>
          <h3 className="font-head font-semibold text-white">Elles fusent ? Pose-les, on trie après.</h3>
          <p className="text-[13px] text-white/50 leading-relaxed mt-2">
            La réserve d'idées arrive sur cette page. En attendant, confie chaque idée au Copilote — il les garde au chaud et t'aide à les trier quand tu es prête.
          </p>
          <button onClick={() => openCopilot("J'ai une idée qui fuse. Note-la et dis-moi comment tu vas m'aider à la trier.")}
            className="mt-3 inline-flex items-center gap-1.5 rounded-xl gold-bg px-4 py-2 text-sm font-semibold text-[#0A1128]"
            data-testid="vision-idees-copilot">
            Confier une idée au Copilote <ArrowRight size={14} />
          </button>
        </section>

        {/* Atelier visuel — le canvas complet, un cran plus loin */}
        <section className="glass p-6 md:col-span-6 flex flex-col sm:flex-row sm:items-center gap-5" data-testid="vision-atelier">
          <div className="flex-1">
            <Eyebrow>Atelier visuel · le Vision Board complet</Eyebrow>
            <h3 className="font-head text-lg font-semibold text-white">Canvas libre, moodboard, génération IA, export PDF</h3>
            <p className="text-[13px] text-white/50 mt-1 max-w-2xl">Ton outil de création complet vit ici, un cran plus loin — sans écraser ta clarté du jour.</p>
          </div>
          <button onClick={() => navigate("/vision/atelier")}
            className="inline-flex items-center gap-2 rounded-full gold-bg px-5 py-3 text-sm font-semibold text-[#0A1128] shrink-0"
            data-testid="vision-open-atelier">
            <Palette size={16} /> Ouvrir l'atelier visuel
          </button>
        </section>
      </div>
    </div>
  );
}
