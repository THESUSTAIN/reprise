import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Briefcase, Zap, Sparkles, ChevronDown, ChevronUp } from "lucide-react";
import { BOTTOM } from "@fm/constants/testIds";
import { useI18n } from "@fm/context/I18nContext";

/**
 * Barre d'actions rapides flottante (desktop only).
 * Reproduit le pattern de final-main/BottomActionBar :
 *   - Toujours centrée en bas
 *   - Toggle ⌄ → réduit en petite capsule "↑ Actions rapides" au même endroit
 *   - Re-clic sur la capsule → barre redéploie
 */
export default function FloatingBottomBar({ activePanel, onOpen }) {
  const { t } = useI18n();
  const navigate = useNavigate();

  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem("zay_bottom_bar_collapsed") === "1"; } catch { return false; }
  });
  useEffect(() => {
    try { localStorage.setItem("zay_bottom_bar_collapsed", collapsed ? "1" : "0"); } catch { /* ignore */ }
  }, [collapsed]);

  // Badge rouge IA (synchronisé avec localStorage)
  const [collabUnread, setCollabUnread] = useState(() => {
    try { return localStorage.getItem("zay_collab_unread") === "1"; } catch { return false; }
  });
  useEffect(() => {
    const id = setInterval(() => {
      try {
        const v = localStorage.getItem("zay_collab_unread") === "1";
        setCollabUnread((p) => p !== v ? v : p);
      } catch { /* ignore */ }
    }, 2000);
    return () => clearInterval(id);
  }, []);

  const ACTIONS = [
    { id: "espace",        label: t("bottom.espace"),        sub: t("bottom.espaceSub"),        icon: Briefcase, testId: BOTTOM.espace,        fallbackTo: "/espace" },
    { id: "energie",       label: t("bottom.energie"),       sub: t("bottom.energieSub"),       icon: Zap,       testId: BOTTOM.energie,       fallbackTo: "/bien-etre" },
    { id: "collaborateur", label: t("bottom.collaborateur"), sub: t("bottom.collaborateurSub"), icon: Sparkles,  testId: BOTTOM.collaborateur, fallbackTo: "/croissance" },
  ];

  const handleClick = (a) => {
    if (a.id === "collaborateur") {
      try { localStorage.setItem("zay_collab_unread", "0"); } catch { /* ignore */ }
      setCollabUnread(false);
    }
    if (typeof onOpen === "function") onOpen(a.id);
    else if (a.fallbackTo) navigate(a.fallbackTo);
  };

  // ── Mode réduit : capsule "↑ Actions rapides" au centre bas ─────────────
  if (collapsed) {
    return (
      <button
        type="button"
        data-testid={BOTTOM.bar}
        onClick={() => setCollapsed(false)}
        title="Afficher les actions rapides"
        aria-label="Afficher les actions rapides"
        className="hidden md:inline-flex fixed bottom-5 left-1/2 -translate-x-1/2 z-40 items-center gap-1.5 bg-[#1F3B73]/95 backdrop-blur border border-white/10 px-3.5 py-1.5 rounded-full shadow-md hover:shadow-lg transition text-[12px] text-cream/90 hover:text-cream relative"
      >
        <ChevronUp size={14} />
        Actions rapides
        {collabUnread && (
          <span
            data-testid="bottom-bar-pastille-badge"
            className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-[#FF4D4F] ring-2 ring-[#1F3B73]"
          />
        )}
      </button>
    );
  }

  // ── Mode déployé : barre complète au centre bas ─────────────────────────
  return (
    <div
      data-testid={BOTTOM.bar}
      className="hidden md:flex fixed bottom-5 left-1/2 -translate-x-1/2 z-40 items-center gap-1 bg-[#1F3B73]/95 backdrop-blur-md border border-white/10 px-3 py-2 rounded-3xl shadow-[0_18px_40px_-12px_rgba(15,27,61,0.45)]"
    >
      {ACTIONS.map((a, idx) => {
        const Icon = a.icon;
        const isActive = activePanel === a.id;
        const showBadge = a.id === "collaborateur" && collabUnread;
        return (
          <React.Fragment key={a.id}>
            {idx > 0 && <span className="w-px h-7 bg-white/15 mx-1" />}
            <button
              type="button"
              data-testid={a.testId}
              onClick={() => handleClick(a)}
              aria-label={a.label}
              title={`${a.label} — ${a.sub}`}
              className={`relative inline-flex items-center gap-2.5 px-3 py-1.5 rounded-2xl transition text-left ${
                isActive ? "bg-white text-[#1F3B73]" : "text-cream/90 hover:bg-white/10"
              }`}
            >
              <span className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                isActive ? "bg-[#1F3B73] text-cream" : "bg-white/10 text-cream"
              }`}>
                <Icon size={15} strokeWidth={1.9} />
              </span>
              <span className="hidden lg:flex flex-col leading-tight">
                <span className="text-[12.5px] font-medium">{a.label}</span>
                <span className={`text-[10px] ${isActive ? "text-[#1F3B73]/60" : "text-cream/55"}`}>{a.sub}</span>
              </span>
              {showBadge && (
                <span
                  data-testid="bottom-bar-collab-badge"
                  aria-label="Nouveau message IA"
                  className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-[#FF4D4F] ring-2 ring-[#1F3B73]"
                />
              )}
            </button>
          </React.Fragment>
        );
      })}
      <button
        type="button"
        onClick={() => setCollapsed(true)}
        data-testid="bottom-bar-collapse"
        title="Replier"
        aria-label="Replier la barre d'actions"
        className="ml-1.5 w-7 h-7 rounded-full hover:bg-white/10 transition flex items-center justify-center text-cream/70 hover:text-cream"
      >
        <ChevronDown size={13} />
      </button>
    </div>
  );
}
