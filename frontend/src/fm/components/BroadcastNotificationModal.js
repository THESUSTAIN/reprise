/* eslint-disable */
import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { api } from "@fm/lib/api";
import { useAuth } from "@fm/context/AuthContext";
import { useEscapeClose } from "@fm/hooks/useEscapeClose";

/**
 * Broadcast notification modal — affiché 1x par notification id (localStorage)
 * Supporte un embed iframe (Canva, etc.) ou un body HTML simple.
 * Surface = "app_modal" (cockpit SaaS), audience = all | logged | guests.
 */
const STORAGE_KEY = "zayado_broadcast_seen";

function getSeen() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch { return []; }
}
function markSeen(id) {
  const arr = getSeen();
  if (!arr.includes(id)) {
    arr.push(id);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(arr.slice(-50))); } catch {}
  }
}

export default function BroadcastNotificationModal({ surface = "app_modal" }) {
  const { user } = useAuth();
  const [notif, setNotif] = useState(null);
  const [open, setOpen] = useState(false);

  useEscapeClose(open, () => close());

  useEffect(() => {
    let cancelled = false;
    // Délai léger pour laisser la page se charger avant d'afficher
    const t = setTimeout(() => {
      api.get(`/api/broadcast-notifications/active?surface=${surface}`)
        .then((data) => {
          if (cancelled || !data || !data.id) return;
          const seen = getSeen();
          if (seen.includes(data.id)) return;
          setNotif(data);
          setOpen(true);
        })
        .catch(() => {});
    }, 800);
    return () => { cancelled = true; clearTimeout(t); };
  }, [surface, user?.id]);

  const close = () => {
    if (notif) markSeen(notif.id);
    setOpen(false);
  };

  if (!open || !notif) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="fixed inset-0 z-[200] bg-black/55 backdrop-blur-sm flex items-center justify-center p-4"
        onClick={close}
        data-testid="broadcast-modal-backdrop"
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0, y: 10 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.96, opacity: 0 }}
          transition={{ type: "spring", stiffness: 240, damping: 22 }}
          className="relative w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-2xl bg-white shadow-2xl border border-[var(--zayado-border,#E8E2D8)]"
          onClick={(e) => e.stopPropagation()}
          data-testid="broadcast-modal"
        >
          <button
            onClick={close}
            aria-label="Fermer"
            className="absolute top-3 right-3 z-10 w-9 h-9 grid place-items-center rounded-full bg-white/90 hover:bg-white text-slate-700 border border-[var(--zayado-border,#E8E2D8)] shadow-sm"
            data-testid="broadcast-close"
          >
            <X size={16} />
          </button>

          {notif.embed_url ? (
            <div className="w-full" style={{ aspectRatio: "16/10", maxHeight: "70vh" }}>
              <iframe
                src={notif.embed_url}
                title={notif.title}
                loading="lazy"
                allow="fullscreen"
                className="w-full h-full border-0"
                data-testid="broadcast-iframe"
              />
            </div>
          ) : (
            <div className="p-6 md:p-8 max-h-[70vh] overflow-y-auto">
              <h2 className="font-display text-2xl md:text-3xl text-[var(--zayado-navy,#1a3a6e)] mb-3">
                {notif.title}
              </h2>
              {notif.body_html && (
                <div
                  className="prose prose-sm max-w-none text-[var(--zayado-text,#2a2a2a)]"
                  dangerouslySetInnerHTML={{ __html: notif.body_html }}
                />
              )}
            </div>
          )}

          <div className="flex items-center justify-between gap-2 px-5 py-3 border-t border-[var(--zayado-border,#E8E2D8)] bg-[var(--zayado-cream,#FAF7F2)]">
            <p className="text-[11px] text-[var(--zayado-muted,#7a7066)]">
              Tu peux fermer ce message — il ne s'affichera plus.
            </p>
            {notif.cta_url && (
              <a
                href={notif.cta_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => markSeen(notif.id)}
                className="inline-flex items-center gap-1 px-4 py-2 rounded-md bg-[var(--zayado-navy,#1a3a6e)] hover:opacity-90 text-white text-sm font-medium"
                data-testid="broadcast-cta"
              >
                {notif.cta_label || "Découvrir"}
              </a>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
