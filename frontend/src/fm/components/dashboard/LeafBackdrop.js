import React, { useEffect, useState } from "react";
import { Pencil, X, Check } from "lucide-react";
import { visionApi } from "@fm/lib/api";

/**
 * Backdrop hero du Dashboard.
 * Photo posée à gauche, teintée pour matcher la palette Zayado.
 *
 * Source par défaut : Pexels CDN (libre + stable, ne dépend pas d'Unsplash).
 * L'utilisateur peut remplacer cette image par une image de son Vision Board.
 * Choix persisté dans localStorage (clé : `dash_hero_img`).
 */
const DEFAULT_LEAF_URL =
  "https://images.unsplash.com/photo-1518495973542-4542c06a5843?w=1400&q=70&auto=format&fit=crop";

const STORAGE_KEY = "dash_hero_img";

export default function LeafBackdrop() {
  const [imageUrl, setImageUrl] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEY) || DEFAULT_LEAF_URL; } catch { return DEFAULT_LEAF_URL; }
  });
  const [pickerOpen, setPickerOpen] = useState(false);
  const [boardImages, setBoardImages] = useState([]);
  const [loadingPicker, setLoadingPicker] = useState(false);

  const openPicker = async () => {
    setPickerOpen(true);
    setLoadingPicker(true);
    try {
      const vision = await visionApi.get();
      const board = vision?.vision_board || vision?.board || [];
      const imgs = (Array.isArray(board) ? board : [])
        .map((it) => it?.image_url || it?.url || it?.src || it?.image)
        .filter(Boolean);
      setBoardImages(imgs);
    } catch {
      setBoardImages([]);
    } finally {
      setLoadingPicker(false);
    }
  };

  const selectImage = (url) => {
    setImageUrl(url);
    try { localStorage.setItem(STORAGE_KEY, url); } catch { /* ignore */ }
    setPickerOpen(false);
  };

  const resetImage = () => {
    setImageUrl(DEFAULT_LEAF_URL);
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
    setPickerOpen(false);
  };

  return (
    <>
      <div
        aria-hidden
        className="absolute top-0 left-0 right-0 h-[480px] md:h-[560px] pointer-events-none z-0 overflow-hidden"
        data-testid="hero-backdrop"
      >
        {/* Image */}
        <div
          className="absolute top-0 left-0 h-full transition-[background-image] duration-500"
          style={{
            width: "55%",
            backgroundImage: `url('${imageUrl}')`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat",
            filter: "saturate(0.6) brightness(0.95) contrast(1.02)",
            opacity: 0.78,
            maskImage:
              "linear-gradient(90deg, #000 0%, #000 60%, transparent 100%)",
            WebkitMaskImage:
              "linear-gradient(90deg, #000 0%, #000 60%, transparent 100%)",
          }}
        />
        {/* Voile crème */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(90deg, rgba(253,251,246,0.08) 0%, rgba(253,251,246,0.22) 30%, rgba(253,251,246,0.55) 50%, rgba(253,251,246,0.92) 70%, #f6f3ee 88%, #f6f3ee 100%)",
          }}
        />
        {/* Fondu vertical */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(180deg, transparent 0%, transparent 65%, rgba(253,251,246,0.55) 85%, #f6f3ee 100%)",
          }}
        />
      </div>

      {/* Bouton "Personnaliser" — beige sand visible */}
      <button
        type="button"
        onClick={openPicker}
        data-testid="hero-image-edit"
        className="absolute top-[88px] right-6 z-30 inline-flex items-center gap-2 px-3.5 py-2 rounded-full bg-sand-300 text-navy text-[12.5px] font-medium shadow-md border border-sand-400 hover:bg-sand-400 hover:shadow-lg transition"
        title="Personnaliser l'image (depuis votre Vision Board)"
      >
        <Pencil size={13} strokeWidth={2.2} />
        <span>Personnaliser le hero</span>
      </button>

      {/* Picker modal */}
      {pickerOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={() => setPickerOpen(false)}
          data-testid="hero-picker-overlay"
        >
          <div
            className="bg-cream rounded-2xl shadow-2xl max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-navy/10">
              <h2 className="text-[18px] font-display text-navy">Choisir une image</h2>
              <button
                type="button"
                onClick={() => setPickerOpen(false)}
                className="w-8 h-8 grid place-items-center rounded-full hover:bg-navy/5 text-navy"
                aria-label="Fermer"
                data-testid="hero-picker-close"
              >
                <X size={16} />
              </button>
            </div>
            <div className="overflow-y-auto p-5">
              {loadingPicker ? (
                <p className="text-ink-soft text-sm text-center py-8">Chargement…</p>
              ) : boardImages.length === 0 ? (
                <div className="text-center py-10">
                  <p className="text-ink-soft text-sm mb-2">
                    Votre Vision Board ne contient pas encore d&apos;image.
                  </p>
                  <p className="text-ink-soft/70 text-xs">
                    Ajoutez des images dans <a href="/vision" className="underline text-navy">la page Vision</a> pour les retrouver ici.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {boardImages.map((url, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => selectImage(url)}
                      data-testid={`hero-picker-img-${i}`}
                      className={`relative aspect-[4/3] rounded-lg overflow-hidden border-2 transition ${
                        url === imageUrl ? "border-navy" : "border-transparent hover:border-navy/30"
                      }`}
                    >
                      <img
                        src={url}
                        alt={`Vision ${i + 1}`}
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                      {url === imageUrl && (
                        <span className="absolute top-1.5 right-1.5 w-5 h-5 grid place-items-center rounded-full bg-navy text-cream">
                          <Check size={12} />
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div className="px-5 py-3 border-t border-navy/10 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={resetImage}
                className="text-[12.5px] text-ink-soft hover:text-navy underline underline-offset-2"
                data-testid="hero-picker-reset"
              >
                Revenir à l&apos;image par défaut
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
