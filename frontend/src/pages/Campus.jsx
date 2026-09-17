import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight, BriefcaseBusiness, Building2, CheckCircle2, CircleDot,
  GraduationCap, Lightbulb, Loader2, MessageSquareText, Sparkles,
  Trophy, UsersRound,
} from "lucide-react";
import { toast } from "sonner";
import {
  getCampusSimulationHistory, getCampusSimulationState,
  startCampusSimulation, submitCampusMission,
} from "../lib/api";

const PARCOURS = [
  { id: "alternance", label: "Alternance & études", detail: "Vous entraîner avant ou pendant votre alternance." },
  { id: "reconversion", label: "Reconversion", detail: "Prendre des repères avant un nouveau métier." },
  { id: "salarie", label: "Progression salariée", detail: "Développer votre autonomie dans votre poste actuel." },
];

const DIPLOMES = [
  { value: "licence", label: "Bac +3 / Licence" },
  { value: "licence_pro", label: "Licence professionnelle" },
  { value: "bachelor", label: "Bachelor" },
  { value: "master", label: "Master" },
  { value: "mba", label: "MBA / formation continue" },
];

function realScore(value) {
  const score = Number(value);
  return Number.isFinite(score) ? `${Math.round(score)} / 100` : "—";
}

const SECTION_COPY = {
  today: { eyebrow: "MyExtension Campus", title: "Apprendre le travail en le pratiquant.", description: "Campus prépare étudiants, alternants, personnes en reconversion et salariés à des situations professionnelles concrètes." },
  enterprise: { eyebrow: "Mon entreprise", title: "Comprendre un environnement professionnel.", description: "Explorez l’entreprise virtuelle, ses interlocuteurs et les situations qui donnent un contexte à vos missions." },
  missions: { eyebrow: "Missions", title: "Traiter une situation, pas réciter une leçon.", description: "Chaque mission vous met face à un besoin concret : vous analysez, formulez une réponse, puis recevez un feedback." },
  coach: { eyebrow: "Coach IA", title: "Réfléchir avant d’agir.", description: "Le Coach IA vous aide à structurer votre raisonnement ; il ne fait pas votre travail à votre place." },
  progress: { eyebrow: "Progression", title: "Voir les compétences que vous démontrez.", description: "Votre évolution repose sur les missions réellement traitées et évaluées, jamais sur un score décoratif." },
  portfolio: { eyebrow: "Portfolio", title: "Conserver vos preuves de compétences.", description: "Vos réalisations évaluées forment progressivement un portfolio que vous pourrez présenter lorsque les passerelles partenaires seront activées." },
  alternance: { eyebrow: "Alternance", title: "Préparer votre entrée en entreprise.", description: "Campus aide à rendre vos compétences visibles avant l’alternance, la reconversion ou une évolution professionnelle." },
};

export default function Campus({ activeSection = "today" }) {
  const navigate = useNavigate();
  const [state, setState] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [requiresLogin, setRequiresLogin] = useState(false);
  const [track, setTrack] = useState("reconversion");
  const [programme, setProgramme] = useState("");
  const [diploma, setDiploma] = useState("bachelor");
  const [starting, setStarting] = useState(false);
  const [selectedMission, setSelectedMission] = useState(null);
  const [response, setResponse] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [simulation, portfolio] = await Promise.all([
        getCampusSimulationState(),
        getCampusSimulationHistory(),
      ]);
      setState(simulation || { started: false });
      setHistory(Array.isArray(portfolio?.items) ? portfolio.items : []);
      setRequiresLogin(false);
    } catch (error) {
      if (error?.response?.status === 401 || error?.response?.status === 403) setRequiresLogin(true);
      else toast.error("Campus ne peut pas être chargé pour le moment.");
      setState({ started: false });
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const start = async (event) => {
    event.preventDefault();
    if (requiresLogin) { navigate("/login"); return; }
    if (programme.trim().length < 3) {
      toast.error("Indiquez le domaine ou le métier dans lequel vous voulez vous entraîner.");
      return;
    }
    setStarting(true);
    try {
      await startCampusSimulation({
        programme_label: `${PARCOURS.find((item) => item.id === track)?.label || "Campus"} — ${programme.trim()}`,
        diploma_level: diploma,
      });
      toast.success("Votre environnement professionnel est prêt.");
      await refresh();
    } catch (error) {
      const detail = error?.response?.data?.detail;
      toast.error(detail || "La simulation n’a pas pu être démarrée.");
    } finally {
      setStarting(false);
    }
  };

  const submit = async () => {
    if (!selectedMission || response.trim().length < 10) {
      toast.error("Formulez votre réponse en quelques phrases avant de demander un feedback.");
      return;
    }
    setSubmitting(true);
    try {
      const result = await submitCampusMission(selectedMission.id, response.trim());
      setFeedback(result?.feedback || result);
      setResponse("");
      toast.success("Votre réponse a été évaluée. La prochaine situation est prête.");
      await refresh();
    } catch (error) {
      const detail = error?.response?.data?.detail;
      toast.error(detail || "Le feedback n’a pas pu être généré.");
    } finally {
      setSubmitting(false);
    }
  };

  const missions = (state?.clients || []).map((client) => ({ ...client.current_task, clientName: client.name, clientIndustry: client.industry })).filter(Boolean);
  const copy = SECTION_COPY[activeSection] || SECTION_COPY.today;

  return (
    <div className="space-y-6" data-testid="page-campus">
      <section className="glass relative overflow-hidden p-6 sm:p-8">
        <div className="absolute -right-16 -top-20 h-48 w-48 rounded-full bg-[#DEC2A3]/10 blur-3xl" aria-hidden="true" />
        <div className="relative max-w-3xl">
          <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[.16em] text-[#DEC2A3]"><GraduationCap size={15} /> {copy.eyebrow}</div>
          <h1 className="font-head mt-2 text-3xl font-semibold text-white sm:text-4xl">{copy.title}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-white/65">{copy.description} L’IA structure la simulation et le feedback ; vous gardez le raisonnement, la décision et l’action.</p>
          <div className="mt-5 flex flex-wrap gap-2 text-xs text-white/70">
            <span className="rounded-full border border-white/15 bg-white/[.06] px-3 py-1.5">Simuler</span>
            <span className="rounded-full border border-white/15 bg-white/[.06] px-3 py-1.5">Réfléchir</span>
            <span className="rounded-full border border-white/15 bg-white/[.06] px-3 py-1.5">Agir</span>
            <span className="rounded-full border border-white/15 bg-white/[.06] px-3 py-1.5">Recevoir un feedback</span>
          </div>
        </div>
      </section>

      {loading ? (
        <div className="glass flex min-h-56 items-center justify-center gap-3 text-sm text-white/60"><Loader2 className="animate-spin" size={18} /> Chargement de votre environnement Campus…</div>
      ) : requiresLogin ? (
        <section className="glass p-6 sm:p-8" data-testid="campus-login-state">
          <p className="text-[11px] font-semibold uppercase tracking-[.16em] text-[#DEC2A3]">Accès personnel</p>
          <h2 className="font-head mt-2 text-2xl font-semibold text-white">Votre environnement s’ouvre après connexion.</h2>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-white/60">La simulation, les réponses et le portfolio sont personnels. Connectez-vous pour démarrer ou retrouver votre progression.</p>
          <button onClick={() => navigate("/login")} className="gold-bg mt-5 inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-[#0A1128]">Se connecter <ArrowRight size={15} /></button>
        </section>
      ) : !state?.started ? (
        <section className="grid grid-cols-1 gap-4 lg:grid-cols-[1.1fr_.9fr]">
          <form onSubmit={start} className="glass p-6" data-testid="campus-start-form">
            <p className="text-[11px] font-semibold uppercase tracking-[.16em] text-[#DEC2A3]">Première configuration</p>
            <h2 className="font-head mt-2 text-xl font-semibold text-white">Dans quel contexte voulez-vous progresser ?</h2>
            <p className="mt-1 text-sm text-white/55">Ces informations servent uniquement à construire votre environnement professionnel simulé.</p>
            <div className="mt-5 grid grid-cols-1 gap-2 sm:grid-cols-3">
              {PARCOURS.map((item) => <button key={item.id} type="button" onClick={() => setTrack(item.id)} className={`rounded-xl border p-3 text-left transition-colors ${track === item.id ? "border-[#DEC2A3]/60 bg-[#DEC2A3]/10" : "border-white/15 bg-white/[.03] hover:bg-white/[.06]"}`}><span className="block text-sm font-semibold text-white">{item.label}</span><span className="mt-1 block text-xs leading-relaxed text-white/50">{item.detail}</span></button>)}
            </div>
            <label className="mt-5 block text-xs font-medium text-white/65">Métier, domaine ou formation visé(e)</label>
            <input value={programme} onChange={(event) => setProgramme(event.target.value)} placeholder="Ex. marketing digital, gestion de projet, relation client…" className="mt-1.5 w-full rounded-xl border border-white/15 bg-white/[.05] px-3.5 py-2.5 text-sm text-white placeholder:text-white/35 outline-none focus:border-[#DEC2A3]/60" />
            <label className="mt-4 block text-xs font-medium text-white/65">Niveau de départ</label>
            <select value={diploma} onChange={(event) => setDiploma(event.target.value)} className="mt-1.5 w-full rounded-xl border border-white/15 bg-[#102554] px-3.5 py-2.5 text-sm text-white outline-none focus:border-[#DEC2A3]/60">{DIPLOMES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select>
            <button disabled={starting} className="gold-bg mt-5 inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-[#0A1128] disabled:opacity-50">{starting ? <><Loader2 className="animate-spin" size={15} /> Préparation…</> : <><Sparkles size={15} /> Créer mon entreprise virtuelle</>}</button>
          </form>
          <aside className="glass p-6">
            <p className="text-[11px] font-semibold uppercase tracking-[.16em] text-[#DEC2A3]">Ce qui vous attend</p>
            <div className="mt-5 space-y-4">
              <CampusStep icon={Building2} title="Un environnement professionnel" detail="Une entreprise virtuelle et des interlocuteurs adaptés à votre domaine." />
              <CampusStep icon={MessageSquareText} title="Des missions situées" detail="Un besoin client, une demande manager ou un incident à résoudre." />
              <CampusStep icon={Lightbulb} title="Un feedback qui fait réfléchir" detail="Le système évalue votre réponse ; il ne produit pas votre travail à votre place." />
              <CampusStep icon={Trophy} title="Un portfolio réel" detail="Vos réponses évaluées constituent progressivement vos preuves de compétences." />
            </div>
          </aside>
        </section>
      ) : (
        <>
          <section className="grid grid-cols-1 gap-4 lg:grid-cols-[1.25fr_.75fr]">
            <div className="glass p-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div><p className="text-[11px] font-semibold uppercase tracking-[.16em] text-[#DEC2A3]">Mon entreprise simulée</p><h2 className="font-head mt-1 text-xl font-semibold text-white">{state.domain || state.programme_label}</h2><p className="mt-1 text-sm text-white/55">Jour {state.current_day || 1} de votre parcours professionnel.</p></div>
                <span className="rounded-full border border-emerald-300/25 bg-emerald-300/10 px-3 py-1.5 text-xs font-medium text-emerald-200">Simulation active</span>
              </div>
              <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
                <Metric label="Missions évaluées" value={state.tasks_completed ?? 0} />
                <Metric label="Score moyen" value={state.tasks_completed ? realScore(state.average_score) : "—"} />
                <Metric label="Interlocuteurs" value={state.clients?.length ?? 0} />
              </div>
            </div>
            <div className="glass p-6"><p className="text-[11px] font-semibold uppercase tracking-[.16em] text-[#DEC2A3]">Coach de réflexion</p><h2 className="font-head mt-2 text-lg font-semibold text-white">L’IA ne répond pas à votre place.</h2><p className="mt-2 text-sm leading-relaxed text-white/60">Avant d’écrire, identifiez l’objectif, les informations manquantes et la personne à qui vous répondez. Le feedback intervient après votre proposition.</p><div className="mt-4 flex items-center gap-2 text-xs text-white/70"><CircleDot size={14} className="text-[#DEC2A3]" /> Commencez par une seule mission.</div></div>
          </section>

          <section className="grid grid-cols-1 gap-4 xl:grid-cols-[1.2fr_.8fr]">
            <div className="glass p-6">
              <div className="flex items-center justify-between gap-3"><div><p className="text-[11px] font-semibold uppercase tracking-[.16em] text-[#DEC2A3]">Missions disponibles</p><h2 className="font-head mt-1 text-xl font-semibold text-white">Quelle situation allez-vous traiter ?</h2></div><span className="text-xs text-white/45">{missions.length} en attente</span></div>
              <div className="mt-5 space-y-3">{missions.length === 0 ? <p className="rounded-xl border border-dashed border-white/15 px-4 py-5 text-sm text-white/55">Aucune nouvelle mission n’est disponible pour l’instant.</p> : missions.map((mission) => <button key={mission.id} onClick={() => { setSelectedMission(mission); setFeedback(null); }} className={`w-full rounded-xl border p-4 text-left transition-colors ${selectedMission?.id === mission.id ? "border-[#DEC2A3]/60 bg-[#DEC2A3]/10" : "border-white/15 bg-white/[.03] hover:bg-white/[.06]"}`}><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs text-[#F1E2CC]">{mission.clientName} · {mission.clientIndustry || "Entreprise"}</p><h3 className="mt-1 text-sm font-semibold text-white">{mission.title}</h3><p className="mt-1 text-xs leading-relaxed text-white/55">{mission.description || "Ouvrez la mission pour préparer votre réponse."}</p></div><span className="rounded-full border border-white/15 px-2 py-1 text-[11px] text-white/60">Difficulté {mission.difficulty || 1}/5</span></div></button>)}</div>
            </div>
            <aside className="glass p-6">
              <p className="text-[11px] font-semibold uppercase tracking-[.16em] text-[#DEC2A3]">Portfolio</p>
              <h2 className="font-head mt-1 text-xl font-semibold text-white">Des preuves, pas seulement une note.</h2>
              {history.length === 0 ? <p className="mt-4 text-sm leading-relaxed text-white/55">Votre portfolio s’alimentera avec les missions que vous aurez réellement traitées et fait évaluer.</p> : <div className="mt-4 space-y-3">{history.slice(0, 3).map((item) => <div key={item.response_id} className="rounded-xl border border-white/12 bg-white/[.03] p-3"><p className="text-xs font-medium text-white">{item.task_title}</p><p className="mt-1 text-xs text-white/50">{item.client_name} · score {realScore(item.score)}</p></div>)}</div>}
              <div className="mt-5 border-t border-white/10 pt-4"><p className="text-[11px] font-semibold uppercase tracking-[.16em] text-white/45">Alternance & emploi</p><p className="mt-2 text-xs leading-relaxed text-white/55">La mise en relation avec des entreprises partenaires n’est pas encore connectée. Votre portfolio restera exportable lorsque ce parcours sera activé.</p><button onClick={() => navigate("/collaborateur")} className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-[#F1E2CC] hover:text-white">Préparer mon projet avec Zayado <ArrowRight size={13} /></button></div>
            </aside>
          </section>

          {selectedMission && <section className="glass p-6" data-testid="campus-mission-workspace"><p className="text-[11px] font-semibold uppercase tracking-[.16em] text-[#DEC2A3]">Réponse à préparer</p><h2 className="font-head mt-1 text-xl font-semibold text-white">{selectedMission.title}</h2><p className="mt-2 max-w-3xl text-sm leading-relaxed text-white/60">Avant de rédiger, demandez-vous : quel est l’enjeu, quelle information manque, et quelle réponse est la plus juste pour cet interlocuteur ?</p><textarea value={response} onChange={(event) => setResponse(event.target.value)} rows={6} placeholder="Formulez votre analyse et votre proposition de réponse…" className="mt-5 w-full rounded-xl border border-white/15 bg-white/[.04] px-4 py-3 text-sm text-white placeholder:text-white/35 outline-none focus:border-[#DEC2A3]/60" /><button onClick={submit} disabled={submitting || response.trim().length < 10} className="gold-bg mt-4 inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-[#0A1128] disabled:opacity-50">{submitting ? <><Loader2 className="animate-spin" size={15} /> Évaluation…</> : <><CheckCircle2 size={15} /> Demander un feedback</>}</button>{feedback && <div className="mt-5 rounded-xl border border-emerald-300/25 bg-emerald-300/[.08] p-4 text-sm text-emerald-50"><p className="font-semibold">Feedback reçu</p><p className="mt-1 leading-relaxed text-emerald-50/80">{typeof feedback === "string" ? feedback : feedback.feedback || feedback.summary || "Votre retour a été enregistré."}</p></div>}</section>}
        </>
      )}
    </div>
  );
}

function CampusStep({ icon: Icon, title, detail }) {
  return <div className="flex gap-3"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/15 bg-white/[.06] text-[#F1E2CC]"><Icon size={17} /></span><div><p className="text-sm font-semibold text-white">{title}</p><p className="mt-0.5 text-xs leading-relaxed text-white/55">{detail}</p></div></div>;
}

function Metric({ label, value }) {
  return <div className="rounded-xl border border-white/12 bg-white/[.04] p-3"><p className="text-[11px] text-white/50">{label}</p><p className="font-head mt-1 text-lg font-semibold text-white">{value}</p></div>;
}
