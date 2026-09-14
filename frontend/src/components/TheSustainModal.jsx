import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { BookOpen, Book, Users, Sparkles, ExternalLink, X, Loader2 } from "lucide-react";
import { getPublicConfig } from "../lib/api";

// Fenêtre TheSustain — s'ouvre au clic sur l'item "TheSustain" de
// l'Écosystème (Layout.jsx). Chaque case redirige vers une URL réelle de
// thesustain.net, éditable par un admin via /admin/config
// ({thesustain_urls: {...}}) — jamais codée en dur dans le composant.
const TILES = [
  { key: "journal", label: "Journal", desc: "Votre journal spirituel sur thesustain.net", Icon: BookOpen },
  { key: "bible", label: "Bible", desc: "Lecture et versets du jour", Icon: Book },
  { key: "communaute", label: "Communauté", desc: "Échanger avec d'autres membres", Icon: Users },
  { key: "ressources", label: "Ressources", desc: "Articles, prières, enseignements", Icon: Sparkles },
];

export function TheSustainModal({ open, onClose }) {
  const [urls, setUrls] = useState(null);

  useEffect(() => {
    if (!open) return;
    getPublicConfig().then((cfg) => setUrls(cfg.thesustain_urls || {})).catch(() => setUrls({}));
  }, [open]);

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div style={{ position: "fixed", inset: 0, background: "rgba(5,8,26,0.72)", backdropFilter: "blur(10px)", zIndex: 3000, display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}
      onClick={onClose} data-testid="thesustain-modal-overlay">
      <div style={{ background: "linear-gradient(135deg, rgba(20,35,70,0.94), rgba(11,31,58,0.97))", border: "1px solid rgba(222, 194, 163,0.3)", borderRadius: 22, width: "100%", maxWidth: 460, padding: 24, boxShadow: "0 24px 80px rgba(0,0,0,0.45)" }}
        onClick={(e) => e.stopPropagation()} data-testid="thesustain-modal">
        <div className="flex items-start justify-between mb-1">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[.14em] text-[#DEC2A3]">TheSustain</p>
            <h2 className="font-head text-lg font-semibold text-white mt-0.5">Votre espace foi</h2>
          </div>
          <button onClick={onClose} data-testid="thesustain-modal-close" className="text-white/40 hover:text-white/80"><X size={18} /></button>
        </div>
        <p className="text-white/50 text-[13px] mb-4">Chaque section ouvre thesustain.net dans un nouvel onglet.</p>

        {!urls ? (
          <div className="flex justify-center py-8"><Loader2 size={20} className="animate-spin text-white/40" /></div>
        ) : (
          <div className="grid grid-cols-2 gap-2.5">
            {TILES.map(({ key, label, desc, Icon }) => (
              <a key={key} href={urls[key] || "https://thesustain.net"} target="_blank" rel="noreferrer" data-testid={`thesustain-tile-${key}`}
                className="rounded-xl border border-white/10 bg-white/[0.03] p-3.5 hover:border-[#DEC2A3]/40 hover:bg-white/[0.06] transition-colors">
                <Icon size={18} className="text-[#DEC2A3] mb-2" />
                <p className="text-sm font-semibold text-white flex items-center gap-1">{label} <ExternalLink size={11} className="text-white/30" /></p>
                <p className="text-[11px] text-white/40 mt-0.5 leading-snug">{desc}</p>
              </a>
            ))}
          </div>
        )}

        <a href={urls?.accueil || "https://thesustain.net"} target="_blank" rel="noreferrer" data-testid="thesustain-tile-accueil"
          className="mt-3 flex items-center justify-center gap-1.5 rounded-xl border border-[#DEC2A3]/30 py-2.5 text-sm font-semibold text-[#DEC2A3] hover:bg-[#DEC2A3]/10">
          Ouvrir thesustain.net <ExternalLink size={13} />
        </a>
      </div>
    </div>,
    document.body,
  );
}

export default TheSustainModal;
