/**
 * Product3DViewer — Viewer 3D interactif rotation 360°
 * Utilise <model-viewer> de Google (WebGL, pas de Three.js manuel requis)
 * Compatible avec fichiers .glb / .gltf
 *
 * Usage :
 *   <Product3DViewer modelUrl="/models3d/support-laptop.glb" productName="Support laptop" />
 *
 * Si pas de modèle 3D disponible → fallback galerie photos standard.
 *
 * Pour ajouter un modèle 3D :
 *   1. Convertir les photos en .glb via https://poly.cam ou Blender
 *   2. Placer dans frontend/public/models3d/[slug].glb
 *   3. Passer modelUrl="/models3d/[slug].glb"
 */
import React, { useEffect, useRef, useState } from "react";
import { RotateCcw, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

export default function Product3DViewer({ modelUrl, productName = "produit", fallbackImages = [] }) {
  const viewerRef = useRef(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);

  // Charger le script model-viewer depuis CDN (Google)
  useEffect(() => {
    if (typeof customElements !== "undefined" && customElements.get("model-viewer")) {
      setScriptLoaded(true);
      return;
    }
    const script = document.createElement("script");
    script.type = "module";
    script.src = "https://ajax.googleapis.com/ajax/libs/model-viewer/3.5.0/model-viewer.min.js";
    script.onload = () => setScriptLoaded(true);
    script.onerror = () => setError(true);
    document.head.appendChild(script);
    return () => {};
  }, []);

  // Si pas de modèle 3D → fallback galerie photos
  if (!modelUrl) {
    if (fallbackImages.length === 0) return null;
    return (
      <div className="rounded-xl overflow-hidden bg-gray-50" data-testid="product-gallery">
        <img src={fallbackImages[0]} alt={productName} className="w-full object-cover" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl bg-gray-50 p-8 text-center text-sm text-gray-400" data-testid="viewer-error">
        Viewer 3D indisponible — voir les photos ci-dessous.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-[var(--zayado-border)] overflow-hidden bg-[var(--zayado-cream)]"
         data-testid="product-3d-viewer">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--zayado-border)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
          <span className="text-xs font-medium text-[var(--zayado-muted)]">Vue 3D — glisser pour tourner</span>
        </div>
        <button
          onClick={() => viewerRef.current?.requestFullscreen?.()}
          className="p-1.5 rounded-lg hover:bg-[var(--zayado-cream-dark)] transition-colors text-[var(--zayado-muted)]"
          title="Plein écran"
        >
          <Maximize2 size={14} />
        </button>
      </div>

      {/* Viewer */}
      <div className="relative" style={{ height: "320px" }}>
        {!loaded && !error && (
          <div className="absolute inset-0 flex items-center justify-center bg-[var(--zayado-cream)]">
            <div className="text-center">
              <div className="w-8 h-8 border-2 border-[var(--zayado-navy)] border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <p className="text-xs text-[var(--zayado-muted)]">Chargement du modèle 3D…</p>
            </div>
          </div>
        )}

        {scriptLoaded && (
          // eslint-disable-next-line react/no-unknown-property
          <model-viewer
            ref={viewerRef}
            src={modelUrl}
            alt={`Vue 3D de ${productName}`}
            auto-rotate
            auto-rotate-delay="1000"
            rotation-per-second="30deg"
            camera-controls
            touch-action="pan-y"
            shadow-intensity="1"
            exposure="1.1"
            style={{ width: "100%", height: "100%", background: "transparent" }}
            onLoad={() => setLoaded(true)}
            onError={() => setError(true)}
            data-testid="model-viewer-el"
          />
        )}
      </div>

      {/* Instructions */}
      <div className="px-4 py-2.5 border-t border-[var(--zayado-border)] flex items-center justify-center gap-6 text-[10px] text-[var(--zayado-muted)]">
        <span>🖱️ Clic + glisser : tourner</span>
        <span>🔍 Scroll : zoom</span>
        <span>✌️ Pinch : zoom (mobile)</span>
      </div>
    </div>
  );
}
