import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { api } from "@/lib/api";

const STORAGE_KEY = "zayado_shop_broadcast_seen";

function getSeen() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch { return []; }
}
function markSeen(id) {
  const arr = getSeen();
  if (!arr.includes(id)) {
    arr.push(id);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(arr.slice(-50))); } catch { /* ignore */ }
  }
}

/**
 * Banner discret en haut de la boutique (surface = "shop_banner").
 * Dismiss → masqué pour la session via localStorage.
 */
export function ShopNotificationBanner() {
  const [notif, setNotif] = useState(null);
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api.get("/broadcast-notifications/active?surface=shop_banner")
      .then((r) => {
        const data = r?.data;
        if (cancelled || !data || !data.id) return;
        if (getSeen().includes(data.id)) return;
        setNotif(data);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const close = () => {
    if (notif) markSeen(notif.id);
    setHidden(true);
  };

  if (!notif || hidden) return null;
  return (
    <div
      className="relative w-full bg-[#1a3a6e] text-[#FAF7F2] py-2.5 px-4 text-sm flex items-center justify-center gap-3"
      data-testid="shop-broadcast-banner"
      role="status"
    >
      <span className="font-medium">{notif.title}</span>
      {notif.cta_url && (
        <a
          href={notif.cta_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => markSeen(notif.id)}
          className="underline underline-offset-2 hover:opacity-80"
          data-testid="shop-broadcast-banner-cta"
        >
          {notif.cta_label || "En savoir plus"} →
        </a>
      )}
      <button
        onClick={close}
        aria-label="Fermer"
        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-white/10"
        data-testid="shop-broadcast-banner-close"
      >
        <X size={14} />
      </button>
    </div>
  );
}

/**
 * Modal d'arrivée sur la boutique (surface = "shop_modal").
 * Supporte un embed Canva.
 */
export function ShopNotificationModal() {
  const [notif, setNotif] = useState(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(() => {
      api.get("/broadcast-notifications/active?surface=shop_modal")
        .then((r) => {
          const data = r?.data;
          if (cancelled || !data || !data.id) return;
          if (getSeen().includes(data.id)) return;
          setNotif(data);
          setOpen(true);
        })
        .catch(() => {});
    }, 1000);
    return () => { cancelled = true; clearTimeout(t); };
  }, []);

  const close = () => {
    if (notif) markSeen(notif.id);
    setOpen(false);
  };

  if (!open || !notif) return null;
  return (
    <div
      className="fixed inset-0 z-[200] bg-black/55 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={close}
      data-testid="shop-broadcast-modal-backdrop"
    >
      <div
        className="relative w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-2xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        data-testid="shop-broadcast-modal"
      >
        <button
          onClick={close}
          aria-label="Fermer"
          className="absolute top-3 right-3 z-10 w-9 h-9 grid place-items-center rounded-full bg-white/90 hover:bg-white text-slate-700 shadow"
          data-testid="shop-broadcast-modal-close"
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
              data-testid="shop-broadcast-iframe"
            />
          </div>
        ) : (
          <div className="p-6 md:p-8 max-h-[70vh] overflow-y-auto">
            <h2 className="font-display text-2xl md:text-3xl text-[#1a3a6e] mb-3">{notif.title}</h2>
            {notif.body_html && (
              <div
                className="prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{ __html: notif.body_html }}
              />
            )}
          </div>
        )}
        {notif.cta_url && (
          <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-[#E8E2D8] bg-[#FAF7F2]">
            <a
              href={notif.cta_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => markSeen(notif.id)}
              className="inline-flex items-center gap-1 px-4 py-2 rounded-md bg-[#1a3a6e] hover:opacity-90 text-white text-sm font-medium"
              data-testid="shop-broadcast-cta"
            >
              {notif.cta_label || "Découvrir"}
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
