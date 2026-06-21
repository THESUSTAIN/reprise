import React, { useEffect, useState } from "react";
import { tasksApi } from "@fm/lib/api";
import { CheckCircle2, Circle, Clock, User, Bot, Plus, Calendar, Flame, Trash2, Loader2, Target } from "lucide-react";

/**
 * Inner Missions content used inside Espace de travail tab.
 * Does NOT render TopNav / FloatingBottomBar / MobileBottomNav — the parent
 * EspaceDeTravail page already handles layout chrome.
 */
const PRIORITY_KEY = () => `zay_priorite_jour_${new Date().toISOString().slice(0, 10)}`;

export default function Missions({ onOpenCollab }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [newLabel, setNewLabel] = useState("");

  // ── Priorité unique du jour (disposition reprise de l'ancien Cockpit) ──
  const [priority, setPriority] = useState(() => {
    try { return localStorage.getItem(PRIORITY_KEY()) || ""; } catch { return ""; }
  });
  const [progress, setProgress] = useState(() => {
    try { return Number(localStorage.getItem(PRIORITY_KEY() + "_pct") || 0); } catch { return 0; }
  });
  const savePriority = () => {
    try {
      localStorage.setItem(PRIORITY_KEY(), priority);
      localStorage.setItem(PRIORITY_KEY() + "_pct", String(progress));
    } catch {}
  };

  useEffect(() => {
    tasksApi.list()
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const toggle = async (id) => {
    const t = items.find((x) => x.id === id);
    if (!t) return;
    setItems((arr) => arr.map((x) => (x.id === id ? { ...x, done: !x.done } : x)));
    try { await tasksApi.patch(id, { done: !t.done }); } catch { /* ignore */ }
  };
  const remove = async (id) => {
    setItems((arr) => arr.filter((x) => x.id !== id));
    try { await tasksApi.remove(id); } catch { /* ignore */ }
  };
  const create = async (source = "humain") => {
    if (!newLabel.trim()) return;
    setAdding(true);
    try {
      const t = await tasksApi.create({ label: newLabel.trim(), source });
      setItems((arr) => [...arr, t]);
      setNewLabel("");
    } catch { /* ignore */ } finally { setAdding(false); }
  };

  const done = items.filter((x) => x.done).length;
  const total = items.length;
  const iaItems = items.filter((x) => x.source === "ia");
  const humanItems = items.filter((x) => x.source === "humain");

  return (
    <div data-testid="missions-content">
      <div className="mb-5 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-[#6B6358] font-semibold">Plan du jour</p>
          <p className="mt-2 text-[14.5px] text-[#4A4538]">Ce qui fera avancer concrètement votre business aujourd&apos;hui.</p>
        </div>
        <div className="bg-white border border-[#E8E2D8] rounded-2xl px-5 py-4 shadow-sm">
          <p className="text-[10.5px] tracking-[0.22em] uppercase text-[#6B6358] font-semibold">Progression</p>
          <p className="text-[28px] leading-tight text-[#1F2937] font-display">
            {done} <span className="text-[14px] text-[#6B6358]">/ {total || "—"}</span>
          </p>
          <div className="mt-1.5 h-1.5 w-44 rounded-full bg-[#F3E9D0] overflow-hidden">
            <div className="h-full bg-[#264653] transition-all"
              style={{ width: total ? `${(done / total) * 100}%` : "0%" }} />
          </div>
        </div>
      </div>

      {/* ── Priorité unique du jour ─────────────────────────────────────────── */}
      <section className="mb-5 card-cream p-6 md:p-7" data-testid="priority-section">
        <p className="text-[10.5px] tracking-[0.22em] uppercase text-[#9C7D40] font-semibold mb-2 inline-flex items-center gap-2">
          <Target size={13} /> Priorité unique du jour
        </p>
        <input
          type="text"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          onBlur={savePriority}
          placeholder="Ex : Finaliser la proposition Acme et l'envoyer."
          data-testid="priority-input"
          className="w-full bg-transparent font-display text-[22px] md:text-[26px] italic text-[#1F2937] placeholder:text-[#9CA3AF] focus:outline-none border-b border-[#E8E2D8] focus:border-[#264653] pb-3 transition"
        />
        <div className="mt-4">
          <div className="flex justify-between text-[11.5px] text-[#6B6358] mb-1.5">
            <span>Progression</span>
            <span className="font-semibold text-[#264653]">{progress}%</span>
          </div>
          <input
            type="range" min="0" max="100" value={progress}
            onChange={(e) => setProgress(Number(e.target.value))}
            onMouseUp={savePriority}
            onTouchEnd={savePriority}
            data-testid="priority-range"
            className="w-full accent-[#264653]"
          />
        </div>
      </section>

      {/* ── Ajouter une mission (haut de page) ─────────────────────────────── */}
      <div className="mb-5 card-cream p-5" data-testid="missions-add">
        <div className="flex items-center gap-3 mb-3">
          <span className="w-10 h-10 rounded-2xl bg-[#264653] text-white grid place-items-center shrink-0">
            <Plus size={17} strokeWidth={2} />
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-[15.5px] text-[#1F2937] font-display">Ajouter une mission</p>
            <p className="text-[12.5px] text-[#6B6358]">Tapez votre tâche, ou demandez à l&apos;IA d&apos;en suggérer une.</p>
          </div>
        </div>
        <div className="flex flex-col md:flex-row gap-2">
          <input
            data-testid="task-new-input"
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && create("humain")}
            placeholder="Ex : Préparer le pitch deck v3"
            className="flex-1 bg-white border border-[#E8E2D8] rounded-2xl px-4 py-3 text-[#1F2937] focus:outline-none focus:border-[#264653]/40 placeholder:text-[#9CA3AF]"
          />
          <button onClick={() => create("humain")} disabled={!newLabel.trim() || adding}
            data-testid="task-add-btn"
            className="px-5 h-12 rounded-full bg-[#264653] text-white text-[13.5px] font-semibold hover:bg-[#1D3557] transition-colors disabled:opacity-50">
            {adding ? <Loader2 size={14} className="animate-spin inline" /> : "Ajouter"}
          </button>
          {onOpenCollab && (
            <button onClick={onOpenCollab}
              data-testid="task-suggest-ai"
              className="px-4 h-12 rounded-full bg-[#FBF6EA] hover:bg-[#F3E9D0] text-[#1F2937] text-[13.5px] font-semibold transition-colors inline-flex items-center justify-center gap-2">
              <Flame size={14} /> Suggérer via l&apos;IA
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="card-cream p-12 grid place-items-center text-[#6B6358]">
          <Loader2 className="animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <TasksColumn eyebrow="IA" icon={Bot} title="Préparé par votre IA" subtitle="Ces missions ont été générées et déclenchées automatiquement."
            items={iaItems} onToggle={toggle} onRemove={remove} testid="missions-ia" />
          <TasksColumn eyebrow="HUMAIN" icon={User} title="Action humaine" subtitle="Ce qui ne peut être délégué : présence, voix, décisions."
            items={humanItems} onToggle={toggle} onRemove={remove} testid="missions-human" />
        </div>
      )}
    </div>
  );
}

function TasksColumn({ eyebrow, icon: Icon, title, subtitle, items, onToggle, onRemove, testid }) {
  const remaining = items.filter((x) => !x.done).length;
  return (
    <div className="card-cream p-7" data-testid={testid}>
      <div className="flex items-start gap-3 mb-5">
        <span className="w-11 h-11 rounded-2xl bg-[#264653] text-white grid place-items-center shrink-0">
          <Icon size={18} strokeWidth={1.8} />
        </span>
        <div className="flex-1">
          <p className="text-[10.5px] tracking-[0.22em] uppercase text-[#9C7D40] font-semibold">{eyebrow}</p>
          <p className="text-[20px] text-[#1F2937] leading-tight font-display">{title}</p>
          <p className="text-[13px] text-[#6B6358] mt-1">{subtitle}</p>
        </div>
        <span className="text-[12px] font-semibold text-[#1F2937] bg-[#FBF6EA] px-2.5 py-1 rounded-full whitespace-nowrap">
          {remaining} à faire
        </span>
      </div>

      {items.length === 0 ? (
        <p className="text-[13px] text-[#6B6358] italic">Aucune mission dans cette catégorie pour l&apos;instant.</p>
      ) : (
        <ul className="space-y-2">
          {items.map((it) => (
            <li key={it.id} data-testid={`task-${it.id}`}
              className={`group flex items-center gap-3 p-3 rounded-2xl border transition-all ${
                it.done ? "bg-[#FBF6EA] border-[#E8E2D8] opacity-70" : "bg-white border-[#E8E2D8] hover:border-[#264653]/30"
              }`}>
              <button onClick={() => onToggle(it.id)} aria-label="toggle" data-testid={`task-toggle-${it.id}`} className="shrink-0">
                {it.done ? <CheckCircle2 size={20} className="text-[#264653]" /> : <Circle size={20} className="text-[#9CA3AF] hover:text-[#264653] transition-colors" />}
              </button>
              <div className="flex-1 min-w-0">
                <p className={`text-[14px] ${it.done ? "line-through text-[#9CA3AF]" : "text-[#1F2937]"}`}>{it.label}</p>
                <div className="flex items-center gap-2 mt-0.5 text-[11.5px] text-[#6B6358]">
                  {it.time && <><Calendar size={11} /> {it.time}<span>·</span></>}
                  <Clock size={11} /> {it.duration_min || 25} min
                </div>
              </div>
              <button onClick={() => onRemove(it.id)} aria-label="delete"
                className="opacity-0 group-hover:opacity-100 transition-opacity text-[#9CA3AF] hover:text-rose-600">
                <Trash2 size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
