/**
 * VirtualTryOn — Essai virtuel de lunettes
 * Phase 1 : Upload selfie → IA place les lunettes → résultat en ~5s
 * Phase 2 (V2) : Jeeliz temps réel via caméra (commenté, prêt à activer)
 *
 * Usage dans la fiche produit :
 *   import VirtualTryOn from "@/components/VirtualTryOn";
 *   <VirtualTryOn productName="Lunettes Anti-Lumière Bleue" productSlug="lunettes-anti-lumiere" />
 */
import React, { useState, useRef, useCallback } from "react";
import { Camera, Upload, X, Loader2, Download, RefreshCw } from "lucide-react";
import api from "@/lib/api";

export default function VirtualTryOn({ productName = "ces lunettes", productSlug = "" }) {
  const [phase, setPhase] = useState("idle"); // idle | preview | generating | result | error
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const fileRef = useRef(null);

  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith("image/")) {
      setError("Veuillez sélectionner une image (JPG, PNG, WEBP).");
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setError("Image trop grande — maximum 8 Mo.");
      return;
    }
    setError("");
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
      setPhase("preview");
    };
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  const generate = async () => {
    if (!preview) return;
    setPhase("generating");
    setError("");
    try {
      // Envoyer la selfie + le slug produit → l'IA génère le rendu
      const r = await api.post("/boutique/virtual-tryon", {
        image_base64: preview.split(",")[1],
        product_slug: productSlug,
        product_name: productName,
      });
      if (r.data?.result_url || r.data?.result_base64) {
        setResult(r.data.result_url || `data:image/jpeg;base64,${r.data.result_base64}`);
        setPhase("result");
      } else {
        throw new Error("Aucun résultat retourné.");
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Erreur lors de la génération.";
      setError(msg);
      setPhase("error");
    }
  };

  const reset = () => {
    setPhase("idle");
    setPreview(null);
    setResult(null);
    setError("");
  };

  return (
    <div className="rounded-2xl border border-[var(--zayado-border)] overflow-hidden" data-testid="virtual-tryon">
      {/* Header */}
      <div className="px-5 py-4 bg-[var(--zayado-navy)] text-white flex items-center gap-3">
        <Camera size={18} />
        <div>
          <div className="font-semibold text-sm">Essai virtuel</div>
          <div className="text-xs opacity-70">Essayez {productName} sur votre photo</div>
        </div>
      </div>

      <div className="p-5">
        {/* PHASE : idle — zone d'upload */}
        {(phase === "idle" || phase === "error") && (
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            className="border-2 border-dashed border-[var(--zayado-border)] rounded-xl p-8 text-center hover:border-[var(--zayado-navy)] transition-colors cursor-pointer"
            onClick={() => fileRef.current?.click()}
            data-testid="tryon-dropzone"
          >
            <Upload size={28} className="mx-auto mb-3 text-[var(--zayado-muted)]" />
            <p className="text-sm font-semibold text-[var(--zayado-navy)] mb-1">
              Déposez votre selfie ici
            </p>
            <p className="text-xs text-[var(--zayado-muted)] mb-3">
              JPG, PNG ou WEBP · Max 8 Mo
            </p>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--zayado-navy)] text-white text-xs font-semibold">
              <Upload size={12} /> Choisir une photo
            </div>
            {error && (
              <p className="mt-3 text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg" data-testid="tryon-error">
                {error}
              </p>
            )}
          </div>
        )}

        {/* PHASE : preview — photo chargée, en attente de génération */}
        {phase === "preview" && (
          <div data-testid="tryon-preview">
            <div className="relative rounded-xl overflow-hidden mb-4">
              <img src={preview} alt="Votre selfie" className="w-full max-h-72 object-cover" />
              <button
                onClick={reset}
                className="absolute top-2 right-2 w-8 h-8 rounded-full bg-black/50 text-white flex items-center justify-center hover:bg-black/70 transition-colors"
              >
                <X size={14} />
              </button>
            </div>
            <button
              onClick={generate}
              className="w-full py-3 rounded-xl bg-[var(--zayado-navy)] text-white font-semibold text-sm hover:opacity-90 transition-opacity"
              data-testid="tryon-generate-btn"
            >
              ✨ Essayer {productName}
            </button>
          </div>
        )}

        {/* PHASE : generating — IA en cours */}
        {phase === "generating" && (
          <div className="py-10 text-center" data-testid="tryon-loading">
            <Loader2 size={32} className="animate-spin mx-auto mb-4 text-[var(--zayado-navy)]" />
            <p className="text-sm font-semibold text-[var(--zayado-navy)] mb-1">Génération en cours…</p>
            <p className="text-xs text-[var(--zayado-muted)]">L'IA place les lunettes sur votre photo (~5 secondes)</p>
            <div className="w-full bg-[var(--zayado-border)] rounded-full h-1.5 mt-4 overflow-hidden">
              <div className="h-full bg-[var(--zayado-navy)] rounded-full animate-pulse" style={{ width: "60%" }} />
            </div>
          </div>
        )}

        {/* PHASE : result — résultat affiché */}
        {phase === "result" && result && (
          <div data-testid="tryon-result">
            <div className="relative rounded-xl overflow-hidden mb-4">
              <img src={result} alt="Résultat essai virtuel" className="w-full max-h-80 object-cover" />
              <div className="absolute bottom-2 left-2 bg-black/60 text-white text-[10px] px-2 py-1 rounded-full">
                Simulation IA
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={reset}
                className="flex-1 py-2.5 rounded-xl border border-[var(--zayado-border)] text-sm font-medium flex items-center justify-center gap-2 hover:bg-[var(--zayado-cream)] transition-colors"
                data-testid="tryon-retry"
              >
                <RefreshCw size={14} /> Réessayer
              </button>
              {result.startsWith("data:") ? (
                <a
                  href={result}
                  download={`essai-${productSlug || "lunettes"}.jpg`}
                  className="flex-1 py-2.5 rounded-xl bg-[var(--zayado-navy)] text-white text-sm font-medium flex items-center justify-center gap-2 hover:opacity-90 transition-opacity"
                  data-testid="tryon-download"
                >
                  <Download size={14} /> Télécharger
                </a>
              ) : (
                <button
                  onClick={() => window.open(result, "_blank")}
                  className="flex-1 py-2.5 rounded-xl bg-[var(--zayado-navy)] text-white text-sm font-medium flex items-center justify-center gap-2"
                >
                  <Download size={14} /> Voir en grand
                </button>
              )}
            </div>
            <p className="text-[10px] text-[var(--zayado-muted)] text-center mt-3">
              Rendu généré par IA · Les couleurs peuvent légèrement varier
            </p>
          </div>
        )}
      </div>

      {/* Zone upload cachée */}
      <input
        ref={fileRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
        data-testid="tryon-file-input"
      />

      {/* ── Phase 2 (V2) : Jeeliz temps réel ──────────────────────────────
      Décommentez quand les modèles 3D (.glb) des lunettes sont disponibles.

      import { useEffect, useRef as useCamRef } from "react";
      // Installer : npm install @jeeliz/jeelizglassesntfwidget
      // Modèles 3D : un fichier .glb par référence lunettes dans public/models3d/

      const cameraRef = useCamRef(null);
      useEffect(() => {
        if (phase !== "camera") return;
        // Init Jeeliz WebGL face tracking
        JeelizGlassesNTFWidget.init({
          canvas: cameraRef.current,
          NNPath: "/jeeliz/NNC.json",
          glassesMeshURL: `/models3d/${productSlug}.glb`,
          onComplete: () => console.log("Jeeliz ready"),
          onError: (e) => console.error("Jeeliz error", e),
        });
        return () => JeelizGlassesNTFWidget.destroy();
      }, [phase, productSlug]);
      ─────────────────────────────────────────────────────────────────── */}
    </div>
  );
}
