import React from "react";
import { Search, Eye, Send, Calendar } from "lucide-react";

const PIPE_STAGES = [
  { id: "sourcing",  label: "Sourcing",       color: "from-blue-100 to-blue-50",    icon: Search,   desc: "Détecté par l'IA" },
  { id: "qualified", label: "Qualifié",        color: "from-amber-100 to-amber-50",  icon: Eye,      desc: "Score > 60" },
  { id: "messaged",  label: "Message envoyé",  color: "from-purple-100 to-purple-50",icon: Send,     desc: "En attente de réponse" },
  { id: "rdv",       label: "RDV",             color: "from-emerald-100 to-emerald-50", icon: Calendar, desc: "Conversation chaude" },
];

export default function PipelineView({ leads }) {
  const stagedLeads = PIPE_STAGES.reduce((acc, s) => ({ ...acc, [s.id]: [] }), {});
  for (const l of leads || []) {
    const status = l.status?.toLowerCase();
    if (status === "rdv" || status === "meeting") stagedLeads.rdv.push(l);
    else if (status === "messaged" || status === "contacted") stagedLeads.messaged.push(l);
    else if ((l.score || 0) >= 60) stagedLeads.qualified.push(l);
    else stagedLeads.sourcing.push(l);
  }

  const total = leads?.length || 0;
  const rdvCount = stagedLeads.rdv.length;
  const conversionRate = total ? Math.round((rdvCount / total) * 100) : 0;

  return (
    <div data-testid="pipeline-view">
      <div className="card-cream p-6 mb-5 rise">
        <p className="uppercase-eyebrow">AI Pipeline</p>
        <h2 className="font-display text-[26px] text-navy mt-1">
          {total} prospects · {rdvCount} en RDV · {conversionRate}% conversion
        </h2>
        <p className="text-[13px] text-ink-soft mt-1">
          Chaque carte avance automatiquement selon les signaux : score, réponse, agenda.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4" data-testid="pipeline-grid">
        {PIPE_STAGES.map((stage, i) => {
          const items = stagedLeads[stage.id];
          const Icon = stage.icon;
          return (
            <div key={stage.id} className="rounded-3xl border border-sand-200 overflow-hidden bg-white shadow-soft rise"
              style={{ animationDelay: `${i * 90}ms` }} data-testid={`pipeline-col-${stage.id}`}>
              <div className={`p-4 bg-gradient-to-br ${stage.color} border-b border-sand-200`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="w-7 h-7 grid place-items-center rounded-full bg-navy text-cream">
                    <Icon size={13} />
                  </span>
                  <h3 className="font-semibold text-navy text-[14px]">{stage.label}</h3>
                  <span className="ml-auto text-[12px] text-navy font-semibold tabular-nums">{items.length}</span>
                </div>
                <p className="text-[11.5px] text-ink-soft">{stage.desc}</p>
              </div>
              <div className="p-3 space-y-2 max-h-[480px] overflow-y-auto min-h-[200px]">
                {items.length === 0 ? (
                  <p className="text-[12px] text-ink-muted text-center py-6 italic">Aucun prospect à ce stade.</p>
                ) : items.map((l) => (
                  <div key={l.id || l.name} className="rounded-xl border border-sand-200 bg-cream-soft p-3 hover:border-navy/30"
                    data-testid={`pipeline-lead-${l.id || l.name}`}>
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-[13px] font-medium text-navy truncate">{l.name}</p>
                      <span className="text-[10.5px] text-gold-deep font-semibold">{l.score || 0}</span>
                    </div>
                    <p className="text-[11px] text-ink-soft truncate">{l.co || ""} · {l.from || ""}</p>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
