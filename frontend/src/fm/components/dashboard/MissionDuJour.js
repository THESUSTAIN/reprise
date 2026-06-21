import React, { useState } from "react";
import { Target, Clock, BarChart3, ArrowRight, Pencil, RotateCw, Loader2, X } from "lucide-react";
import { DASH } from "@fm/constants/testIds";
import { api } from "@fm/lib/api";
import { toast } from "sonner";

export default function MissionDuJour({ data, onRefresh }) {
  const [busy, setBusy] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftDuration, setDraftDuration] = useState(60);
  const title = data?.title || "Finaliser le lancement du Growth Agent";
  const impact = data?.impact || "élevé";
  const duration = data?.duration_min || 150;
  const hours = Math.floor(duration / 60);
  const minutes = duration % 60;
  const durationLabel = hours ? `${hours}h${minutes ? ` ${minutes}` : ""}` : `${minutes} min`;
  const energy = Math.max(1, Math.min(3, data?.energy_required || 2));

  return (
    <div
      className="card-navy p-7 md:p-8 flex flex-col justify-between rise"
      style={{ animationDelay: "60ms" }}
    >
      <div className="relative">
        <div className="flex items-start gap-4 mb-7">
          <div className="w-12 h-12 rounded-2xl bg-cream/10 grid place-items-center ring-1 ring-cream/15 text-gold-soft">
            <Target size={20} strokeWidth={1.8} />
          </div>
          <div className="pt-1">
            <p className="text-[10.5px] tracking-[0.26em] uppercase text-gold-soft/80 font-semibold">
              Mission du jour
            </p>
          </div>
        </div>

        <h2 className="font-display text-[26px] md:text-[32px] leading-[1.05] font-medium text-cream pr-2" data-testid="mission-title">
          {title}
        </h2>

        <div className="mt-7 flex flex-wrap items-center gap-2.5">
          <Badge icon={<BarChart3 size={13} strokeWidth={2} />}>
            Impact {impact}
          </Badge>
          <Badge icon={<Clock size={13} strokeWidth={2} />}>{durationLabel}</Badge>
          <Badge>
            Énergie requise
            <span className="ml-2 flex items-center gap-1">
              {[1, 2, 3].map((n) => <Dot key={n} active={n <= energy} />)}
            </span>
          </Badge>
        </div>
      </div>

      <div className="relative mt-8 flex flex-wrap items-center gap-2">
        <button
          data-testid={DASH.missionStart}
          onClick={async () => {
            if (busy) return;
            setBusy(true);
            try {
              if (data?.id) {
                await api.patch(`/tasks/${data.id}`, { in_progress: true });
              }
              // Notifier l'IA (collaborateur) que la mission est démarrée
              api.post("/api/collaborateur/notify", {
                event: "mission_started",
                title: title,
                duration_min: duration,
              }).catch(() => {});
              toast.success("Mission démarrée — votre IA a été notifiée 🚀");
              onRefresh && onRefresh();
            } catch (e) {
              toast.error("Action impossible : " + (e?.detail || "erreur"));
            } finally { setBusy(false); }
          }}
          disabled={busy}
          className="group inline-flex items-center gap-2 pl-5 pr-3 h-11 rounded-full bg-cream text-navy font-semibold text-sm hover:bg-gold-soft transition-colors disabled:opacity-60"
        >
          Commencer
          <span className="w-8 h-8 rounded-full bg-navy text-cream grid place-items-center group-hover:translate-x-0.5 transition-transform">
            <ArrowRight size={14} strokeWidth={2.2} />
          </span>
        </button>
        <button
          data-testid={DASH.missionEdit}
          onClick={() => {
            if (!data?.id) {
              toast.info("Chargement de la mission en cours…");
              return;
            }
            setDraftTitle(title);
            setDraftDuration(data?.duration_min || 60);
            setEditOpen(true);
          }}
          className="inline-flex items-center gap-2 px-4 h-11 rounded-full bg-cream/8 hover:bg-cream/15 text-cream text-sm font-medium ring-1 ring-cream/15 transition-colors"
        >
          Modifier
          <Pencil size={14} strokeWidth={2} />
        </button>
        <button
          data-testid={DASH.missionSuggest}
          onClick={async () => {
            if (busy) return;
            setBusy(true);
            try {
              const m = await api.post("/mission/suggest", {});
              toast.success("Nouvelle mission générée : " + (m.label || "").slice(0, 60));
              onRefresh && onRefresh();
            } catch (e) {
              toast.error("Génération impossible : " + (e?.detail || e?.message || "erreur IA"));
            } finally { setBusy(false); }
          }}
          disabled={busy}
          className="inline-flex items-center gap-2 px-4 h-11 rounded-full bg-cream/8 hover:bg-cream/15 text-cream text-sm font-medium ring-1 ring-cream/15 transition-colors disabled:opacity-60"
        >
          {busy ? (
            <><Loader2 size={14} className="animate-spin" /> Génération…</>
          ) : (
            <><RotateCw size={14} strokeWidth={2} /> Autre suggestion</>
          )}
        </button>
      </div>

      {editOpen && (
        <div className="fixed inset-0 z-50 bg-navy-deep/60 backdrop-blur-sm grid place-items-center p-4" onClick={() => setEditOpen(false)}>
          <div onClick={(e) => e.stopPropagation()} className="bg-cream rounded-3xl p-6 max-w-md w-full border border-sand-200 shadow-soft">
            <div className="flex items-center justify-between mb-4">
              <p className="font-display text-[22px] text-navy">Modifier la mission</p>
              <button onClick={() => setEditOpen(false)} className="text-ink-soft hover:text-ink"><X size={18} /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-[11px] uppercase tracking-[0.18em] text-ink-soft font-semibold">Titre</label>
                <input
                  data-testid="mission-edit-title"
                  value={draftTitle}
                  onChange={(e) => setDraftTitle(e.target.value)}
                  autoFocus
                  className="mt-1 w-full bg-white border border-sand-200 rounded-2xl px-4 py-2.5 text-[14px] text-ink focus:outline-none focus:border-navy/40"
                />
              </div>
              <div>
                <label className="text-[11px] uppercase tracking-[0.18em] text-ink-soft font-semibold">Durée (minutes)</label>
                <input
                  type="number" min={5} max={480} step={5}
                  data-testid="mission-edit-duration"
                  value={draftDuration}
                  onChange={(e) => setDraftDuration(parseInt(e.target.value, 10) || 0)}
                  className="mt-1 w-full bg-white border border-sand-200 rounded-2xl px-4 py-2.5 text-[14px] text-ink focus:outline-none focus:border-navy/40"
                />
              </div>
            </div>
            <div className="mt-5 flex gap-2">
              <button
                data-testid="mission-edit-save"
                onClick={async () => {
                  if (!draftTitle.trim()) { toast.error("Titre requis"); return; }
                  setBusy(true);
                  try {
                    await api.patch(`/tasks/${data.id}`, { label: draftTitle.trim(), duration_min: draftDuration });
                    toast.success("Mission mise à jour");
                    setEditOpen(false);
                    onRefresh && onRefresh();
                  } catch (e) {
                    toast.error("Édition impossible : " + (e?.detail || "erreur"));
                  } finally { setBusy(false); }
                }}
                disabled={busy || !draftTitle.trim()}
                className="flex-1 px-4 h-11 rounded-full bg-navy text-cream text-[13px] font-semibold hover:bg-navy-bright transition disabled:opacity-50"
              >
                {busy ? <Loader2 size={14} className="animate-spin inline" /> : "Enregistrer"}
              </button>
              <button onClick={() => setEditOpen(false)} className="px-4 h-11 rounded-full bg-cream-soft text-ink text-[13px] font-medium">Annuler</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Badge({ icon, children }) {
  return (
    <span className="inline-flex items-center gap-2 h-8 px-3.5 rounded-full bg-cream/[0.07] ring-1 ring-cream/10 text-[12.5px] font-medium text-cream/90">
      {icon}
      {children}
    </span>
  );
}

function Dot({ active = false }) {
  return (
    <span
      className={`w-1.5 h-1.5 rounded-full ${
        active ? "bg-gold-soft" : "bg-cream/25"
      }`}
    />
  );
}
