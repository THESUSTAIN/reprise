import React from "react";
import {
  ArrowRight, Calendar, Lightbulb, AlertTriangle, TrendingUp, Sparkles, Quote,
  Bot, CheckCircle2, Clock,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const GOLD = "#DEC2A3";
const SAGE = "#8fa876";
const CORAL = "#d98a6a";
const BLUE = "#4f6fb0";

function SectionHead({ icon: Icon, title, action, onAction }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, marginBottom: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
        {Icon && <Icon size={15} color={GOLD} />}
        <h3 style={{ fontSize: 13.5, fontWeight: 700, color: "var(--txt)", margin: 0, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{title}</h3>
      </div>
      {action && (
        <button type="button" onClick={onAction} data-testid="section-head-action" style={{
          display: "inline-flex", alignItems: "center", gap: 4, background: "transparent",
          border: "none", color: "#93c5fd", fontSize: 11.5, fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap",
        }}>{action} <ArrowRight size={12} /></button>
      )}
    </div>
  );
}

/* ── Prochaine séquence de la journée ─────────────────────── */
export function NextSequence({ data }) {
  const navigate = useNavigate();
  const checklist = Array.isArray(data?.ia_checklist) ? data.ia_checklist : [];
  const items = checklist.slice(0, 4).map((it, i) => ({
    time: it.time || ["09:30", "10:30", "14:00", "16:00"][i] || "",
    title: it.title || it.label || it.text || `Étape ${i + 1}`,
    tag: it.priority || (i % 3 === 0 ? "Priorité haute" : i % 3 === 1 ? "Priorité moyenne" : "Préparation"),
  }));
  if (items.length === 0) return null;
  const tagColor = (t) => t.includes("haute") ? CORAL : t.includes("moyenne") ? GOLD : BLUE;
  return (
    <div className="glass-card" data-testid="cockpit-next-sequence" style={{ padding: 16, marginBottom: 12 }}>
      <SectionHead icon={Calendar} title="Prochaine séquence de la journée" action="Pilotage" onAction={() => navigate("/pilotage")} />
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {items.map((it, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }} data-testid={`sequence-item-${i}`}>
            <span style={{ fontSize: 11.5, fontWeight: 600, color: "var(--txt-muted)", width: 40 }}>{it.time}</span>
            <span style={{ flex: 1, fontSize: 12.5, fontWeight: 600, color: "var(--txt)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{it.title}</span>
            <span style={{
              fontSize: 10, fontWeight: 600, padding: "3px 8px", borderRadius: 999,
              color: tagColor(it.tag), background: `${tagColor(it.tag)}1f`, whiteSpace: "nowrap",
            }}>{it.tag}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Insights clés pour vous (données réelles, état vide honnête) ────── */
const INSIGHT_STYLE = {
  opportunite: { label: "Opportunité", color: SAGE, icon: TrendingUp },
  attention: { label: "Attention", color: CORAL, icon: AlertTriangle },
  idee: { label: "Idée du jour", color: GOLD, icon: Lightbulb },
};

export function KeyInsights({ data }) {
  const navigate = useNavigate();
  const raw = Array.isArray(data?.insights) ? data.insights : [];
  const insights = raw.map((ins) => ({
    ...(INSIGHT_STYLE[ins.kind] || INSIGHT_STYLE.idee),
    label: ins.label || (INSIGHT_STYLE[ins.kind] || INSIGHT_STYLE.idee).label,
    text: ins.text,
    cta: ins.cta || "Voir",
    to: ins.to || "/pilotage",
  }));
  return (
    <div className="glass-card" data-testid="cockpit-key-insights" style={{ padding: 20 }}>
      <SectionHead icon={Lightbulb} title="Insights clés pour vous" action="Pilotage" onAction={() => navigate("/pilotage")} />
      {insights.length === 0 ? (
        <p data-testid="key-insights-empty" style={{ fontSize: 12.5, color: "var(--txt-muted)", margin: 0, lineHeight: 1.5 }}>
          Rien à signaler pour l'instant. Renseignez votre objectif de CA, vos factures et
          votre bien-être pour que le cockpit vous remonte des alertes et opportunités ici.
        </p>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
          {insights.map((ins, i) => {
            const Icon = ins.icon;
            return (
              <div key={i} data-testid={`insight-card-${i}`} style={{
                padding: 14, borderRadius: 14, background: "var(--glass-soft)",
                border: `1px solid ${ins.color}33`, borderLeft: `3px solid ${ins.color}`,
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
                  <Icon size={14} color={ins.color} />
                  <span style={{ fontSize: 12.5, fontWeight: 700, color: ins.color }}>{ins.label}</span>
                </div>
                <p style={{ fontSize: 12.5, color: "var(--txt)", margin: "0 0 10px", lineHeight: 1.5 }}>{ins.text}</p>
                <button type="button" onClick={() => navigate(ins.to)} style={{
                  background: "transparent", border: "none", color: "#93c5fd", fontSize: 12,
                  fontWeight: 600, cursor: "pointer", padding: 0,
                }}>{ins.cta} →</button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ── Ce que l’IA a préparé : missions créées vs missions effectuées ── */
export function NightRecap({ data, onSeeTasks }) {
  const vg = data?.value_generated || {};
  const activity = Array.isArray(data?.activite_recente) ? data.activite_recente : [];
  const normalized = activity.map((a) => ({
    text: a.label || a.title || a.text || a.message || "",
    time: a.time || a.when || a.date || a.created_at || "",
    status: String(a.status || a.state || "").toLowerCase(),
    kind: String(a.kind || a.type || a.category || "").toLowerCase(),
    completed: a.completed === true,
  })).filter((item) => item.text);
  const completedMissions = normalized.filter((item) => item.status === "completed" || item.status === "done" || item.status === "effectue" || item.status === "terminé" || item.status === "termine" || item.completed === true).slice(0, 5);
  let createdMissions = normalized.filter((item) => item.status !== "completed" && item.status !== "done" && item.status !== "effectue" && item.status !== "terminé" && item.status !== "termine" && (item.kind.includes("mission") || item.kind.includes("rituel") || /facture|rituel|priorit|action|relancer|protéger|proteger/i.test(item.text))).slice(0, 5);
  if (createdMissions.length === 0 && Number(vg.missions_created) > 0) createdMissions = [{ text: `${vg.missions_created} mission(s) créée(s) après validation`, time: "", status: "created" }];

  return (
    <div className="glass-card" data-testid="cockpit-night-recap" style={{
      padding: 16, marginBottom: 12, border: "1px solid rgba(93,202,165,0.28)",
      background: "linear-gradient(135deg, rgba(93,202,165,0.10), rgba(30,58,138,0.14))",
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, marginBottom: 12, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
          <Bot size={15} color={SAGE} />
          <h3 style={{ fontSize: 13.5, fontWeight: 700, color: "var(--txt)", margin: 0 }}>Ce que l'IA a fait pour vous</h3>
        </div>
        <span data-testid="night-recap-ratio" style={{
          fontSize: 10, fontWeight: 700, padding: "4px 9px", borderRadius: 999,
          color: SAGE, background: `${SAGE}1f`, whiteSpace: "nowrap",
        }}>Vous gardez la main</span>
      </div>

      <div data-testid="night-recap-value" style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        {[
          { label: "Temps gagné", val: (Number(vg.time_saved_min) || 0) >= 60 ? `${Math.floor((vg.time_saved_min) / 60)}h${String((vg.time_saved_min) % 60).padStart(2, "0")}` : `${Number(vg.time_saved_min) || 0} min` },
          { label: "Missions créées", val: Number(vg.missions_created) || 0 },
          { label: "Réponses IA", val: Number(vg.ai_tasks) || 0 },
        ].map((m, i) => (
          <div key={i} data-testid={`night-value-${i}`} style={{ flex: 1, minWidth: 78, padding: "9px 10px", borderRadius: 12, background: "var(--glass-soft)", border: "1px solid var(--glass-border)" }}>
            <div style={{ fontSize: 16, fontWeight: 800, color: "var(--txt)" }}>{m.val}</div>
            <div style={{ fontSize: 10, color: "var(--txt-muted)" }}>{m.label}</div>
          </div>
        ))}
      </div>

      <p style={{ fontSize: 10.5, fontWeight: 700, color: "var(--txt-muted)", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 8px" }}>Missions créées après validation</p>
      {createdMissions.length === 0 ? (
        <p data-testid="night-recap-empty" style={{ fontSize: 12, color: "var(--txt-muted)", margin: 0, lineHeight: 1.5 }}>
          Aucune mission n’a encore été créée. Approuvez une décision du Copilote pour préparer une prochaine action.
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 9 }}>
          {createdMissions.map((mission, i) => (
            <div key={i} data-testid={`night-mission-created-${i}`} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <Clock size={15} color={BLUE} style={{ flexShrink: 0 }} />
              <span style={{ flex: 1, fontSize: 12.5, color: "var(--txt)", lineHeight: 1.4 }}>{mission.text}</span>
              <span style={{ fontSize: 10.5, color: "var(--txt-muted)", whiteSpace: "nowrap" }}>À faire</span>
              {mission.time && <span style={{ fontSize: 10.5, color: "var(--txt-muted)", whiteSpace: "nowrap" }}>{mission.time}</span>}
            </div>
          ))}
        </div>
      )}
      {completedMissions.length > 0 && <>
        <p style={{ fontSize: 10.5, fontWeight: 700, color: "var(--txt-muted)", textTransform: "uppercase", letterSpacing: "0.06em", margin: "16px 0 8px" }}>Missions effectuées</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 9 }}>
          {completedMissions.map((mission, i) => <div key={i} data-testid={`night-mission-completed-${i}`} style={{ display: "flex", alignItems: "center", gap: 10 }}><CheckCircle2 size={15} color={SAGE} style={{ flexShrink: 0 }} /><span style={{ flex: 1, fontSize: 12.5, color: "var(--txt)", lineHeight: 1.4 }}>{mission.text}</span>{mission.time && <span style={{ fontSize: 10.5, color: "var(--txt-muted)", whiteSpace: "nowrap" }}>{mission.time}</span>}</div>)}
        </div>
      </>}

      <button type="button" onClick={onSeeTasks} data-testid="night-recap-see-tasks" style={{
        marginTop: 12, width: "100%", display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 6,
        height: 34, borderRadius: 12, border: "1px solid rgba(255,255,255,0.15)", background: "rgba(255,255,255,0.05)",
        color: "var(--txt)", fontSize: 12, fontWeight: 600, cursor: "pointer",
      }}>
        Voir le suivi des missions <ArrowRight size={13} />
      </button>
    </div>
  );
}

/* ── Bandeau citation ─────────────────────────────────────── */
export function QuoteBar({ data }) {
  const navigate = useNavigate();
  const q = data?.citation_du_jour || {
    text: "La foi, c'est prendre le premier pas, même quand on ne voit pas tout l'escalier.",
    author: "Martin Luther King",
  };
  return (
    <div className="glass-card" data-testid="cockpit-quote-bar" style={{ padding: "16px 20px", marginTop: 4, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0 }}>
        <Quote size={20} color={GOLD} style={{ flexShrink: 0 }} />
        <p style={{ margin: 0, fontSize: 14, color: "var(--txt)", fontStyle: "italic", lineHeight: 1.4 }}>
          {q.text} <span style={{ color: "var(--txt-muted)", fontStyle: "normal" }}>— {q.author}</span>
        </p>
      </div>
      <button type="button" onClick={() => navigate("/vision")} data-testid="cockpit-inspiration-btn" style={{
        display: "inline-flex", alignItems: "center", gap: 6, flexShrink: 0,
        background: "var(--glass-soft)", border: "1px solid var(--glass-border)",
        borderRadius: 999, padding: "8px 16px", color: "var(--txt)", fontSize: 12.5, fontWeight: 600, cursor: "pointer",
      }}>
        <Sparkles size={14} color={GOLD} /> Inspiration du jour →
      </button>
    </div>
  );
}
