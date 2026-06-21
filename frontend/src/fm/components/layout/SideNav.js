import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Home,
  Eye,
  Briefcase,
  LineChart,
  TrendingUp,
  Heart,
  Layers,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import Logo from "@fm/components/layout/LogoIcon";
import { useAuth } from "@fm/context/AuthContext";

/**
 * SideNav — Sidebar gauche style Zayado bleu.
 *  - 6 items principaux + séparateur + Cockpit Hub
 *  - Collapse 64px (icônes only) ↔ Expanded 220px
 *  - Flèche collapse sur le bord droit
 */
const NAV_ITEMS = [
  { id: "accueil", icon: Home, label: "Accueil", to: "/" },
  { id: "vision", icon: Eye, label: "Vision", to: "/vision" },
  { id: "espace", icon: Briefcase, label: "Mon espace", to: "/espace" },
  { id: "pilotage", icon: LineChart, label: "Pilotage", to: "/pilotage" },
  { id: "croissance", icon: TrendingUp, label: "Croissance", to: "/croissance" },
  { id: "bien-etre", icon: Heart, label: "Bien-être", to: "/bien-etre" },
];

export default function SideNav() {
  const navigate = useNavigate();
  const location = useLocation();

  const [pinned, setPinned] = useState(() => {
    try { return localStorage.getItem("zay_sidenav_expanded") === "1"; } catch { return false; }
  });
  const [hovered, setHovered] = useState(false);
  const expanded = pinned || hovered;

  useEffect(() => {
    try { localStorage.setItem("zay_sidenav_expanded", pinned ? "1" : "0"); } catch { /* ignore */ }
  }, [pinned]);

  // Push page content right on desktop — basé sur 'pinned' uniquement (sinon le contenu sauterait au hover)
  useEffect(() => {
    const apply = () => {
      const isDesktop = window.innerWidth >= 1024;
      document.body.classList.toggle("has-sidenav", isDesktop && !pinned);
      document.body.classList.toggle("has-sidenav-expanded", isDesktop && pinned);
    };
    apply();
    window.addEventListener("resize", apply);
    return () => {
      window.removeEventListener("resize", apply);
      document.body.classList.remove("has-sidenav", "has-sidenav-expanded");
    };
  }, [pinned]);

  const isActive = (to) => {
    if (to === "/") return location.pathname === "/";
    return location.pathname.startsWith(to);
  };

  const width = expanded ? 220 : 64;

  return (
    <aside
      data-testid="sidenav"
      aria-label="Navigation principale"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="hidden lg:flex fixed top-0 left-0 bottom-0 z-40 flex-col transition-[width] duration-200 ease-out"
      style={{
        width,
        background: "linear-gradient(180deg, #2A4A8E 0%, #1F3B73 38%, #14275C 72%, #0F1E50 100%)",
        boxShadow: hovered && !pinned ? "8px 0 24px -6px rgba(15,27,61,0.38)" : "2px 0 16px -4px rgba(15,27,61,0.28)",
      }}
    >
      {/* Logo en haut */}
      <button
        type="button"
        onClick={() => navigate("/")}
        data-testid="sidenav-logo"
        className={`h-[76px] flex items-center transition-all ${
          expanded ? "px-4 justify-start" : "px-0 justify-center"
        } hover:bg-white/5`}
        aria-label="Accueil"
      >
        {expanded ? (
          <Logo variant="onDark" size="md" testid="sidenav-logo-full" />
        ) : (
          <Logo variant="onDark" size="md" showWordmark={false} testid="sidenav-logo-icon" />
        )}
      </button>

      <div className="h-px bg-white/10 mx-3" />

      {/* Nav items */}
      <nav className="flex-1 px-2 pt-3 overflow-y-auto" data-testid="sidenav-items">
        {NAV_ITEMS.map((item) => (
          <SideItem
            key={item.id}
            item={item}
            active={isActive(item.to)}
            expanded={expanded}
            onClick={() => navigate(item.to)}
          />
        ))}

        {/* Séparateur — services optionnels */}
        <div className="my-3 mx-2 h-px bg-white/10" />

        <SideItem
          item={{ id: "hub", icon: Layers, label: "Cockpit Hub", to: "/hub" }}
          active={isActive("/hub")}
          expanded={expanded}
          onClick={() => navigate("/hub")}
          eyebrow={expanded ? "À venir" : undefined}
        />
      </nav>

      {/* Bottom — carte essai + user pill (visible uniquement en mode expanded) */}
      {expanded && (
        <SideBottom navigate={navigate} />
      )}

      {/* Collapse arrow */}
      <button
        type="button"
        data-testid="sidenav-collapse-btn"
        onClick={() => setPinned((v) => !v)}
        aria-label={pinned ? "Détacher la navigation" : "Épingler la navigation"}
        className="absolute top-1/2 -right-3 -translate-y-1/2 w-6 h-12 grid place-items-center rounded-r-md bg-[#1E3A8A] hover:bg-[#2A4A8E] text-cream shadow-md border border-white/10 transition"
      >
        {pinned ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
      </button>
    </aside>
  );
}

function SideItem({ item, active, expanded, onClick, eyebrow }) {
  const Icon = item.icon;
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={`sidenav-${item.id}`}
      title={!expanded ? item.label : undefined}
      className={`relative w-full flex items-center gap-3 mb-1 rounded-lg transition-colors text-left ${
        expanded ? "px-3 py-2.5" : "px-0 py-2.5 justify-center"
      } ${
        active
          ? "bg-white/15 text-white"
          : "text-white/70 hover:bg-white/8 hover:text-white"
      }`}
    >
      {active && (
        <span
          className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-r-md bg-white"
          aria-hidden
        />
      )}
      <span className="shrink-0">
        <Icon size={18} strokeWidth={1.8} />
      </span>
      {expanded && (
        <span className="flex flex-col items-start min-w-0">
          <span className="text-[13.5px] font-medium tracking-tight whitespace-nowrap">
            {item.label}
          </span>
          {eyebrow && (
            <span className="text-[10px] text-white/45 tracking-[0.12em] uppercase whitespace-nowrap">
              {eyebrow}
            </span>
          )}
        </span>
      )}
    </button>
  );
}

function SideBottom({ navigate }) {
  const { user } = useAuth();
  const isPaid = user?.plan && ["start", "grow", "serenity", "business"].includes((user.plan || "").toLowerCase());
  const firstName = user?.first_name || user?.settings?.first_name || "";
  const lastName = user?.last_name || user?.settings?.last_name || "";
  const initials = ((firstName[0] || "") + (lastName[0] || "")).toUpperCase() || (user?.email || "?")[0].toUpperCase();
  const planLabel = user?.plan ? user.plan.charAt(0).toUpperCase() + user.plan.slice(1) : "Découverte";

  return (
    <div className="px-3 pb-3 pt-2 space-y-2">
      {!isPaid && (
        <div className="rounded-xl bg-white/8 border border-white/10 p-3" data-testid="sidenav-trial-card">
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-cream mb-1">
            <Sparkles size={11} className="text-gold" /> Démarrez votre essai
          </div>
          <p className="text-[11px] text-white/65 leading-relaxed mb-2.5">
            7 jours gratuits sur le Plan Start — sans engagement, sans CB.
          </p>
          <button
            type="button"
            onClick={() => navigate("/tarifs")}
            data-testid="sidenav-trial-cta"
            className="w-full inline-flex items-center justify-center px-3 py-1.5 rounded-md bg-gold text-navy text-[11.5px] font-semibold hover:bg-gold-deep transition"
          >
            Activer mon essai
          </button>
        </div>
      )}

      <button
        type="button"
        onClick={() => navigate("/settings?section=profile")}
        data-testid="sidenav-user-pill"
        className="w-full flex items-center gap-2.5 px-2 py-2 rounded-lg hover:bg-white/8 transition text-left"
      >
        <span className="w-8 h-8 rounded-full bg-white/15 text-cream text-[11px] font-semibold grid place-items-center shrink-0">
          {initials}
        </span>
        <span className="flex-1 min-w-0">
          <span className="block text-[12px] text-cream font-medium truncate">
            {firstName && lastName ? `${firstName} ${lastName}` : firstName || user?.email?.split("@")[0] || "Mon profil"}
          </span>
          <span className="block text-[10px] text-white/55 truncate">
            Plan {planLabel}
          </span>
        </span>
        <ChevronRight size={12} className="text-white/40 shrink-0" />
      </button>
    </div>
  );
}
