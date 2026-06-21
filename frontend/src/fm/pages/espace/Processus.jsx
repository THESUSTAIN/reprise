import React, { useEffect, useState } from "react";
import { Plus, Check, Trash2, X, Loader2, ChevronRight, Sparkles, FolderOpen } from "lucide-react";
import { processesApi } from "@fm/lib/api";
import { toast } from "sonner";

const CATEGORY_ICONS = {
  Commercial: "🤝", Marketing: "📣", Finance: "💼", RH: "👥", Général: "📋",
};

export default function Processus() {
  const [templates, setTemplates] = useState([]);
  const [items, setItems] = useState(null);
  const [creating, setCreating] = useState(false);
  const [opened, setOpened] = useState(null);

  const load = async () => {
    try {
      const [tpls, list] = await Promise.all([processesApi.templates(), processesApi.list()]);
      setTemplates(tpls.templates || []);
      setItems(list.items || []);
    } catch {
      setItems([]);
    }
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(); }, []);

  const create = async (templateId, name) => {
    try {
      const tpl = templates.find((t) => t.id === templateId);
      const r = await processesApi.create({ name, template_id: templateId, category: tpl?.category || "Général" });
      setItems((arr) => [r, ...(arr || [])]);
      setCreating(false);
      setOpened(r);
      toast.success("Processus créé");
    } catch {
      toast.error("Création impossible");
    }
  };

  const toggleStep = async (proc, idx) => {
    const newSteps = proc.steps.map((s, i) => i === idx ? { ...s, done: !s.done } : s);
    setOpened({ ...proc, steps: newSteps });
    setItems((arr) => arr.map((p) => p.id === proc.id ? { ...p, steps: newSteps } : p));
    try {
      await processesApi.patch(proc.id, { steps: newSteps });
    } catch {
      toast.error("Sauvegarde impossible");
    }
  };

  const editStepLabel = async (proc, idx, newLabel) => {
    const newSteps = proc.steps.map((s, i) => i === idx ? { ...s, label: newLabel } : s);
    setOpened({ ...proc, steps: newSteps });
    setItems((arr) => arr.map((p) => p.id === proc.id ? { ...p, steps: newSteps } : p));
    await processesApi.patch(proc.id, { steps: newSteps });
  };

  const addStep = async (proc) => {
    const newSteps = [...(proc.steps || []), { label: `Étape ${(proc.steps?.length || 0) + 1}`, done: false, owner: "humain" }];
    setOpened({ ...proc, steps: newSteps });
    setItems((arr) => arr.map((p) => p.id === proc.id ? { ...p, steps: newSteps } : p));
    await processesApi.patch(proc.id, { steps: newSteps });
  };

  const remove = async (id) => {
    if (!window.confirm("Supprimer ce processus ?")) return;
    await processesApi.remove(id);
    setItems((arr) => arr.filter((p) => p.id !== id));
    if (opened?.id === id) setOpened(null);
  };

  // Compute stats for header
  const procTotal = items?.length || 0;
  const procDone = (items || []).filter((p) => {
    const total = (p.steps || []).length;
    const done = (p.steps || []).filter((s) => s.done).length;
    return total > 0 && done === total;
  }).length;

  return (
    <div className="space-y-5" data-testid="processes-content">
      {/* Header — aligné Missions */}
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-[#6B6358] font-semibold">Matrices opérationnelles</p>
          
          <p className="mt-1 text-[14.5px] text-[#4A4538]">Industrialisez les tâches répétitives. Choisissez un modèle, suivez l&apos;avancement.</p>
        </div>
        <div className="bg-white border border-[#E8E2D8] rounded-2xl px-5 py-4 shadow-sm">
          <p className="text-[10.5px] tracking-[0.22em] uppercase text-[#6B6358] font-semibold">Processus</p>
          <p className="text-[28px] leading-tight text-[#1F2937] font-display">
            {procDone} <span className="text-[14px] text-[#6B6358]">/ {procTotal || "—"} terminés</span>
          </p>
          <div className="mt-1.5 h-1.5 w-44 rounded-full bg-[#F3E9D0] overflow-hidden">
            <div className="h-full bg-[#264653] transition-all"
              style={{ width: procTotal ? `${(procDone / procTotal) * 100}%` : "0%" }} />
          </div>
        </div>
      </div>

      {/* Ajout / Nouveau processus (en haut, aligné Missions) */}
      <div className="card-cream p-5" data-testid="process-add-block">
        <div className="flex items-center gap-3 mb-3">
          <span className="w-10 h-10 rounded-2xl bg-[#264653] text-white grid place-items-center shrink-0">
            <Plus size={17} strokeWidth={2} />
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-[15.5px] text-[#1F2937] font-display">Lancer un processus</p>
            <p className="text-[12.5px] text-[#6B6358]">Démarrez à partir d&apos;un modèle clé en main ou créez le vôtre.</p>
          </div>
          <button
            onClick={() => setCreating(true)}
            data-testid="process-create-btn"
            className="px-4 h-11 rounded-full bg-navy text-cream text-[13.5px] font-semibold hover:bg-navy-bright transition inline-flex items-center justify-center gap-2 shrink-0"
          >
            <Plus size={14} /> Nouveau processus
          </button>
        </div>
        {/* Templates inline */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {templates.slice(0, 6).map((t) => (
            <button
              key={t.id}
              onClick={() => create(t.id, t.name)}
              className="bg-white border border-[#E8E2D8] rounded-xl p-2.5 text-left hover:border-[#264653]/30 transition flex items-center gap-2"
              data-testid={`tpl-process-${t.id}`}
            >
              <span className="text-base shrink-0">{CATEGORY_ICONS[t.category] || "📋"}</span>
              <span className="text-[12.5px] text-[#1F2937] truncate">{t.name}</span>
              <span className="ml-auto text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded-full bg-[#F3E9D0] text-[#9C7D40] shrink-0">{t.steps}</span>
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      {items === null ? (
        <div className="card-soft p-12 grid place-items-center text-[#6B6358]"><Loader2 className="animate-spin" /></div>
      ) : items.length === 0 ? (
        <div className="card-soft p-10 text-center" data-testid="process-empty">
          <FolderOpen size={28} className="mx-auto text-[#9C7D40] mb-3" />
          <p className="text-[15px] text-[#1F2937] font-medium">Aucun processus actif</p>
          <p className="text-[12.5px] text-[#6B6358] mt-1">Cliquez sur un template ci-dessus pour démarrer.</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="process-list">
          {items.map((p) => {
            const done = (p.steps || []).filter((s) => s.done).length;
            const total = (p.steps || []).length;
            const pct = total ? Math.round((done / total) * 100) : 0;
            return (
              <div key={p.id} className="card-soft p-5 cursor-pointer hover:border-navy/30 transition" onClick={() => setOpened(p)} data-testid={`process-${p.id}`}>
                <div className="flex items-start justify-between mb-3">
                  <span className="text-2xl leading-none">{CATEGORY_ICONS[p.category] || "📋"}</span>
                  <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#F3E9D0] text-[#9C7D40]">{p.category}</span>
                </div>
                <p className="font-display text-[17px] text-[#1F2937] leading-tight mb-2">{p.name}</p>
                <div className="flex items-center justify-between text-[12px] text-[#6B6358] mb-1.5">
                  <span>{done}/{total} étapes</span>
                  <span className="font-semibold text-navy">{pct}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-[#F3E9D0] overflow-hidden">
                  <div className="h-full bg-navy transition-all" style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create modal */}
      {creating && (
        <CreateModal templates={templates} onClose={() => setCreating(false)} onCreate={create} />
      )}

      {/* Open modal */}
      {opened && (
        <OpenedModal
          proc={opened}
          onClose={() => setOpened(null)}
          onToggle={(i) => toggleStep(opened, i)}
          onEdit={(i, val) => editStepLabel(opened, i, val)}
          onAddStep={() => addStep(opened)}
          onDelete={() => remove(opened.id)}
        />
      )}
    </div>
  );
}

function CreateModal({ templates, onClose, onCreate }) {
  const [picked, setPicked] = useState(null);
  const [name, setName] = useState("");
  return (
    <div className="fixed inset-0 z-50 bg-navy/40 backdrop-blur-sm grid place-items-center p-4" onClick={onClose}>
      <div className="bg-cream rounded-3xl p-6 max-w-lg w-full border border-sand-200 shadow-soft" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2"><Sparkles className="text-gold-deep" size={18} /><p className="font-display text-[20px] text-navy">Nouveau processus</p></div>
          <button onClick={onClose} className="text-ink-soft"><X size={18} /></button>
        </div>
        <p className="text-[12.5px] text-ink-soft mb-4">Choisissez un modèle, donnez-lui votre nom.</p>
        <div className="grid grid-cols-2 gap-2 mb-4 max-h-64 overflow-y-auto">
          {templates.map((t) => (
            <button key={t.id} onClick={() => { setPicked(t); if (!name) setName(t.name); }} data-testid={`pick-${t.id}`}
              className={`p-3 rounded-xl border-2 text-left transition ${picked?.id === t.id ? "border-navy bg-blue-50" : "border-sand-200 bg-white hover:border-navy/30"}`}>
              <div className="text-xl mb-1">{CATEGORY_ICONS[t.category] || "📋"}</div>
              <div className="text-[12.5px] text-ink font-medium">{t.name}</div>
              <div className="text-[10.5px] text-ink-soft mt-0.5">{t.steps} étapes</div>
            </button>
          ))}
        </div>
        {picked && (
          <input autoFocus value={name} onChange={(e) => setName(e.target.value)} data-testid="new-process-name"
            placeholder="Nom personnalisé" className="w-full bg-white border border-sand-200 rounded-lg px-3 py-2.5 text-[14px] outline-none focus:border-navy/40 mb-3" />
        )}
        <div className="flex gap-2">
          <button onClick={onClose} className="flex-1 py-2.5 bg-cream-soft text-ink text-sm rounded-xl">Annuler</button>
          <button onClick={() => picked && onCreate(picked.id, name.trim() || picked.name)} disabled={!picked || !name.trim()}
            data-testid="confirm-create-process"
            className="flex-1 py-2.5 bg-navy text-cream text-sm font-semibold rounded-xl disabled:opacity-40">
            Créer
          </button>
        </div>
      </div>
    </div>
  );
}

function OpenedModal({ proc, onClose, onToggle, onEdit, onAddStep, onDelete }) {
  return (
    <div className="fixed inset-0 z-50 bg-navy/40 backdrop-blur-sm grid place-items-center p-4">
      <div className="bg-cream rounded-3xl max-w-2xl w-full max-h-[85vh] flex flex-col border border-sand-200 shadow-soft">
        <div className="p-5 border-b border-sand-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{CATEGORY_ICONS[proc.category] || "📋"}</span>
            <div>
              <p className="text-[10.5px] uppercase tracking-wider text-gold-deep font-semibold">{proc.category}</p>
              <p className="font-display text-[22px] text-navy">{proc.name}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-ink-soft"><X size={18} /></button>
        </div>
        <div className="p-6 overflow-y-auto flex-1 space-y-2" data-testid="process-steps">
          {proc.steps.map((s, i) => (
            <div key={i} className={`flex items-center gap-3 p-3 rounded-2xl border transition ${s.done ? "bg-cream-soft border-sand-200 opacity-70" : "bg-white border-sand-200 hover:border-navy/30"}`}>
              <button onClick={() => onToggle(i)} aria-label="toggle" className="shrink-0" data-testid={`step-toggle-${i}`}>
                {s.done ? <div className="w-6 h-6 rounded-full bg-navy text-cream grid place-items-center"><Check size={13} /></div> : <div className="w-6 h-6 rounded-full border-2 border-sand-300" />}
              </button>
              <input value={s.label} onChange={(e) => onEdit(i, e.target.value)} className={`flex-1 bg-transparent text-[14px] outline-none ${s.done ? "line-through text-ink-muted" : "text-ink"}`} />
              <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-cream-soft text-ink-soft">{s.owner || "humain"}</span>
            </div>
          ))}
          <button onClick={onAddStep} data-testid="add-step" className="w-full mt-2 inline-flex items-center justify-center gap-1 h-10 rounded-2xl border-2 border-dashed border-sand-300 text-ink-soft hover:border-navy/40 hover:text-navy">
            <Plus size={14} /> Ajouter une étape
          </button>
        </div>
        <div className="p-4 border-t border-sand-200 flex justify-between">
          <button onClick={onDelete} className="text-[12px] text-rose-600 inline-flex items-center gap-1 hover:underline" data-testid="delete-process">
            <Trash2 size={12} /> Supprimer le processus
          </button>
          <button onClick={onClose} className="px-4 h-9 rounded-full bg-cream-soft text-ink text-[12.5px]">Fermer</button>
        </div>
      </div>
    </div>
  );
}
