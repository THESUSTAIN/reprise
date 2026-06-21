import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Search, Bell, ChevronDown, LogOut, User, Settings, Globe, Check, Sun, Moon, MessageCircle, Flame, Link2, ShieldCheck, Globe2 } from "lucide-react";
import { NAV } from "@fm/constants/testIds";
import Logo from "@fm/components/layout/LogoIcon";
import SideNav from "@fm/components/layout/SideNav";
import { useAuth } from "@fm/context/AuthContext";
import { useI18n } from "@fm/context/I18nContext";
import { useTheme } from "@fm/context/ThemeContext";
import useIsMobile from "@fm/hooks/useIsMobile";
import { streakApi } from "@fm/lib/api";
import { ParametresModal } from "@fm/pages/Parametres";

export default function TopNav({ active = "accueil", onNavigate, onOpenChat }) {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsSection, setSettingsSection] = useState(null);
  const { user, logout } = useAuth();
  const { t, lang, setLang, languages } = useI18n();
  const { theme, toggle: toggleTheme } = useTheme();
  const menuRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useIsMobile();
  const [streak, setStreak] = useState(0);

  useEffect(() => {
    streakApi.get().then((d) => setStreak(d.streak_days || 0)).catch(() => {});
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
        setLangOpen(false);
      }
    };
    if (menuOpen || langOpen) document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [menuOpen, langOpen]);

  const firstName = user?.first_name || "";
  const currentLang = languages.find((l) => l.code === lang) || languages[0];

  const NAV_LINKS = [
    { id: "accueil", label: "Accueil", to: "/", testId: "nav-accueil-link" },
    { id: "vision", label: t("nav.vision"), to: "/vision", testId: NAV.vision },
    { id: "espace", label: "Espace de travail", to: "/espace", testId: "nav-espace-link" },
    { id: "pilotage", label: t("nav.pilotage"), to: "/pilotage", testId: NAV.pilotage },
    { id: "croissance", label: t("nav.croissance"), to: "/croissance", testId: NAV.croissance },
  ];

  // Sync active state with current URL
  const path = location.pathname;
  const activeFromPath =
    path === "/" ? "accueil" :
    path.startsWith("/vision") ? "vision" :
    path.startsWith("/espace") || path.startsWith("/missions") ? "espace" :
    path.startsWith("/pilotage") ? "pilotage" :
    path.startsWith("/croissance") ? "croissance" : active;

  return (
    <>
    <SideNav />
    <header
      className={`fixed top-0 left-0 right-0 z-40 transition-all duration-300 ${
        scrolled
          ? "border-b border-[#E8E2D8] shadow-sm"
          : "border-b border-[#E8E2D8]"
      }`}
      style={{ background: "#FFFFFF" }}
      data-testid="top-nav"
    >
      <div className="mx-auto max-w-[1400px] px-6 lg:px-10 h-[76px] flex items-center gap-10">
        <button
          data-testid={NAV.logo}
          onClick={() => navigate("/")}
          className="lg:hidden flex items-center group shrink-0"
        >
          <Logo variant="onLight" size="md" />
        </button>

        {/* Salutation utilisateur — visible uniquement sur desktop ≥lg (sidebar a déjà le logo) */}
        <div
          className="hidden lg:flex items-center"
          data-testid="topnav-user-greeting"
        >
          <span className="text-[15px] text-navy font-medium tracking-tight">
            {(() => {
              const fn = user?.first_name
                || user?.settings?.first_name
                || user?.name?.split(" ")[0]
                || (user?.email?.includes("guest") ? "Invité" : "");
              // Filtrer les valeurs résiduelles "X" ou single-char placeholders
              const clean = fn && fn.length >= 2 ? fn : "";
              return clean
                ? <>Bonjour, <span className="font-semibold">{clean}</span></>
                : <>Bonjour</>;
            })()}
          </span>
        </div>

        <nav className="hidden md:flex lg:hidden items-center gap-1 ml-2">
          {NAV_LINKS.map((link) => {
            const isActive = activeFromPath === link.id;
            return (
              <button
                key={link.id}
                data-testid={link.testId}
                onClick={() => navigate(link.to)}
                className={`relative px-4 py-2 text-[15px] font-medium transition-colors ${
                  isActive ? "text-navy" : "text-ink-soft hover:text-navy"
                }`}
              >
                {link.label}
                {isActive && (
                  <span className="absolute -bottom-[24px] left-1/2 -translate-x-1/2 w-8 h-[2px] bg-gold rounded-full" />
                )}
              </button>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <span
            data-testid="nav-streak"
            title={`Série de ${streak} jour${streak > 1 ? "s" : ""}`}
            className="hidden md:inline-flex items-center gap-1.5 px-3 h-10 rounded-full bg-white text-[#1F2937] text-[13px] font-semibold border border-[#E8E2D8] shadow-sm"
          >
            <Flame size={14} className="text-amber-500" fill="currentColor" />
            <span>{streak}</span>
          </span>
          {/* Compact streak on mobile */}
          <span
            data-testid="nav-streak-mobile"
            title={`Série de ${streak} jour${streak > 1 ? "s" : ""}`}
            className="md:hidden inline-flex items-center gap-1 px-2 h-8 rounded-full bg-white text-[#1F2937] text-[12px] font-semibold border border-[#E8E2D8] shadow-sm"
          >
            <Flame size={12} className="text-amber-500" fill="currentColor" />
            <span>{streak}</span>
          </span>
          {/* Discuter avec Zayado moved into "Mon espace" dropdown to declutter the header */}

          <button
            data-testid={NAV.search}
            aria-label="Search"
            onClick={() => {
              const q = window.prompt("Rechercher dans le Cockpit (page, mission, document…) :");
              if (!q) return;
              const target = q.toLowerCase();
              if (target.includes("vision")) navigate("/vision");
              else if (target.includes("mission") || target.includes("tâche") || target.includes("processus") || target.includes("document")) navigate("/espace");
              else if (target.includes("pilot") || target.includes("ca") || target.includes("finance")) navigate("/pilotage");
              else if (target.includes("croiss") || target.includes("growth")) navigate("/croissance");
              else if (target.includes("bien") || target.includes("énergie")) navigate("/bien-etre");
              else if (target.includes("réglage") || target.includes("paramètre") || target.includes("intégration")) navigate("/settings");
              else alert(`Aucune correspondance pour "${q}". Essayez : vision, mission, pilotage, croissance, bien-être…`);
            }}
            className="w-10 h-10 grid place-items-center rounded-full hover:bg-cream-soft transition-colors text-navy"
          >
            <Search size={18} strokeWidth={1.8} />
          </button>
          <button
            data-testid={NAV.notifications}
            aria-label="Ouvrir le Collaborateur IA"
            onClick={() => onOpenChat && onOpenChat()}
            title="Ouvrir le Collaborateur IA"
            className="w-10 h-10 grid place-items-center rounded-full hover:bg-cream-soft transition-colors text-navy relative"
          >
            <Bell size={18} strokeWidth={1.8} />
            <span className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-gold ring-2 ring-cream-base" />
          </button>

          {/* Mon espace dropdown — inspired from final-main */}
          {(() => {
            // Detect env: preview (emergent) → /api/preview-site, production → https://zayado.net
            const backend = process.env.REACT_APP_BACKEND_URL || "";
            const isPreview = backend.includes("preview.emergentagent.com") || backend.includes("localhost");
            const zayadoHref = isPreview ? `${backend}/api/preview-site/` : "https://zayado.net";
            return (
              <a
                href={zayadoHref}
                target="_blank"
                rel="noopener noreferrer"
                data-testid="btn-zayado-net"
                title="Visiter le site Zayado"
                className="hidden sm:inline-flex items-center gap-1.5 px-3 h-9 md:h-10 rounded-full border border-sand-300 bg-white text-navy text-[12.5px] font-semibold hover:bg-cream-soft transition-colors"
              >
                zayado.net
              </a>
            );
          })()}
          <div className="relative" ref={menuRef}>
            <button
              data-testid={NAV.monEspace}
              onClick={() => { setMenuOpen((v) => !v); setLangOpen(false); }}
              aria-label={firstName ? `Menu de ${firstName}` : "Mon espace"}
              className="ml-1 inline-flex items-center gap-2 px-2.5 md:px-4 h-9 md:h-10 rounded-full bg-navy text-cream text-sm font-medium hover:bg-navy-bright transition-colors shadow-soft max-w-[140px] md:max-w-none"
            >
              {isMobile ? (
                <span className="font-semibold w-5 grid place-items-center">
                  {(firstName || "Z").trim().charAt(0).toUpperCase()}
                </span>
              ) : (
                <span className="truncate">{firstName || t("nav.monEspace")}</span>
              )}
              <ChevronDown size={15} strokeWidth={2} className={`shrink-0 transition-transform ${menuOpen ? "rotate-180" : ""}`} />
            </button>

            {menuOpen && !langOpen && (
              <div
                data-testid="mon-espace-menu"
                className="absolute right-0 mt-2 w-64 rounded-2xl bg-white border border-sand-200 shadow-float overflow-hidden"
              >
                <div className="px-4 py-3 border-b border-sand-200 bg-cream-soft">
                  <p className="text-[10.5px] tracking-[0.22em] uppercase text-ink-soft font-semibold">
                    {t("menu.connectedAs")}
                  </p>
                  <p className="text-[13px] text-navy font-semibold truncate mt-0.5">{user?.email}</p>
                </div>
                <button
                  onClick={() => { setMenuOpen(false); setSettingsSection("profil"); setSettingsOpen(true); }}
                  className="w-full px-4 py-2.5 text-left text-[13.5px] hover:bg-cream-soft flex items-center gap-3"
                  data-testid="menu-profile"
                >
                  <User size={15} className="text-ink-soft" />
                  <span className="flex-1">{t("menu.profile")}</span>
                </button>
                <button
                  onClick={() => { setMenuOpen(false); setSettingsSection("profil"); setSettingsOpen(true); }}
                  className="w-full px-4 py-2.5 text-left text-[13.5px] hover:bg-cream-soft flex items-center gap-3"
                  data-testid="menu-reglages"
                >
                  <Settings size={15} className="text-ink-soft" />
                  <span className="flex-1">{t("menu.settings")}</span>
                </button>
                <button
                  onClick={() => { setMenuOpen(false); setSettingsSection("integrations"); setSettingsOpen(true); }}
                  className="w-full px-4 py-2.5 text-left text-[13.5px] hover:bg-cream-soft flex items-center gap-3"
                  data-testid="menu-integrations"
                >
                  <Link2 size={15} className="text-ink-soft" />
                  <span className="flex-1">Intégrations</span>
                </button>
                {user?.is_admin && (
                  <button
                    onClick={() => { setMenuOpen(false); navigate("/admin"); }}
                    className="w-full px-4 py-2.5 text-left text-[13.5px] hover:bg-cream-soft flex items-center gap-3 border-t border-sand-200"
                    data-testid="menu-admin"
                  >
                    <ShieldCheck size={15} className="text-gold-deep" />
                    <span className="flex-1 font-semibold">Administration</span>
                  </button>
                )}
                {user?.is_admin && (
                  <button
                    onClick={() => { setMenuOpen(false); navigate("/wordpress"); }}
                    className="w-full px-4 py-2.5 text-left text-[13.5px] hover:bg-cream-soft flex items-center gap-3"
                    data-testid="menu-wordpress"
                  >
                    <Globe2 size={15} className="text-navy" />
                    <span className="flex-1 font-semibold">Site WordPress</span>
                  </button>
                )}
                <button
                  onClick={() => { setMenuOpen(false); onOpenChat?.(); }}
                  className="w-full px-4 py-2.5 text-left text-[13.5px] hover:bg-cream-soft flex items-center gap-3 border-t border-sand-200"
                  data-testid="menu-chat-zayado"
                >
                  <MessageCircle size={15} className="text-navy" />
                  <span className="flex-1">Discuter avec Zayado</span>
                </button>
                <button
                  onClick={toggleTheme}
                  className="w-full px-4 py-2.5 text-left text-[13.5px] hover:bg-cream-soft flex items-center gap-3 border-t border-sand-200"
                  data-testid="menu-theme"
                >
                  {theme === "light" ? <Moon size={15} className="text-ink-soft" /> : <Sun size={15} className="text-ink-soft" />}
                  <span className="flex-1">
                    {theme === "light" ? t("menu.darkMode") : t("menu.lightMode")}
                  </span>
                </button>
                <button
                  onClick={() => setLangOpen(true)}
                  className="w-full px-4 py-2.5 text-left text-[13.5px] hover:bg-cream-soft flex items-center gap-3"
                  data-testid="menu-language"
                >
                  <Globe size={15} className="text-ink-soft" />
                  <span className="flex-1">{t("menu.language")}</span>
                  <span className="text-[12px] text-ink-soft inline-flex items-center gap-1">
                    {currentLang.flag} {currentLang.code.toUpperCase()}
                  </span>
                </button>
                <MenuRow
                  icon={LogOut}
                  label={t("menu.logout")}
                  onClick={() => { setMenuOpen(false); logout(); }}
                  testid="menu-logout"
                  danger
                />
              </div>
            )}

            {langOpen && (
              <div
                data-testid="language-menu"
                className="absolute right-0 mt-2 w-64 rounded-2xl bg-white border border-sand-200 shadow-float overflow-hidden"
              >
                <div className="px-4 py-3 border-b border-sand-200 bg-cream-soft flex items-center gap-2">
                  <button
                    onClick={() => setLangOpen(false)}
                    className="text-[12px] text-ink-soft hover:text-navy"
                  >
                    ←
                  </button>
                  <p className="text-[12px] tracking-[0.18em] uppercase text-navy font-semibold">
                    {t("menu.language")}
                  </p>
                </div>
                {languages.map((l) => (
                  <button
                    key={l.code}
                    data-testid={`lang-${l.code}`}
                    onClick={() => { setLang(l.code); setLangOpen(false); setMenuOpen(false); }}
                    className="w-full px-4 py-2.5 text-left text-[13.5px] hover:bg-cream-soft flex items-center gap-3"
                  >
                    <span className="text-lg">{l.flag}</span>
                    <span className="flex-1 text-ink">{l.label}</span>
                    {lang === l.code && <Check size={14} className="text-gold-deep" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      <ParametresModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        initialSection={settingsSection}
      />
    </header>
    </>
  );
}

function MenuRow({ icon: Icon, label, onClick, testid, danger }) {
  return (
    <button
      onClick={onClick}
      data-testid={testid}
      className={`w-full px-4 py-2.5 text-left text-[13.5px] hover:bg-cream-soft flex items-center gap-3 ${
        danger ? "text-red-700 border-t border-sand-200" : "text-ink"
      }`}
    >
      <Icon size={15} className={danger ? "" : "text-ink-soft"} />
      {label}
    </button>
  );
}
