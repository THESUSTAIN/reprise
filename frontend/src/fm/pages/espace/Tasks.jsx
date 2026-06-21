import React from "react";
import { CheckSquare, Plus, Clock } from "lucide-react";
import { useApp } from "@fm/context/AppContext";

export default function Tasks() {
  const { cockpit } = useApp();
  const items = cockpit?.livrables || [];
  return (
    <div className="p-6 lg:p-10 max-w-[1100px] mx-auto" data-testid="tasks-page">
      <div className="flex items-end justify-between mb-8">
        <div>
          <div className="text-xs text-inkMuted">Tâches</div>
          <h1 className="text-3xl tracking-tight text-ink">Tes prochaines décisions justes.</h1>
        </div>
        <button className="inline-flex items-center gap-2 bg-aubergine text-cream px-4 py-2 rounded-full text-sm hover:bg-aubergine-deep transition">
          <Plus className="w-4 h-4" /> Nouvelle tâche
        </button>
      </div>

      <div className="space-y-3">
        {items.map((t, i) => (
          <div key={i} className="bg-white border border-outline rounded-2xl p-5 flex items-center gap-4 hover:border-aubergine/30 transition">
            <div className="w-10 h-10 rounded-xl bg-aubergine/8 flex items-center justify-center text-aubergine">
              <CheckSquare className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-blush text-aubergine">{t.type}</span>
                <span className="text-[10px] text-inkMuted inline-flex items-center gap-1"><Clock className="w-3 h-3" /> 20 min</span>
              </div>
              <div className="text-ink text-[15px]">{t.title}</div>
            </div>
            <button className="text-xs text-aubergine hover:underline">Démarrer</button>
          </div>
        ))}
      </div>
    </div>
  );
}
