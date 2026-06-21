import React from "react";
import { useNavigate } from "react-router-dom";
import { FileText, Users, Linkedin, Mail, TrendingUp, Check, ArrowRight, Circle } from "lucide-react";
import { DASH } from "@fm/constants/testIds";

/** Pick the most relevant icon from the task label so the UI feels alive. */
function iconFor(label = "") {
  const s = label.toLowerCase();
  if (s.includes("linkedin") || s.includes("post")) return Linkedin;
  if (s.includes("prospect") || s.includes("lead")) return Users;
  if (s.includes("email") || s.includes("relance")) return Mail;
  if (s.includes("financ") || s.includes("revenu") || s.includes("ca")) return TrendingUp;
  return FileText;
}

export default function IAChecklist({ items, missions }) {
  const navigate = useNavigate();
  const list = (items && items.length > 0)
    ? items.slice(0, 5)
    : [
        { label: "Aucune mission IA pour le moment", done: false },
      ];
  const total = missions?.total || items?.length || 0;

  return (
    <div
      className="card-cream p-6 md:p-7 flex flex-col rise"
      style={{ animationDelay: "120ms" }}
      data-testid="ia-checklist"
    >
      <p className="uppercase-eyebrow mb-6 !text-navy">
        Ce que l&apos;IA a préparé pour vous
      </p>
      <ul className="space-y-4 flex-1">
        {list.map((it, i) => {
          const Icon = iconFor(it.label);
          return (
            <li key={it.id || i} className="flex items-center gap-3">
              <span className="w-9 h-9 rounded-full bg-cream-soft grid place-items-center text-navy/80">
                <Icon size={14} strokeWidth={1.9} />
              </span>
              <span className="text-[14px] text-ink flex-1">{it.label}</span>
              {it.done ? (
                <span className="w-5 h-5 rounded-full grid place-items-center bg-navy text-cream">
                  <Check size={12} strokeWidth={3} />
                </span>
              ) : (
                <span className="w-5 h-5 rounded-full grid place-items-center bg-sand-200 text-ink-muted">
                  <Circle size={10} strokeWidth={2} />
                </span>
              )}
            </li>
          );
        })}
      </ul>
      <button
        data-testid={DASH.iaChecklistViewAll}
        onClick={() => navigate("/espace?tab=missions")}
        className="mt-6 inline-flex items-center gap-1.5 text-[13px] font-semibold text-navy hover:gap-2.5 transition-all self-start"
      >
        Voir tout {total ? `(${total})` : ""}
        <ArrowRight size={14} strokeWidth={2.2} />
      </button>
    </div>
  );
}
