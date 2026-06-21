import React from "react";
import { X, Check } from "lucide-react";

/**
 * WelcomeModal — popup d'accueil par page (style "Welcome to Leads")
 * repris avec la palette navy/cream/or de Zayado.
 *
 * Usage : voir hooks/useWelcomeModal.js
 */
export default function WelcomeModal({ open, onClose, icon: Icon, title, description, points = [] }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4 bg-navy/50 backdrop-blur-sm"
         data-testid="welcome-modal-overlay">
      <div className="relative w-full max-w-[480px] rounded-3xl border border-sand-200 bg-white shadow-2xl p-7 md:p-8 text-center"
           data-testid="welcome-modal">
        <button onClick={onClose} aria-label="Fermer" data-testid="welcome-modal-close"
                className="absolute top-4 right-4 text-ink-soft hover:text-ink transition">
          <X size={18} />
        </button>

        {/* Icône */}
        <div className="mx-auto mb-5 w-16 h-16 rounded-2xl grid place-items-center"
             style={{ background: "rgba(38,70,83,0.08)" }}>
          {Icon && <Icon size={28} className="text-navy" strokeWidth={1.8} />}
        </div>

        {/* Titre */}
        <h2 className="font-display text-[24px] md:text-[26px] text-navy mb-3">
          {title}
        </h2>

        {/* Description */}
        <p className="text-[14px] text-ink-soft leading-relaxed mb-5">
          {description}
        </p>

        {/* Liste de points clés */}
        {points.length > 0 && (
          <ul className="text-left space-y-2.5 mb-6">
            {points.map((p, i) => (
              <li key={i} className="flex items-start gap-2.5 text-[13.5px] text-ink">
                <Check size={16} className="text-emerald-600 shrink-0 mt-0.5" />
                <span>{p}</span>
              </li>
            ))}
          </ul>
        )}

        <button onClick={onClose} data-testid="welcome-modal-cta"
                className="w-full h-12 rounded-full bg-navy text-cream text-[14px] font-semibold hover:bg-navy/90 transition">
          Compris, on y va !
        </button>
      </div>
    </div>
  );
}
