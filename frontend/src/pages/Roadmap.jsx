import React, { useEffect, useState } from "react";
import { Map, Sparkles, Loader2, Target, FlaskConical, BarChart3 } from "lucide-react";
import api from "@/lib/api";

export default function Roadmap() {
  const [form, setForm] = useState({ project_description: "", target_market: "", main_hypothesis: "" });
  const [loading, setLoading] = useState(false);
  const [sprints, setSprints] = useState([]);
  const [active, setActive] = useState(null);

  useEffect(() => { load(); }, []);
  const load = async () => {
    try {
      const r = await api.get("/roadmap/sprints");
      const data = Array.isArray(r.data) ? r.data : (r.data?.items || []);
      setSprints(data);
      if (data.length > 0 && !active) setActive(data[0]);
    } catch {
      setSprints([]);
    }
  };

  const generate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await api.post("/roadmap/generate", form);
      setActive(r.data);
      load();
    } finally { setLoading(false); }
  };

  return (
    <div className="space-y-6" data-testid="roadmap-page">
      <header>
        <div className="chip mb-3"><Map size={14} /> Roadmap 30/60/90</div>
        <h1 className="font-display text-3xl md:text-4xl">Construire, mesurer, apprendre.</h1>
        <p className="text-[var(--zayado-muted)] mt-2 max-w-2xl">
          Pas de plan à 3 ans. Trois sprints de 30 jours pour tester les hypothèses
          les plus risquées en premier.
        </p>
      </header>

      <div className="grid md:grid-cols-3 gap-5">
        <form onSubmit={generate} className="card-soft p-5 space-y-3" data-testid="roadmap-form">
          <h3 className="font-display text-lg">Générer une roadmap</h3>
          <textarea rows={2} className="w-full px-4 py-3 rounded-2xl border border-[var(--zayado-border)] resize-none" placeholder="Projet"
            required value={form.project_description}
            onChange={(e) => setForm({ ...form, project_description: e.target.value })}
            data-testid="roadmap-project" />
          <textarea rows={2} className="w-full px-4 py-3 rounded-2xl border border-[var(--zayado-border)] resize-none" placeholder="Marché cible"
            required value={form.target_market}
            onChange={(e) => setForm({ ...form, target_market: e.target.value })}
            data-testid="roadmap-market" />
          <textarea rows={2} className="w-full px-4 py-3 rounded-2xl border border-[var(--zayado-border)] resize-none" placeholder="Hypothèse principale à tester"
            required value={form.main_hypothesis}
            onChange={(e) => setForm({ ...form, main_hypothesis: e.target.value })}
            data-testid="roadmap-hypothesis" />
          <button disabled={loading} className="btn-navy btn-press w-full inline-flex items-center justify-center gap-2" data-testid="roadmap-generate-btn">
            {loading ? <Loader2 className="animate-spin" size={16} /> : <Sparkles size={16} />}
            {loading ? "Génération…" : "Générer"}
          </button>
        </form>

        <div className="md:col-span-2 space-y-3">
          {sprints.length > 1 && (
            <div className="flex gap-2 flex-wrap">
              {sprints.map((s) => (
                <button
                  key={s.sprint_id}
                  onClick={() => setActive(s)}
                  className={`chip ${active?.sprint_id === s.sprint_id ? "!bg-[var(--zayado-navy)] !text-[var(--zayado-cream)]" : ""}`}
                  data-testid={`sprint-${s.sprint_id}`}
                >
                  {s.project.slice(0, 30)}…
                </button>
              ))}
            </div>
          )}
          {active ? (
            <div className="space-y-4">
              {active.data?.sprints?.map((sp, i) => (
                <div key={i} className="card-soft p-5 animate-fade-up" style={{ animationDelay: `${i * 80}ms` }} data-testid={`sprint-card-${i}`}>
                  <div className="flex items-baseline justify-between mb-3">
                    <h3 className="font-display text-xl">{sp.phase}</h3>
                    <span className="chip"><Target size={12} /> Sprint {i + 1}</span>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <div className="text-xs uppercase tracking-wider text-[var(--zayado-muted)] mb-1">Hypothèse</div>
                      <div className="italic">{sp.hypothesis}</div>
                    </div>
                    <div>
                      <div className="text-xs uppercase tracking-wider text-[var(--zayado-muted)] mb-1 flex items-center gap-1"><FlaskConical size={12} /> Expériences (Build)</div>
                      <ul className="space-y-1">
                        {sp.experiments?.map((x, j) => <li key={j} className="flex gap-2 text-sm"><span className="text-[var(--zayado-navy)]">•</span>{x}</li>)}
                      </ul>
                    </div>
                    <div>
                      <div className="text-xs uppercase tracking-wider text-[var(--zayado-muted)] mb-1 flex items-center gap-1"><BarChart3 size={12} /> Métriques (Measure)</div>
                      <div className="flex flex-wrap gap-2">
                        {sp.metrics?.map((m, j) => <span key={j} className="chip">{m}</span>)}
                      </div>
                    </div>
                    <div className="border-t border-[var(--zayado-border)] pt-3">
                      <div className="text-xs uppercase tracking-wider text-[var(--zayado-muted)] mb-1">Décision (Learn)</div>
                      <div className="text-sm">{sp.decision_criteria}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="card-soft p-8 text-center text-[var(--zayado-muted)]">
              Aucune roadmap encore. Remplissez le formulaire pour générer la vôtre.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
