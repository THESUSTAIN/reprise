import React, { useState } from "react";
import { X } from "lucide-react";
import { LEAD_STATUSES } from "./TerrainView";

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="text-[11.5px] uppercase tracking-wider text-ink-soft font-semibold block mb-1.5">{label}</span>
      {children}
    </label>
  );
}

export default function AddLeadModal({ onClose, onAdd }) {
  const [form, setForm] = useState({ name: "", co: "", status: "Détecté", score: 50, from: "Manuel" });
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-navy/40 backdrop-blur-sm fade-in p-4" onClick={onClose}>
      <div className="card-cream p-6 w-full max-w-md rise" onClick={(e) => e.stopPropagation()} data-testid="add-lead-modal">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-[22px] text-navy">Nouveau lead</h3>
          <button onClick={onClose} className="w-8 h-8 grid place-items-center rounded-full hover:bg-sand-200"><X size={16} /></button>
        </div>
        <div className="space-y-3">
          <Field label="Nom *">
            <input data-testid="add-lead-name" autoFocus value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full h-10 px-3 rounded-xl bg-white border border-sand-300 text-[14px] focus:outline-none focus:border-navy/50" />
          </Field>
          <Field label="Société">
            <input data-testid="add-lead-co" value={form.co} onChange={(e) => setForm({ ...form, co: e.target.value })}
              className="w-full h-10 px-3 rounded-xl bg-white border border-sand-300 text-[14px] focus:outline-none focus:border-navy/50" />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Statut">
              <select data-testid="add-lead-status" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}
                className="w-full h-10 px-3 rounded-xl bg-white border border-sand-300 text-[14px] focus:outline-none focus:border-navy/50">
                {LEAD_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Score">
              <input data-testid="add-lead-score" type="number" min={0} max={100} value={form.score}
                onChange={(e) => setForm({ ...form, score: parseInt(e.target.value) || 0 })}
                className="w-full h-10 px-3 rounded-xl bg-white border border-sand-300 text-[14px] focus:outline-none focus:border-navy/50" />
            </Field>
          </div>
          <Field label="Source">
            <input data-testid="add-lead-from" value={form.from} onChange={(e) => setForm({ ...form, from: e.target.value })}
              placeholder="LinkedIn, Reddit, Recommandation…"
              className="w-full h-10 px-3 rounded-xl bg-white border border-sand-300 text-[14px] focus:outline-none focus:border-navy/50" />
          </Field>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="px-4 h-10 rounded-full bg-cream-soft text-ink hover:bg-sand-200 text-[13px] font-medium">Annuler</button>
          <button data-testid="add-lead-submit" onClick={() => form.name.trim() && onAdd(form)} disabled={!form.name.trim()}
            className="px-5 h-10 rounded-full bg-navy text-cream text-[13px] font-semibold hover:bg-navy-bright transition-colors disabled:opacity-50">
            Ajouter
          </button>
        </div>
      </div>
    </div>
  );
}
