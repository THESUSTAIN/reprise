import React, { useState, useEffect } from "react";
import { X, Sparkles, Loader2, Wand2, ImagePlus, Video, ChevronRight, Zap } from "lucide-react";
import { toast } from "sonner";
import { studioApi } from "../../lib/finalVisionModuleApi";

// Templates statiques (miroir de /app/backend/routes/studio.py)
const STATIC_TEMPLATES = {
  images: [
    { id: "portrait",       label: "Portrait entrepreneur",  hint: "Dirigeant confiant, bureau lumineux, casual chic" },
    { id: "moodboard",      label: "Moodboard aspirationnel", hint: "Vision de succès, ambiance, univers visuel" },
    { id: "avatar-client",  label: "Univers client cible",   hint: "Le contexte visuel de votre client idéal" },
    { id: "brand-universe", label: "Univers de marque",       hint: "Identité visuelle, textures, ambiances" },
    { id: "aspirational",   label: "Vision aspirationnelle",  hint: "Symbolique de succès et de sérénité" },
  ],
  videos: [
    { id: "manifesto", label: "Manifesto 4s",           hint: "Voici ce que je construis en 2026" },
    { id: "reveal",    label: "Reveal / Coming Soon",   hint: "Teaser d'un lancement à venir" },
    { id: "vision",    label: "Vision annuelle",         hint: "Timeline visuelle de votre parcours" },
    { id: "citation",  label: "Citation motion",         hint: "Ambiance apaisante pour une phrase forte" },
  ],
};

/**
 * Studio Modal — Génération d'images (Nano Banana) et vidéos (Sora 2) dans le canvas.
 * Pattern CapCut : templates visibles en cards → clic → prompt guidé → génération → insertion.
 *
 * Props :
 * - open (bool) : ouverture
 * - onClose () : fermer
 * - onGenerated ({kind, url, prompt, template}) : callback après génération réussie
 * - initialKind ("image" | "video") : tab actif par défaut
 */
export default function StudioModal({ open, onClose, onGenerated, initialKind = "image" }) {
  const [tab, setTab] = useState(initialKind);
  const [templates] = useState(STATIC_TEMPLATES);
  const [quota, setQuota] = useState({ images: { remaining: 1, cap: 1 }, videos: { remaining: 1, cap: 1 } });
  const [selectedTpl, setSelectedTpl] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setTab(initialKind);
    setSelectedTpl(null);
    setPrompt("");
    studioApi.quota().then(setQuota).catch(() => {});
  }, [open, initialKind]);

  if (!open) return null;

  const list = tab === "image" ? templates.images : templates.videos;
  const q = tab === "image" ? quota.images : quota.videos;
  // remaining === null signifie plan illimité (serenite/business/admin) → toujours autorisé.
  const isUnlimited = q.remaining === null || q.remaining === undefined;
  const quotaExhausted = !isUnlimited && q.remaining <= 0;
  const canGenerate = !quotaExhausted && prompt.trim().length > 3;

  const handleTplClick = (tpl) => {
    setSelectedTpl(tpl);
    if (!prompt.trim()) setPrompt(tpl.hint || "");
  };

  const handleGenerate = async () => {
    if (!canGenerate) {
      if (quotaExhausted) return toast.error("Quota mensuel atteint. Passez à l'offre supérieure pour continuer.");
      return toast.error("Décrivez ce que vous voulez créer (au moins 4 caractères).");
    }
    setLoading(true);
    try {
      const templateId = selectedTpl?.id || "custom";
      const res = tab === "image"
        ? await studioApi.generateImage(prompt.trim(), templateId)
        : await studioApi.generateVideo(prompt.trim(), templateId);
      onGenerated?.(res);
      onClose();
      toast.success(tab === "image" ? "Image ajoutée au board ✦" : "Vidéo ajoutée au board ✦");
      setPrompt("");
    } catch (e) {
      const status = e?.response?.status;
      if (status === 429) {
        toast.error("Vous avez atteint votre quota. Passez à l'offre supérieure pour continuer.");
      } else {
        // Message simple — pas de détail technique côté fournisseur IA
        toast.error("La création n'est pas disponible pour le moment. Réessayez dans un instant.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
      onClick={onClose}
      data-testid="studio-modal"
    >
      <div
        className="relative w-full max-w-3xl max-h-[92vh] overflow-hidden rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface)] shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--app-border)] px-5 py-4">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--app-accent-soft)] text-[var(--app-accent)]">
              <Sparkles size={17} />
            </span>
            <div>
              <h3 className="font-head text-lg font-semibold text-[var(--app-text)]">Studio · Créer avec l'IA</h3>
              <p className="text-xs text-[var(--app-text-muted)]">Choisis un modèle, décris ta vision, l'IA génère.</p>
            </div>
          </div>
          <button onClick={onClose} className="rounded-lg p-2 text-[var(--app-text-muted)] hover:bg-[var(--app-surface-2)]" data-testid="studio-modal-close">
            <X size={16} />
          </button>
        </div>

        {/* Tabs Image / Video */}
        <div className="flex items-center gap-1 border-b border-[var(--app-border)] px-4 pt-3 pb-0">
          {[
            { id: "image", label: "Images IA", icon: ImagePlus },
            { id: "video", label: "Vidéos IA", icon: Video },
          ].map((t) => {
            const active = tab === t.id;
            const Icn = t.icon;
            return (
              <button
                key={t.id}
                onClick={() => { setTab(t.id); setSelectedTpl(null); }}
                data-testid={`studio-tab-${t.id}`}
                className={[
                  "flex items-center gap-1.5 rounded-t-lg border-b-2 px-3 py-2 text-sm font-medium transition",
                  active
                    ? "border-[var(--app-accent)] text-[var(--app-text)]"
                    : "border-transparent text-[var(--app-text-muted)] hover:text-[var(--app-text)]",
                ].join(" ")}
              >
                <Icn size={14} /> {t.label}
              </button>
            );
          })}
          <div className="ml-auto pb-2 flex items-center gap-1.5 text-[11px] text-[var(--app-text-muted)]">
            <Zap size={11} className="text-[var(--app-accent)]" />
            {isUnlimited ? (
              <span className="font-semibold text-[var(--app-text)]">Illimité</span>
            ) : (
              <>
                Quota : <span className="font-semibold text-[var(--app-text)]">{q.remaining}</span>/{q.cap} restant{q.cap > 1 ? "s" : ""} ce mois
              </>
            )}
          </div>
        </div>

        {/* Templates strip (CapCut style) */}
        <div className="overflow-y-auto flex-1 px-5 pt-4 pb-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--app-text-muted)] mb-2">Modèles</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 mb-4">
            <button
              onClick={() => setSelectedTpl(null)}
              data-testid="studio-tpl-custom"
              className={[
                "flex flex-col items-start gap-1 rounded-xl border p-3 text-left transition",
                selectedTpl === null
                  ? "border-[var(--app-accent)] bg-[var(--app-accent-soft)]"
                  : "border-[var(--app-border)] bg-[var(--app-surface-2)] hover:border-[var(--app-accent)]/50",
              ].join(" ")}
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--app-surface)] text-[var(--app-accent)]"><Wand2 size={15} /></span>
              <div className="mt-1">
                <div className="text-[12px] font-semibold text-[var(--app-text)]">Libre</div>
                <div className="text-[10px] text-[var(--app-text-muted)] leading-snug">Ton propre prompt, sans preset.</div>
              </div>
            </button>
            {list.map((tpl) => {
              const active = selectedTpl?.id === tpl.id;
              return (
                <button
                  key={tpl.id}
                  onClick={() => handleTplClick(tpl)}
                  data-testid={`studio-tpl-${tpl.id}`}
                  className={[
                    "flex flex-col items-start gap-1 rounded-xl border p-3 text-left transition",
                    active
                      ? "border-[var(--app-accent)] bg-[var(--app-accent-soft)]"
                      : "border-[var(--app-border)] bg-[var(--app-surface-2)] hover:border-[var(--app-accent)]/50",
                  ].join(" ")}
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--app-surface)] text-[var(--app-accent)]">
                    {tab === "image" ? <ImagePlus size={15} /> : <Video size={15} />}
                  </span>
                  <div className="mt-1">
                    <div className="text-[12px] font-semibold text-[var(--app-text)]">{tpl.label}</div>
                    <div className="text-[10px] text-[var(--app-text-muted)] leading-snug">{tpl.hint}</div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Prompt */}
          <label className="text-[11px] font-semibold uppercase tracking-wide text-[var(--app-text-muted)] mb-1 block">
            Décrivez votre {tab === "image" ? "image" : "vidéo"}
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleGenerate(); }}
            rows={3}
            autoFocus
            data-testid="studio-prompt"
            placeholder={selectedTpl?.hint || (tab === "image"
              ? "Ex : Portrait professionnel d'une dirigeante confiante dans un bureau lumineux"
              : "Ex : Timeline visuelle de mon parcours passé → 2027")}
            className="w-full resize-none rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-2)] px-3 py-2.5 text-sm text-[var(--app-text)] outline-none focus:border-[var(--app-accent)] placeholder:text-[var(--app-text-muted)]"
          />
        </div>

        {/* Footer */}
        <div className="border-t border-[var(--app-border)] px-5 py-3 flex items-center justify-between gap-3">
          {quotaExhausted ? (
            <>
              <p className="text-[11px] text-[var(--app-text-muted)]">
                Quota mensuel {tab === "image" ? "d'images" : "de vidéos"} atteint pour votre offre.
              </p>
              <a
                href="https://zayado.net/tarifs"
                target="_blank"
                rel="noopener noreferrer"
                data-testid="studio-upsell"
                className="flex items-center gap-2 rounded-full bg-[var(--app-accent)] px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90"
              >
                <Zap size={15} />
                Passer à l'offre supérieure
                <ChevronRight size={14} />
              </a>
            </>
          ) : (
            <>
              <p className="text-[11px] text-[var(--app-text-muted)]">
                {tab === "image" ? "Propulsé par Nano Banana (Google) · ~15s" : "Propulsé par Sora 2 · 2-5 min · gardez la fenêtre ouverte"}
              </p>
              <button
                onClick={handleGenerate}
                disabled={!canGenerate || loading}
                data-testid="studio-generate"
                className="flex items-center gap-2 rounded-full bg-[var(--app-navy)] px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {loading ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
                {loading ? "Génération…" : `Générer ${tab === "image" ? "l'image" : "la vidéo"}`}
                <ChevronRight size={14} />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
