import React, { useEffect, useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, CircleDot, Compass, Flag, Loader2, Plus, Sparkles, Target, TimerReset, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import {
  applyStrategicDecision,
  createStrategicDecision,
  createStrategicMilestone,
  getProjets,
  getStrategicDecisions,
  getStrategicMilestones,
  getStrategyOverview,
  getVision,
  updateStrategicDecision,
} from "../../lib/api";

const WINDOWS = [
  { id: "now", label: "Maintenant", hint: "Le prochain jalon qui mérite votre attention." },
  { id: "next", label: "Ensuite", hint: "À préparer après l’engagement actuel." },
  { id: "later", label: "Plus tard", hint: "À garder visible sans le confondre avec l’urgence." },
];

const EMPTY = { milestones: [], decisions: [], tasks: [] };

function visionText(value) {
  if (!value) return "Votre Cap n’est pas encore rédigé.";
  if (typeof value === "string") return value;
  return value.value || value.vision || value.content || value.text || "Votre Cap n’est pas encore rédigé.";
}

function strategicStatus(value) {
  return ({ active: "En mouvement", planned: "À préparer", watch: "À surveiller", complete: "Prouvé", deferred: "Reporté", abandoned: "Abandonné" })[value] || "À préciser";
}

export function StrategicCapHome({ onOpenHorizon, onOpenDecisions, onOpenPillars }) {
  const [overview, setOverview] = useState(EMPTY);
  const [vision, setVision] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const [strategy, savedVision] = await Promise.allSettled([getStrategyOverview(), getVision()]);
    if (strategy.status === "fulfilled") setOverview({ ...EMPTY, ...strategy.value });
    if (savedVision.status === "fulfilled") setVision(savedVision.value);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const now = useMemo(() => (overview.milestones || []).filter((item) => item.time_window === "now" && !["complete", "abandoned"].includes(item.status)), [overview]);
  const pending = useMemo(() => (overview.decisions || []).find((item) => item.status === "pending"), [overview]);
  const approvedTasks = useMemo(() => (overview.tasks || []).filter((task) => task.strategic_milestone_id && !task.done), [overview]);

  return (
    <section className="glass mb-5 overflow-hidden p-5 md:p-6" data-testid="strategic-cap-home">
      <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
        <div className="max-w-3xl">
          <span className="mb-2 inline-flex items-center gap-2 text-[10px] font-bold tracking-[.16em] text-[#F1E2CC]"><Compass size={13} /> MON CAP VIVANT</span>
          <h2 className="font-head text-2xl font-semibold text-white md:text-3xl">{visionText(vision)}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-white/70">Votre Vision se transforme ici en axes, jalons et décisions. Mon Mouvement exécute ; la Vision arbitre le pourquoi.</p>
        </div>
        <button onClick={onOpenPillars} className="gold-bg inline-flex shrink-0 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-[#0B1F3A]"><Target size={15} /> Voir mes axes</button>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-[1.15fr_.85fr_.85fr]">
        <article className="rounded-2xl border border-white/20 bg-white/[0.08] p-4">
          <div className="flex items-center justify-between gap-3"><span className="text-[10px] font-bold tracking-[.14em] text-[#F1E2CC]">LE PROCHAIN JALON</span><Flag size={15} className="text-[#F1E2CC]" /></div>
          {loading ? <div className="mt-5 flex items-center gap-2 text-sm text-white/55"><Loader2 size={15} className="animate-spin" /> Lecture de la trajectoire…</div> : now[0] ? <><h3 className="mt-3 text-base font-semibold text-white">{now[0].title}</h3><p className="mt-1 text-sm text-white/65">{now[0].expected_evidence || "Preuve à préciser"}</p><button onClick={onOpenHorizon} className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-[#F1E2CC]">Voir l’Horizon 90 jours <ArrowRight size={13} /></button></> : <><p className="mt-3 text-sm text-white/65">Aucun jalon actif. Créez la prochaine étape qui rendra votre Cap concret.</p><button onClick={onOpenHorizon} className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-[#F1E2CC]">Créer un jalon <Plus size={13} /></button></>}
        </article>
        <article className="rounded-2xl border border-white/20 bg-white/[0.08] p-4">
          <span className="text-[10px] font-bold tracking-[.14em] text-[#F1E2CC]">DÉCISION PRIORITAIRE</span>
          {pending ? <><h3 className="mt-3 text-base font-semibold text-white">{pending.title}</h3><p className="mt-1 line-clamp-2 text-sm text-white/65">{pending.why_now || "Raisonnement à préciser."}</p><button onClick={onOpenDecisions} className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-[#F1E2CC]">Décider maintenant <ArrowRight size={13} /></button></> : <><p className="mt-3 text-sm text-white/65">Aucune décision stratégique en attente.</p><button onClick={onOpenDecisions} className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-[#F1E2CC]">Préparer une décision <Plus size={13} /></button></>}
        </article>
        <article className="rounded-2xl border border-white/20 bg-white/[0.08] p-4">
          <span className="text-[10px] font-bold tracking-[.14em] text-[#F1E2CC]">PREUVES D’EXÉCUTION</span>
          <strong className="mt-3 block font-head text-3xl text-white">{approvedTasks.length || "—"}</strong>
          <p className="mt-1 text-sm text-white/65">{approvedTasks.length ? "mission(s) liée(s) à un jalon en cours." : "Aucune mission stratégique ouverte pour le moment."}</p>
          <button onClick={onOpenHorizon} className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-[#F1E2CC]">Relier ma trajectoire <ArrowRight size={13} /></button>
        </article>
      </div>
    </section>
  );
}

export function StrategicHorizon() {
  const [milestones, setMilestones] = useState([]);
  const [projects, setProjects] = useState([]);
  const [form, setForm] = useState({ title: "", pillar_id: "", time_window: "now", expected_evidence: "", project_id: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    const [savedMilestones, savedProjects] = await Promise.allSettled([getStrategicMilestones(), getProjets()]);
    if (savedMilestones.status === "fulfilled") setMilestones(savedMilestones.value || []);
    if (savedProjects.status === "fulfilled") setProjects(Array.isArray(savedProjects.value) ? savedProjects.value : (savedProjects.value?.items || []));
  };
  useEffect(() => { load(); }, []);

  const create = async (event) => {
    event.preventDefault();
    if (!form.title.trim()) return toast.error("Donnez un nom concret au jalon.");
    setSaving(true);
    try {
      await createStrategicMilestone({ ...form, title: form.title.trim(), project_id: form.project_id || null, pillar_id: form.pillar_id.trim() || null });
      setForm({ title: "", pillar_id: "", time_window: "now", expected_evidence: "", project_id: "" });
      await load();
      toast.success("Jalon stratégique créé.");
    } catch (error) { toast.error(error?.response?.data?.detail || "Impossible d’enregistrer ce jalon."); }
    finally { setSaving(false); }
  };

  return <section className="space-y-4" data-testid="strategic-horizon">
    <div className="glass p-5"><span className="text-[10px] font-bold tracking-[.16em] text-[#F1E2CC]">HORIZON 90 JOURS</span><h2 className="mt-2 font-head text-2xl font-semibold text-white">Rendre le Cap visible sans transformer chaque idée en urgence.</h2><p className="mt-1 max-w-3xl text-sm text-white/65">Un jalon est une preuve attendue ou une étape stratégique ; une mission ne sera créée qu’après une décision validée.</p></div>
    <form onSubmit={create} className="glass grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-5">
      <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Prochain jalon stratégique" className="rounded-xl border border-white/25 bg-white/[0.08] px-3 py-2.5 text-sm text-white outline-none placeholder:text-white/45 focus:border-[#F1E2CC] xl:col-span-2" />
      <input value={form.pillar_id} onChange={(e) => setForm({ ...form, pillar_id: e.target.value })} placeholder="Axe ou pilier (optionnel)" className="rounded-xl border border-white/25 bg-white/[0.08] px-3 py-2.5 text-sm text-white outline-none placeholder:text-white/45 focus:border-[#F1E2CC]" />
      <select value={form.time_window} onChange={(e) => setForm({ ...form, time_window: e.target.value })} className="rounded-xl border border-white/25 bg-[#172C5C] px-3 py-2.5 text-sm text-white outline-none focus:border-[#F1E2CC]"><option value="now">Maintenant</option><option value="next">Ensuite</option><option value="later">Plus tard</option></select>
      <select value={form.project_id} onChange={(e) => setForm({ ...form, project_id: e.target.value })} className="rounded-xl border border-white/25 bg-[#172C5C] px-3 py-2.5 text-sm text-white outline-none focus:border-[#F1E2CC]"><option value="">Projet lié (optionnel)</option>{projects.map((project) => <option key={project.id} value={project.id}>{project.nom || project.name || project.title}</option>)}</select>
      <input value={form.expected_evidence} onChange={(e) => setForm({ ...form, expected_evidence: e.target.value })} placeholder="Quelle preuve attendue ?" className="rounded-xl border border-white/25 bg-white/[0.08] px-3 py-2.5 text-sm text-white outline-none placeholder:text-white/45 focus:border-[#F1E2CC] md:col-span-2 xl:col-span-4" />
      <button disabled={saving} className="gold-bg inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-[#0B1F3A] disabled:opacity-60">{saving ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />} Créer le jalon</button>
    </form>
    <div className="grid gap-4 xl:grid-cols-3">{WINDOWS.map((window) => <section key={window.id} className="glass min-h-64 p-4"><div className="flex items-start justify-between gap-3"><div><span className="text-[10px] font-bold tracking-[.14em] text-[#F1E2CC]">{window.label.toUpperCase()}</span><p className="mt-1 text-xs leading-5 text-white/55">{window.hint}</p></div><TimerReset size={15} className="text-white/50" /></div><div className="mt-4 space-y-2">{milestones.filter((item) => item.time_window === window.id).map((item) => <article key={item.id} className="rounded-xl border border-white/20 bg-white/[0.08] p-3"><div className="flex gap-2"><CircleDot size={14} className="mt-0.5 shrink-0 text-[#F1E2CC]" /><div><strong className="text-sm text-white">{item.title}</strong><p className="mt-1 text-xs text-white/60">{item.expected_evidence || "Preuve à préciser"}</p><span className="mt-2 inline-block text-[10px] font-semibold text-[#F1E2CC]">{strategicStatus(item.status)}</span></div></div></article>)}{!milestones.some((item) => item.time_window === window.id) && <p className="rounded-xl border border-dashed border-white/20 p-3 text-xs leading-5 text-white/50">Aucun jalon ici. Cette fenêtre reste volontairement vide tant que vous ne l’avez pas choisi.</p>}</div></section>)}</div>
  </section>;
}

export function StrategicDecisions() {
  const [decisions, setDecisions] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [form, setForm] = useState({ title: "", detail: "", why_now: "", impact: "", milestone_id: "", priority: "normal" });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    const [savedDecisions, savedMilestones] = await Promise.allSettled([getStrategicDecisions(), getStrategicMilestones()]);
    if (savedDecisions.status === "fulfilled") setDecisions(savedDecisions.value || []);
    if (savedMilestones.status === "fulfilled") setMilestones(savedMilestones.value || []);
  };
  useEffect(() => { load(); }, []);

  const create = async (event) => {
    event.preventDefault();
    if (!form.title.trim()) return toast.error("La décision doit être formulée clairement.");
    setSaving(true);
    try { await createStrategicDecision({ ...form, title: form.title.trim(), milestone_id: form.milestone_id || null }); setForm({ title: "", detail: "", why_now: "", impact: "", milestone_id: "", priority: "normal" }); await load(); toast.success("Décision prête à être validée."); }
    catch (error) { toast.error(error?.response?.data?.detail || "Impossible de créer la décision."); }
    finally { setSaving(false); }
  };
  const approve = async (decision) => {
    try { await applyStrategicDecision(decision.id); await load(); toast.success("Mission créée dans Mon Mouvement."); }
    catch (error) { toast.error(error?.response?.data?.detail || "Impossible de créer la mission."); }
  };
  const defer = async (decision) => {
    try { await updateStrategicDecision(decision.id, { status: "deferred" }); await load(); toast("Décision reportée. Elle reste dans le journal."); }
    catch { toast.error("Impossible de reporter cette décision."); }
  };

  return <section className="space-y-4" data-testid="strategic-decisions">
    <div className="glass p-5"><span className="text-[10px] font-bold tracking-[.16em] text-[#F1E2CC]">DÉCISIONS & VALIDATION</span><h2 className="mt-2 font-head text-2xl font-semibold text-white">Une décision doit être expliquée, choisie puis traçable.</h2><p className="mt-1 max-w-3xl text-sm text-white/65">Valider crée une mission dans Mon Mouvement. Reporter conserve la décision dans votre journal, sans effacer le raisonnement.</p></div>
    <form onSubmit={create} className="glass grid gap-3 p-4 md:grid-cols-2"><input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Décision à arbitrer" className="rounded-xl border border-white/25 bg-white/[0.08] px-3 py-2.5 text-sm text-white outline-none placeholder:text-white/45 focus:border-[#F1E2CC]" /><select value={form.milestone_id} onChange={(e) => setForm({ ...form, milestone_id: e.target.value })} className="rounded-xl border border-white/25 bg-[#172C5C] px-3 py-2.5 text-sm text-white outline-none focus:border-[#F1E2CC]"><option value="">Jalon lié (optionnel)</option>{milestones.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select><textarea value={form.why_now} onChange={(e) => setForm({ ...form, why_now: e.target.value })} placeholder="Pourquoi cette décision maintenant ?" rows={3} className="rounded-xl border border-white/25 bg-white/[0.08] px-3 py-2.5 text-sm text-white outline-none placeholder:text-white/45 focus:border-[#F1E2CC]" /><textarea value={form.impact} onChange={(e) => setForm({ ...form, impact: e.target.value })} placeholder="Quel résultat ou quel coût du report ?" rows={3} className="rounded-xl border border-white/25 bg-white/[0.08] px-3 py-2.5 text-sm text-white outline-none placeholder:text-white/45 focus:border-[#F1E2CC]" /><textarea value={form.detail} onChange={(e) => setForm({ ...form, detail: e.target.value })} placeholder="Contexte de décision (optionnel)" rows={2} className="rounded-xl border border-white/25 bg-white/[0.08] px-3 py-2.5 text-sm text-white outline-none placeholder:text-white/45 focus:border-[#F1E2CC] md:col-span-2" /><button disabled={saving} className="gold-bg inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-[#0B1F3A] md:col-span-2 disabled:opacity-60">{saving ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />} Préparer la décision</button></form>
    <div className="space-y-3">{decisions.map((decision) => <article key={decision.id} className="glass p-4"><div className="flex flex-col justify-between gap-4 md:flex-row"><div className="max-w-3xl"><span className="text-[10px] font-bold tracking-[.13em] text-[#F1E2CC]">{(decision.status || "pending").toUpperCase()}</span><h3 className="mt-1 text-base font-semibold text-white">{decision.title}</h3>{decision.why_now && <p className="mt-2 text-sm text-white/75"><b className="font-semibold text-[#F1E2CC]">Pourquoi maintenant :</b> {decision.why_now}</p>}{decision.impact && <p className="mt-1 text-sm text-white/65"><b className="font-semibold text-white/85">Impact :</b> {decision.impact}</p>}{decision.detail && <p className="mt-2 text-sm text-white/55">{decision.detail}</p>}</div>{decision.status === "pending" && <div className="flex shrink-0 flex-wrap items-start gap-2"><button onClick={() => approve(decision)} className="gold-bg inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-bold text-[#0B1F3A]"><CheckCircle2 size={14} /> Créer la mission</button><button onClick={() => defer(decision)} className="rounded-xl border border-white/25 px-3 py-2 text-xs font-semibold text-white/80 hover:bg-white/10">Reporter</button></div>}</div></article>)}{!decisions.length && <div className="glass p-6 text-center"><TrendingUp size={20} className="mx-auto text-[#F1E2CC]" /><p className="mt-3 text-sm text-white/65">Aucune décision stratégique en attente. Créez-en une lorsque l’arbitrage mérite une trace et une mission.</p></div>}</div>
  </section>;
}
