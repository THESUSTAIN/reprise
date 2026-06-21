/* eslint-disable */
import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useLocation, useNavigate } from "react-router-dom";
import { X } from "lucide-react";
import { energyApi, meApi } from "@fm/lib/api";
import { useAuth } from "@fm/context/AuthContext";
import { useEscapeClose } from "@fm/hooks/useEscapeClose";
import { toast } from "sonner";

const DISMISS_KEY = "mxai_energy_popup_dismissed_until";

/**
 * Energy "How do you arrive this morning?" pill — sits just above the
 * floating bottom bar. Tap an emoji to log the day's ritual instantly.
 */
const MOODS = [
  { emoji: "😌", label: "Serein", physique: 8, mentale: 8, stress: 2 },
  { emoji: "🙂", label: "Bien", physique: 7, mentale: 7, stress: 3 },
  { emoji: "😐", label: "Neutre", physique: 5, mentale: 5, stress: 5 },
  { emoji: "😣", label: "Tendu", physique: 4, mentale: 4, stress: 8 },
  { emoji: "🤯", label: "Submergé", physique: 3, mentale: 3, stress: 9 },
];

export default function EnergyMorningPopup() {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  useEscapeClose(open, () => {
    setOpen(false);
    const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate() + 1); tomorrow.setHours(4, 0, 0, 0);
    localStorage.setItem(DISMISS_KEY, tomorrow.toISOString());
  });

  useEffect(() => {
    if (!user || !user.id) return;
    if (user.show_energy_popup === false) return;
    // Only show on the dashboard (home). Hide everywhere else to avoid overlay noise.
    if (location.pathname !== "/") return;
    const dismissed = localStorage.getItem(DISMISS_KEY);
    if (dismissed) {
      const today = new Date().toISOString().slice(0, 10);
      if (dismissed >= today) return;
    }
    let cancelled = false;
    (async () => {
      try {
        const t = await energyApi.today();
        if (cancelled) return;
        if (!t.found) setOpen(true);
      } catch {
        /* ignore */
      }
    })();
    return () => { cancelled = true; };
  }, [user, location.pathname]);

  const dismissToday = () => {
    const today = new Date().toISOString().slice(0, 10);
    localStorage.setItem(DISMISS_KEY, today);
    setOpen(false);
  };
  const disablePermanently = async () => {
    try { await meApi.updateProfile({ show_energy_popup: false }); } catch {}
    dismissToday();
  };
  const pick = async (m) => {
    setBusy(true);
    try {
      await energyApi.ritual(m.physique, m.mentale, m.stress);
      toast.success(`${m.emoji} Énergie posée — le copilote ajuste ta charge.`);
      dismissToday();
    } catch (e) {
      toast.error(e.message || "Erreur");
    } finally {
      setBusy(false);
    }
  };

  if (!open) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 14 }}
        transition={{ type: "spring", stiffness: 280, damping: 28 }}
        className="fixed bottom-[80px] md:bottom-[88px] left-1/2 -translate-x-1/2 z-[55] w-[92%] max-w-md"
        data-testid="energy-morning-popup"
      >
        <div className="relative rounded-3xl bg-navy text-cream shadow-float border border-white/10 px-5 py-4">
          <button
            data-testid="energy-popup-close"
            onClick={dismissToday}
            aria-label="Fermer"
            className="absolute top-3 right-3 w-7 h-7 grid place-items-center rounded-full text-cream/70 hover:text-cream hover:bg-white/10"
          ><X size={14} /></button>
          <p className="font-display text-[18px] leading-snug">
            Comment tu arrives <span className="font-serif-italic text-gold-deep">ce matin</span> ?
          </p>
          <div className="mt-3 flex items-center justify-between gap-2" data-testid="energy-emoji-row">
            {MOODS.map((m) => (
              <button
                key={m.emoji}
                data-testid={`energy-mood-${m.label.toLowerCase()}`}
                onClick={() => pick(m)}
                disabled={busy}
                aria-label={m.label}
                className="text-[34px] sm:text-[40px] leading-none hover:scale-110 active:scale-95 transition-transform disabled:opacity-40 cursor-pointer select-none"
              >
                {m.emoji}
              </button>
            ))}
          </div>
          <div className="mt-3 flex items-center justify-between text-[11px] text-cream/65">
            <span>1 clic · le copilote ajuste ta charge en conséquence.</span>
            <button
              data-testid="energy-popup-more"
              onClick={() => { dismissToday(); navigate("/bien-etre"); }}
              className="underline hover:text-cream"
            >Plus de détails →</button>
          </div>
          <button
            data-testid="energy-popup-disable"
            onClick={disablePermanently}
            className="absolute -top-2 -left-2 text-[10px] bg-cream-soft text-ink-soft px-2 py-0.5 rounded-full border border-sand-300 hover:bg-sand-200"
          >Ne plus afficher</button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
