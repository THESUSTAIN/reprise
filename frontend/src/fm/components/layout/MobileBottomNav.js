import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { LayoutGrid, Briefcase, Sparkles, Zap, Plus, X, Eye, BarChart3, TrendingUp, Heart, Settings as SettingsIcon, ShieldCheck, Globe } from "lucide-react";
import { useAuth } from "@fm/context/AuthContext";

/**
 * MobileBottomNav — barre de navigation bas mobile (md:hidden).
 *
 * Design strictement repris de app-main.zip :
 *   - background: linear-gradient(180deg, #0F1E3C 0%, #152F5C 100%)
 *   - indicateur actif (gold) #E5D5A2 en haut de l'onglet
 *   - bouton central "Collab" plus prominent (cercle accent gold)
 *
 * 5 onglets : Dashboard | Mon espace | Collab (centre) | Énergie | Plus
 * Le bouton "Plus" ouvre une feuille contenant : Vision, Missions, Pilotage,
 * Croissance, Bien-être, Réglages.
 */
export default function MobileBottomNav({ onOpenCollab, onOpenEspace }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [plusOpen, setPlusOpen] = useState(false);

  const isOn = (path) => location.pathname === path || (path !== "/" && location.pathname.startsWith(path));

  // 5 tabs : 4 réguliers + 1 central "Collab" prominent.
  const tabs = [
    { key: "dashboard", icon: <LayoutGrid size={20} strokeWidth={1.6} />, label: "Accueil",  onClick: () => { setPlusOpen(false); navigate("/"); },              active: location.pathname === "/" },
    { key: "espace",    icon: <Briefcase size={20} strokeWidth={1.6} />,  label: "Espace",   onClick: () => { setPlusOpen(false); navigate("/espace"); },         active: isOn("/espace") },
    { key: "collab",    icon: <Sparkles size={22} strokeWidth={1.8} color="#E5D5A2" />, label: "Collab.", onClick: () => { setPlusOpen(false); onOpenCollab ? onOpenCollab() : navigate("/"); }, active: false, center: true },
    { key: "pilotage",  icon: <BarChart3 size={20} strokeWidth={1.6} />,  label: "Pilotage", onClick: () => { setPlusOpen(false); navigate("/pilotage"); },       active: isOn("/pilotage") },
    { key: "plus",      icon: <Plus size={20} strokeWidth={1.6} />,        label: "Plus",     onClick: () => setPlusOpen((v) => !v),                              active: plusOpen },
  ];

  // Items dans la feuille "Plus" — organisés par catégorie (style menu complet).
  const plusGroups = [
    {
      title: "Mon activité",
      items: [
        { icon: <LayoutGrid size={18} strokeWidth={1.8} />, label: "Vue d'ensemble",       path: "/" },
        { icon: <BarChart3 size={18} strokeWidth={1.8} />,  label: "Pilotage financier",   path: "/pilotage" },
        { icon: <Briefcase size={18} strokeWidth={1.8} />,  label: "Espace de travail",    path: "/espace" },
        { icon: <Eye size={18} strokeWidth={1.8} />,        label: "Idées & opportunités", path: "/vision" },
        { icon: <Zap size={18} strokeWidth={1.8} />,        label: "Mon énergie",          path: "/bien-etre" },
      ],
    },
    {
      title: "Acquérir des clients",
      items: [
        { icon: <TrendingUp size={18} strokeWidth={1.8} />, label: "Lancement clients", path: "/croissance" },
        { icon: <Sparkles size={18} strokeWidth={1.8} />,        label: "Agent commercial IA", path: "/croissance?tab=agent" },
      ],
    },
    {
      title: "Services Zayado",
      items: [
        { icon: <Heart size={18} strokeWidth={1.8} />,      label: "Groupement",         path: "/groupement" },
        { icon: <Globe size={18} strokeWidth={1.8} />,      label: "Boutique bien-être", path: "/bien-etre#boutique" },
        ...(user?.is_admin ? [
          { icon: <ShieldCheck size={18} strokeWidth={1.8} />, label: "Admin",     path: "/admin" },
          { icon: <Globe size={18} strokeWidth={1.8} />,        label: "WordPress", path: "/wordpress" },
        ] : []),
      ],
    },
    {
      title: "Compte",
      items: [
        { icon: <SettingsIcon size={18} strokeWidth={1.8} />, label: "Réglages",     path: "/settings" },
        { icon: <Globe size={18} strokeWidth={1.8} />,        label: "Intégrations", path: "/integrations" },
      ],
    },
  ];

  return (
    <>
      <nav
        data-testid="mobile-bottom-nav"
        className="fixed bottom-0 left-0 right-0 z-50 md:hidden"
        style={{
          background: "#F6F3EE",
          borderTop: "1px solid rgba(0,0,0,0.06)",
          paddingBottom: "env(safe-area-inset-bottom)",
        }}
      >
        <div className="flex items-stretch" style={{ height: 64 }}>
          {tabs.map((t) => {
            if (t.center) {
              return (
                <button
                  key={t.key}
                  data-testid={`mbnav-${t.key}`}
                  onClick={t.onClick}
                  className="flex-1 flex flex-col items-center justify-center relative"
                  style={{ background: "transparent", border: "none", cursor: "pointer", padding: "4px 4px" }}
                >
                  <div
                    style={{
                      width: 48, height: 48, borderRadius: "50%",
                      background: "linear-gradient(135deg, #1A3A6E 0%, #0F1E3C 100%)",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      boxShadow: "0 6px 16px rgba(15,30,60,0.32), 0 0 0 4px #F6F3EE",
                      marginTop: -22,
                      color: "#E5D5A2",
                    }}
                  >
                    {t.icon}
                  </div>
                  <span style={{ fontSize: 11, fontWeight: 600, color: "#1A3A6E", marginTop: 4 }}>{t.label}</span>
                </button>
              );
            }
            return (
              <button
                key={t.key}
                data-testid={`mbnav-${t.key}`}
                onClick={t.onClick}
                style={{
                  flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 3,
                  background: "transparent", border: "none", cursor: "pointer",
                  color: t.active ? "#1A3A6E" : "#7a7368",
                  padding: "8px 4px",
                  position: "relative",
                  minHeight: 64,
                }}
              >
                <span>{t.icon}</span>
                <span style={{ fontSize: 11, fontWeight: t.active ? 600 : 500 }}>{t.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Sheet "Plus" */}
      {plusOpen && (
        <div
          className="fixed inset-0 z-[60] md:hidden"
          onClick={() => setPlusOpen(false)}
          data-testid="mbnav-plus-sheet"
        >
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
          <div
            onClick={(e) => e.stopPropagation()}
            className="absolute left-0 right-0 bottom-0 rounded-t-3xl overflow-hidden flex flex-col"
            style={{
              background: "#F6F3EE",
              maxHeight: "85vh",
              paddingBottom: "env(safe-area-inset-bottom)",
              boxShadow: "0 -8px 32px rgba(0,0,0,0.18)",
              animation: "slide-up-mobile 0.22s ease-out",
            }}
          >
            <div className="flex items-center justify-between px-6 pt-5 pb-3">
              <h3 className="text-[26px]" style={{ color: "#1F2937", fontFamily: "'DM Serif Display', Georgia, serif" }}>Menu</h3>
              <button
                onClick={() => setPlusOpen(false)}
                data-testid="mbnav-plus-close"
                className="w-9 h-9 rounded-full flex items-center justify-center hover:bg-black/5"
                style={{ color: "#1F2937" }}
              >
                <X size={20} strokeWidth={1.6} />
              </button>
            </div>
            <div className="border-t border-[#E8E2D8]" />
            <div className="overflow-y-auto px-6 py-5 space-y-6">
              {plusGroups.map((group) => (
                <div key={group.title}>
                  <p className="text-[11px] uppercase tracking-[0.18em] font-semibold mb-3" style={{ color: "#9CA3AF" }}>
                    {group.title}
                  </p>
                  <ul className="space-y-1">
                    {group.items.map((it) => (
                      <li key={it.path + it.label}>
                        <button
                          data-testid={`mbnav-plus-${it.label.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z]+/g, "-")}`}
                          onClick={() => { setPlusOpen(false); navigate(it.path); }}
                          className="w-full flex items-center gap-4 py-3 hover:bg-black/5 rounded-lg px-2 transition-colors"
                          style={{ color: "#1F2937" }}
                        >
                          <span style={{ color: "#6B7280" }}>{it.icon}</span>
                          <span style={{ fontSize: 15, fontWeight: 500 }}>{it.label}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
          <style>{`
            @keyframes slide-up-mobile {
              from { transform: translateY(100%); }
              to { transform: translateY(0); }
            }
          `}</style>
        </div>
      )}
    </>
  );
}
