import { NavLink, Outlet, useLocation, useNavigate, Navigate } from "react-router-dom";
import { useState, useEffect, useCallback, useRef } from "react";
import {
  Compass, Eye, HeartPulse, MessageCircle, Gem, Search, Bell, Gauge,
  LayoutGrid, LayoutDashboard, ListChecks, Handshake, ChevronDown, Settings as SettingsIcon, HelpCircle, LogOut, X, Mail, Globe, TrendingUp, Rocket, Briefcase, GraduationCap, Sun, Moon, Map, Bot,
} from "lucide-react";
import { toast } from "sonner";
import ChatPanel from "./ChatPanel";
import SettingsModal from "./SettingsModal";
import TheSustainModal from "./TheSustainModal";
import InstallBanner from "./InstallBanner";
import WelcomeTour from "./WelcomeTour";
import { authMe, getProfile, getHeaderMessages, getHeaderNotifications, markHeaderMessagesRead, markHeaderNotificationsRead, setLanguage, logoutSession, getNewsHistory, getLastSeenNewsId, globalSearch } from "../lib/api";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "./ui/dropdown-menu";

// Navigation principale — refondue.
//
// Avant : « Hub IA · Vision · Croissance · DAF IA · Espace ».
//   • « Espace » portait une icône de grille et ouvrait en réalité la page
//     Collaborateur : ni le nom ni l'icône ne disaient où l'on allait.
//   • « Mon Mouvement » — l'exécution, le cœur quotidien du produit —
//     n'était accessible par AUCUNE entrée de menu.
//   • Le Copilote, argument central du produit, n'avait pas d'entrée non plus.
//
// Maintenant : l'exécution entre, le Copilote prend la place centrale
// surélevée (le geste réflexe des applications mobiles), le pilotage
// financier rejoint le menu profil où se trouvent déjà les autres modules.
const ITEMS = [
  { id: "aujourdhui", label: "Aujourd'hui", shortLabel: "Aujourd'hui", sub: "Votre journée en un coup d'œil", Icon: LayoutDashboard, path: "/", exact: true },
  { id: "moncap", label: "Vision", shortLabel: "Vision", sub: "Cap & décisions", Icon: Eye, path: "/vision" },
  { id: "copilote", label: "Copilote", shortLabel: "Copilote", sub: "L'IA prépare, vous décidez", Icon: MessageCircle, action: "copilot", center: true },
  { id: "mouvement", label: "Mon Mouvement", shortLabel: "Mouvement", sub: "Tâches & projets", Icon: ListChecks, path: "/mouvement" },
  { id: "croissance", label: "Croissance", shortLabel: "Croissance", sub: "Prospects & ventes", Icon: TrendingUp, path: "/croissance" },
];
const MENU_GROUP_STARTS = new Set(["contexte"]);

const COLLAPSE_KEY = "mx_sidebar_collapsed";
const SEARCH_TARGETS = [
  { label: "Aujourd'hui", path: "/" },
  { label: "Ma Vision", path: "/vision" },
  { label: "Mon Mouvement", path: "/mouvement" },
  { label: "Mindset & capacité", path: "/mindset" },
  { label: "Contexte (Pilotage & Croissance)", path: "/contexte" },
  { label: "Campus", path: "/campus" },
  { label: "Collaborateur", path: "/collaborateur" },
  { label: "Roadmap 30/60/90", path: "/roadmap" },
  { label: "Mes agents", path: "/agents" },
  { label: "TheSustain · Foi & vocation", path: "/thesustain", requiresTheSustain: true },
  { label: "Paramètres", action: "settings" },
];

const ECOSYSTEM_ITEMS = [
  // DAF IA quitte la navigation principale (cinq entrées maximum sur mobile)
  // mais devait rester atteignable : il manquait ici.
  { id: "pilotage", label: "DAF IA · Pilotage", sub: "Finances & trésorerie", path: "/pilotage", Icon: Briefcase, available: true },
  { id: "roadmap", label: "Roadmap 30/60/90", sub: "Plan d'action par étapes", path: "/roadmap", Icon: Map, available: true },
  { id: "agents", label: "Mes agents (WhatsApp/Telegram)", sub: "Assistants automatisés", path: "/agents", Icon: Bot, available: true },
  { id: "mindset", label: "Mindset & capacité", sub: "Énergie & anti-surcharge", path: "/mindset", Icon: HeartPulse, available: true },
  { id: "contexte", label: "Contexte", sub: "Échéances & priorités", path: "/contexte", Icon: Gauge, available: true },
  { id: "collaborateur", label: "Collaborateur", sub: "Déléguer & partager", path: "/collaborateur", Icon: Handshake, available: true },
  { id: "campus", label: "Campus", sub: "Formations & simulations", path: "/campus", Icon: GraduationCap, available: true },
  { id: "business", label: "Équiper mon business", sub: "Boutique & outils", path: "https://zayado.net/boutique", Icon: Gem, available: true, external: true },
  { id: "espace", label: "Espace", sub: "Espace membres", path: "https://espace.zayado.net", Icon: Briefcase, available: true, external: true },
  { id: "thesustain", label: "TheSustain · Foi & vocation", sub: "Foi & vocation", path: "/thesustain", Icon: Eye, available: true, requiresTheSustain: true },
];

/* ─────────────── Sidebar (rail 96px, modèle exact) ─────────────── */
function Sidebar({ onSettings, onCopilote, unseenNewsCount }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem(COLLAPSE_KEY) === "1"; } catch { return false; }
  });
  useEffect(() => {
    try { localStorage.setItem(COLLAPSE_KEY, collapsed ? "1" : "0"); } catch { /* noop */ }
  }, [collapsed]);
  const toggle = useCallback(() => setCollapsed((c) => !c), []);

  // Corrige un vrai bug : l'infobulle au survol d'une icône reste affichée
  // pendant un scroll de la page (le curseur ne bouge pas, donc :hover
  // reste actif), et vient masquer le contenu qui a défilé en dessous.
  // On force sa fermeture dès qu'un scroll se produit n'importe où.
  const [scrolling, setScrolling] = useState(false);
  useEffect(() => {
    let timeout;
    const onScroll = () => {
      setScrolling(true);
      clearTimeout(timeout);
      timeout = setTimeout(() => setScrolling(false), 150);
    };
    window.addEventListener("scroll", onScroll, { capture: true, passive: true });
    return () => { window.removeEventListener("scroll", onScroll, { capture: true }); clearTimeout(timeout); };
  }, []);

  const isActive = (item) =>
    item.path ? (item.exact ? location.pathname === "/" : location.pathname.startsWith(item.path)) : false;

  const onItemClick = (item) => {
    // "open-kairos" n'a jamais existé dans ITEMS : le test ne se déclenchait
    // jamais. L'action réelle est "copilot".
    if (item.action) return onCopilote();
    if (item.path) navigate(item.path);
  };

  return (
    <aside className={`side-nav ${collapsed ? "is-collapsed" : ""}`} data-testid="side-nav" data-collapsed={collapsed ? "1" : "0"}>
      <button type="button" onClick={toggle} className="side-logo-btn" data-testid="side-logo"
        title={collapsed ? "Ouvrir le menu" : "Replier le menu"} aria-label="Menu">
        <img src="/logo-zayado.png" alt="myextension-ai by zayado" className="side-logo-img" />
      </button>

      <button type="button" onClick={toggle} className="side-edge-strip" data-testid="side-edge-strip"
        aria-label="Ouvrir le menu" tabIndex={collapsed ? 0 : -1} />

      <div className="side-inner">
        <div className="menu-island relative w-full rounded-r-3xl py-3 px-2.5 flex items-center justify-center">
          <svg className="menu-scoop-top absolute left-0 top-[-30px] -rotate-90 pointer-events-none" width="30" height="30" viewBox="0 0 30 30" aria-hidden="true">
            <path d="M30 0H0V30C0 13.431 13.431 0 30 0Z" />
          </svg>
          <svg className="menu-scoop-bottom absolute left-0 bottom-[-30px] pointer-events-none" width="30" height="30" viewBox="0 0 30 30" aria-hidden="true">
            <path d="M30 0H0V30C0 13.431 13.431 0 30 0Z" />
          </svg>
          <ul className="relative z-10 flex flex-col items-center w-full" aria-label="Navigation principale">
            {ITEMS.map((item) => {
              const active = isActive(item);
              const Icon = item.desktopIcon || item.Icon;
              return (
                <li key={item.id} className={`w-full flex justify-center ${MENU_GROUP_STARTS.has(item.id) ? "menu-group-start" : ""}`}>
                  <button onClick={() => onItemClick(item)} data-testid={`side-${item.id}`} aria-label={item.label}
                    className={`menu-link group relative w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 ${active ? "active" : ""} ${item.action ? "menu-link-action" : ""}`}>
                    <Icon size={16} strokeWidth={1.85} />
                    {item.action === "copilot" && unseenNewsCount > 0 && (
                      <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[9px] font-bold text-white" data-testid="side-copilote-badge">{unseenNewsCount}</span>
                    )}
                    <span className={`menu-tooltip pointer-events-none absolute left-full ml-3 top-1/2 -translate-y-1/2 whitespace-nowrap rounded-md text-white text-xs px-2.5 py-1.5 transition-opacity z-50 ${scrolling ? "!opacity-0" : "opacity-0 group-hover:opacity-100"}`}>
                      <span className="block font-medium">{item.label}</span>
                      {item.sub && <span className="block text-[10px] text-white/60 leading-tight">{item.sub}</span>}
                    </span>
                  </button>
                </li>
              );
            })}
            {/* Desktop uniquement : Contexte et Mindset ont leur place dans ce rail
                (contrairement à la barre mobile plafonnée à 5 icônes) — avant,
                seul le menu Écosystème (un clic de plus) les exposait. */}
            <li className="w-full flex justify-center menu-group-start">
              <button onClick={() => navigate("/contexte")} data-testid="side-contexte" aria-label="Contexte" className={`menu-link group relative w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 ${location.pathname.startsWith("/contexte") ? "active" : ""}`}>
                <Gauge size={16} strokeWidth={1.85} />
                <span className={`menu-tooltip pointer-events-none absolute left-full ml-3 top-1/2 -translate-y-1/2 whitespace-nowrap rounded-md text-white text-xs px-2.5 py-1.5 transition-opacity z-50 ${scrolling ? "!opacity-0" : "opacity-0 group-hover:opacity-100"}`}><span className="block font-medium">Contexte</span><span className="block text-[10px] text-white/60 leading-tight">Échéances & priorités</span></span>
              </button>
            </li>
            <li className="w-full flex justify-center">
              <button onClick={() => navigate("/mindset")} data-testid="side-mindset" aria-label="Mindset & capacité" className={`menu-link group relative w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 ${location.pathname.startsWith("/mindset") ? "active" : ""}`}>
                <HeartPulse size={16} strokeWidth={1.85} />
                <span className={`menu-tooltip pointer-events-none absolute left-full ml-3 top-1/2 -translate-y-1/2 whitespace-nowrap rounded-md text-white text-xs px-2.5 py-1.5 transition-opacity z-50 ${scrolling ? "!opacity-0" : "opacity-0 group-hover:opacity-100"}`}><span className="block font-medium">Mindset & capacité</span><span className="block text-[10px] text-white/60 leading-tight">Énergie & recul</span></span>
              </button>
            </li>
          </ul>
        </div>

        <div className="side-settings-zone w-full flex items-center justify-center pt-3">
          <button onClick={() => onSettings()} data-testid="side-settings" title="Paramètres"
            className="w-9 h-9 rounded-full bg-gradient-to-br from-[#d4b78c] to-[#c4a374] flex items-center justify-center shadow-lg hover:scale-105 transition-transform">
            <Gem className="w-4 h-4 text-[#0a1f4e]" strokeWidth={2} />
          </button>
        </div>
      </div>

    </aside>
  );
}

/* ─────────────── Header (transparent, modèle exact) ─────────────── */
function Header({ onSettings, profileName, theSustainMember, ambianceFoi, onOpenTheSustain, onOpenCopilot, unseenNewsCount, headerNotifications, setHeaderNotifications }) {
  const navigate = useNavigate();
  // Corrige AUTH-03 : aucun élément de l'interface ne permettait de savoir
  // si la session provenait de Google, Microsoft, thesustain ou d'un compte
  // démo — on lit la méthode déjà mémorisée par Login.jsx à la connexion.
  const loginProviderLabel = (() => {
    const method = (() => { try { return localStorage.getItem("zayado_last_login_method"); } catch { return null; } })();
    return { google: "Connecté avec Google", microsoft: "Connecté avec Microsoft", thesustain: "Accès thesustain.net", demo: "Compte de démonstration", email: "Connecté par e-mail" }[method] || "Espace personnel";
  })();
  const [searchOpen, setSearchOpen] = useState(false);
  const [q, setQ] = useState("");
  const [headerMessages, setHeaderMessages] = useState([]);
  // headerNotifications remonté dans Layout (App shell) : le son de nouvelle
  // notification (voir plus bas dans ce fichier) en a besoin dans sa propre
  // portée, et lisait par erreur cette variable alors qu'elle n'existait que
  // dans le scope de Header — d'où le crash "headerNotifications is not
  // defined" en prod. Header reçoit maintenant la même donnée par props.
  const headerSession = "default";
  const [isLight, setIsLight] = useState(() => document.documentElement.classList.contains("ambiance-clarte"));

  const toggleTheme = () => {
    const next = !isLight;
    document.documentElement.classList.toggle("ambiance-clarte", next);
    setIsLight(next);
    // Même clé que SettingsModal (PREFERENCE_KEY), sans modifier l’univers éditorial des citations.
    try {
      const raw = JSON.parse(localStorage.getItem("cours-main-settings-preferences") || "{}");
      localStorage.setItem("cours-main-settings-preferences", JSON.stringify({ ...raw, theme: next ? "light" : "dark" }));
    } catch { /* noop */ }
  };

  useEffect(() => {
    getHeaderMessages(headerSession).then((messages) => setHeaderMessages(messages?.items || [])).catch(() => {});
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setSearchOpen(true); }
      if (e.key === "Escape") setSearchOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const [dataResults, setDataResults] = useState([]);
  useEffect(() => {
    const query = q.trim();
    if (!query) { setDataResults([]); return; }
    const handle = setTimeout(() => {
      globalSearch(query).then(setDataResults).catch(() => setDataResults([]));
    }, 250); // anti-rebond — pas un appel réseau à chaque frappe
    return () => clearTimeout(handle);
  }, [q]);
  const navResults = SEARCH_TARGETS
    .filter((s) => !s.requiresTheSustain || theSustainMember || ambianceFoi)
    .filter((s) => s.label.toLowerCase().includes(q.toLowerCase()));
  const results = [...dataResults, ...navResults];
  const go = (target) => {
    if (target.action === "settings") onSettings();
    else if (target.path) navigate(target.path);
    setSearchOpen(false); setQ("");
  };

  return (
    <header className="app-header" data-testid="app-header">
      <button type="button" className="header-mobile-brand" onClick={() => navigate("/")} aria-label="Accueil MyExtension" data-testid="header-mobile-brand">
        <img src="/logo-zayado.png" alt="myextension-ai by zayado" />
      </button>
      <div className="header-cockpit-chip" data-testid="header-mobile-cockpit-status"><Rocket size={14} /> Cockpit <span>0/8</span></div>
      <div className="header-search" data-testid="header-search" onClick={() => setSearchOpen(true)}>
        <Search size={16} className="header-search-icon" />
        <input type="text" placeholder="Rechercher (Cmd+K)" readOnly data-testid="header-search-input" style={{ cursor: "pointer" }} />
      </div>

      <div className="header-actions">
        <button className="header-icon-btn" title="Changer de thème" aria-label="Changer de thème" data-testid="ambiance-toggle-btn" onClick={toggleTheme}>
          {isLight ? <Moon size={18} /> : <Sun size={18} />}
        </button>
        <DropdownMenu><DropdownMenuTrigger asChild><button className="header-icon-btn header-icon-badge" title="Messages" aria-label="Messages" data-testid="header-mail-btn" onClick={() => markHeaderMessagesRead(headerSession).then(() => setHeaderMessages((items) => items.map((item) => ({ ...item, unread: false })))).catch(() => {})}><Mail size={18} />{headerMessages.filter((item) => item.unread).length > 0 && <span className="header-badge">{headerMessages.filter((item) => item.unread).length}</span>}</button></DropdownMenuTrigger><DropdownMenuContent align="end" className="w-80 bg-[#0B1F3A] border-white/15 text-white"><DropdownMenuLabel>Messages</DropdownMenuLabel><DropdownMenuSeparator className="bg-white/10" />{headerMessages.length === 0 && <div className="px-3 py-6 text-center text-xs text-white/50">Aucun message pour le moment.</div>}{headerMessages.map((item) => <DropdownMenuItem key={item.id} className="flex items-start gap-3 py-3 cursor-pointer"><div className="w-9 h-9 rounded-full gold-bg text-[#0A1128] text-xs font-semibold flex items-center justify-center">{(item.sender || "M").charAt(0).toUpperCase()}</div><div className="min-w-0"><p className="text-sm font-medium">{item.sender}</p><p className="text-xs text-white/60">{item.text}</p></div></DropdownMenuItem>)}</DropdownMenuContent></DropdownMenu>
        <DropdownMenu><DropdownMenuTrigger asChild><button className="header-icon-btn header-icon-badge" title="Notifications" aria-label="Notifications" data-testid="header-notifications-btn"
          onClick={() => markHeaderNotificationsRead(headerSession).then(() => setHeaderNotifications((items) => items.map((item) => ({ ...item, unread: false })))).catch(() => {})}>
          {/* Corrigé : le badge comptait déjà /notifications + les actualités non
              vues, mais le clic n'ouvrait jamais la liste — il filait droit vers
              le chat en marquant tout lu au passage, donc rien ne s'affichait
              jamais ici malgré le badge. Vrai dropdown maintenant, sur le
              modèle du bouton Messages juste à côté. */}
          <Bell size={18} />{(headerNotifications.filter((item) => item.unread).length + unseenNewsCount) > 0 && <span className="header-badge">{headerNotifications.filter((item) => item.unread).length + unseenNewsCount}</span>}
        </button></DropdownMenuTrigger><DropdownMenuContent align="end" className="w-80 bg-[#0B1F3A] border-white/15 text-white"><DropdownMenuLabel>Notifications</DropdownMenuLabel><DropdownMenuSeparator className="bg-white/10" />
          {unseenNewsCount > 0 && <DropdownMenuItem className="flex items-start gap-3 py-3 cursor-pointer" onClick={() => onOpenCopilot?.()}><Bell className="mt-1 h-4 w-4 shrink-0 text-[#E8C96A]" /><div className="min-w-0"><p className="text-sm font-medium">Actualité</p><p className="text-xs text-white/60">{unseenNewsCount} actualité{unseenNewsCount > 1 ? "s" : ""} non lue{unseenNewsCount > 1 ? "s" : ""}</p></div></DropdownMenuItem>}
          {headerNotifications.length === 0 && unseenNewsCount === 0 && <div className="px-3 py-6 text-center text-xs text-white/50">Aucune notification pour le moment.</div>}
          {headerNotifications.map((item) => <DropdownMenuItem key={item.id} className="flex items-start gap-3 py-3 cursor-pointer" onClick={() => { if (item.action_url) navigate(item.action_url); else onOpenCopilot?.(); }}><Bell className="mt-1 h-4 w-4 shrink-0 text-[#E8C96A]" /><div className="min-w-0"><p className="text-sm font-medium">{item.title}</p><p className="text-xs text-white/60">{item.text}</p></div></DropdownMenuItem>)}
        </DropdownMenuContent></DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="header-icon-btn" title="Modules" data-testid="header-apps-btn"><LayoutGrid size={18} /></button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="ecosystem-menu w-72 border-white/15 p-3 text-white">
            <DropdownMenuLabel className="ecosystem-menu-title px-1 pb-2 text-[11px] uppercase tracking-[0.18em] text-white/65">Écosystème MyExtension AI</DropdownMenuLabel>
            <div className="ecosystem-grid grid grid-cols-2 gap-2">
              {ECOSYSTEM_ITEMS.filter((item) => !item.requiresTheSustain || theSustainMember || ambianceFoi).map((item) => {
                const Icon = item.Icon;
                return <button key={item.id} type="button" data-testid={`ecosystem-${item.id}`} onClick={() => { if (item.id === "thesustain") { onOpenTheSustain(); return; } if (item.available && item.external) window.open(item.path, "_blank", "noopener,noreferrer"); else if (item.available) navigate(item.path); else toast.info(`${item.label} sera disponible dans le prochain lot.`); }} className={`ecosystem-card flex flex-col items-center justify-center gap-1 rounded-xl border border-white/10 p-3 text-center ${item.available ? "" : "is-disabled"}`}><span className="ecosystem-card-icon"><Icon size={19} /></span><span className="ecosystem-card-label text-[11px] font-medium leading-tight">{item.label}</span>{item.sub && <span className="ecosystem-card-sub text-[9px] text-white/55 leading-tight">{item.sub}</span>}</button>;
              })}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="header-profile" data-testid="header-profile-btn">
              <span className="header-avatar" aria-hidden="true">{(profileName || "M").trim().charAt(0).toUpperCase()}</span>
              <span className="header-profile-info">
                <span className="header-profile-name">{profileName || "Mon compte"}</span>
                <span className="header-profile-role">Espace personnel</span>
              </span>
              <ChevronDown size={16} className="header-profile-chevron" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56 bg-[#0B1F3A] border-white/15 text-white">
            <DropdownMenuLabel>
              <div className="flex items-center gap-3 py-1">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#DD2A33] to-[#A81D24] text-white text-sm font-bold flex items-center justify-center">{(profileName || "M").trim().charAt(0).toUpperCase()}</div>
                <div className="min-w-0"><p className="text-sm font-semibold">{profileName || "Mon compte"}</p><p className="text-xs text-white/50" data-testid="header-login-provider">{loginProviderLabel}</p></div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-white/10" />
            <DropdownMenuItem className="cursor-pointer" data-testid="profile-parametres" onClick={() => onSettings()}>
              <SettingsIcon className="w-4 h-4 mr-2" /> Paramètres
            </DropdownMenuItem>
            <DropdownMenuItem className="cursor-pointer" data-testid="profile-contexte" onClick={() => navigate("/contexte")}>
              <Gauge className="w-4 h-4 mr-2" /> Contexte
            </DropdownMenuItem>
            <DropdownMenuItem className="cursor-pointer" data-testid="profile-revoir-guide" onClick={() => window.dispatchEvent(new CustomEvent("cours:open-tour"))}>
              <HelpCircle className="w-4 h-4 mr-2" /> Revoir le guide
            </DropdownMenuItem>
            <DropdownMenuSeparator className="bg-white/10" />
            <DropdownMenuItem className="cursor-pointer" onClick={() => setLanguage("fr").then(() => toast.success("Langue française enregistrée.")).catch(() => toast.error("Impossible d’enregistrer la langue."))}><Globe className="w-4 h-4 mr-2" /> Français</DropdownMenuItem><DropdownMenuItem className="cursor-pointer" onClick={() => setLanguage("en").then(() => toast.success("English language saved.")).catch(() => toast.error("Impossible d’enregistrer la langue."))}><Globe className="w-4 h-4 mr-2" /> English</DropdownMenuItem>
            <DropdownMenuItem className="cursor-pointer text-rose-300" onClick={() => logoutSession().then(() => { toast.success("Session déconnectée."); navigate("/login"); }).catch(() => toast.error("Impossible de fermer la session."))}>
              <LogOut className="w-4 h-4 mr-2" /> Déconnexion
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {searchOpen && (
        <div className="search-overlay" onClick={() => setSearchOpen(false)} data-testid="global-search-modal">
          <div className="search-box" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-2 px-2.5 py-2">
              <Search size={16} className="text-white/60" />
              <input autoFocus value={q} onChange={(e) => setQ(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && results[0] && go(results[0])}
                placeholder="Aller à…" data-testid="global-search-input"
                className="flex-1 bg-transparent border-none outline-none text-[15px] text-white placeholder:text-white/40" />
              <kbd className="text-[11px] text-white/60 border border-white/15 rounded px-1.5">Esc</kbd>
            </div>
            <div className="border-t border-white/10 mt-1 pt-1">
              {results.map((r) => (
                <button key={r.id || r.path || r.action} onClick={() => go(r)} data-testid={`search-result-${r.label}`}
                  className="block w-full text-left px-3 py-2 rounded-lg text-sm text-white/85 hover:bg-white/10 transition-colors">
                  {r.label}{r.type && <span className="ml-2 text-[11px] text-white/55">{r.type}</span>}
                </button>
              ))}
              {results.length === 0 && <p className="px-3 py-2 text-[13px] text-white/60">Aucun résultat.</p>}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

/* ─────────────── Bottom nav (mobile, modèle Kairos) ─────────────── */
function BottomNav({ onCopilote, hasUnseenNews }) {
  const location = useLocation();
  const navigate = useNavigate();
  // Le Copilote n'est pas une route : il ne doit jamais s'afficher comme
  // l'onglet actif (il l'était dès qu'on se trouvait sur l'accueil).
  const isActive = (item) => item.action
    ? false
    : (item.exact ? location.pathname === item.path : location.pathname.startsWith(item.path));
  return (
    <nav className="bottom-nav" data-testid="bottom-nav">
      {ITEMS.map((item) => (
        <button key={item.id} className={`relative ${item.center ? "is-center" : ""} ${isActive(item) ? "active" : ""}`} data-testid={`bottomnav-${item.id}`}
          onClick={() => (item.action ? onCopilote() : navigate(item.path))}>
          {item.action && hasUnseenNews && <span className="bottom-nav-dot" data-testid="bottomnav-news-badge" />}
          <item.Icon size={item.center ? 21 : 17} strokeWidth={1.8} />
          <span>{item.shortLabel || item.label}</span>
        </button>
      ))}
    </nav>
  );
}

/* ─────────────── PWA install prompt : voir components/InstallBanner.jsx
   (remplace l'ancien toast générique par une bannière au format natif —
   carte blanche, icône, lien d'action, cohérente avec ce que montrent
   les autres apps type Bol.com plutôt qu'une notification texte). ─────────────── */

/* ─────────────── App shell ─────────────── */
export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [copilotAsk, setCopilotAsk] = useState(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsSection, setSettingsSection] = useState("general");
  const [visionContext, setVisionContext] = useState({ tab: "accueil", label: "Accueil Vision" });
  const [isMobile, setIsMobile] = useState(() => typeof window !== "undefined" && window.innerWidth < 769);
  useEffect(() => {
    const update = () => setIsMobile(window.innerWidth < 769);
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);
  // L'accueil mobile n'est plus le chat plein écran : header et navigation
  // basse restent visibles sur toutes les routes, comme sur PC. Le Copilote
  // s'ouvre par-dessus, en plein écran, depuis la navigation basse.

  // Bug d'audit : Vision (VisionBoard.jsx) et Bien-être émettent déjà
  // "cours:open-copilot" ("Transformer en action", "Parler au copilote")
  // mais rien ne l'écoutait — les boutons ne faisaient rien.
  useEffect(() => {
    setCopilotOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const onOpenCopilot = (e) => {
      setCopilotAsk(e.detail?.ask || null);
      setCopilotOpen(true);
    };
    const onVisionContext = (e) => setVisionContext(e.detail || null);
    window.addEventListener("cours:open-copilot", onOpenCopilot);
    window.addEventListener("cours:vision-context", onVisionContext);
    return () => {
      window.removeEventListener("cours:open-copilot", onOpenCopilot);
      window.removeEventListener("cours:vision-context", onVisionContext);
    };
  }, [navigate]);
  useEffect(() => {
    const onOpenSettings = (event) => {
      setSettingsSection(event?.detail?.section || "general");
      setSettingsOpen(true);
    };
    window.addEventListener("cours:open-settings", onOpenSettings);
    return () => window.removeEventListener("cours:open-settings", onOpenSettings);
  }, []);
  const [profileName, setProfileName] = useState("");
  const [theSustainMember, setTheSustainMember] = useState(false);
  const [ambianceFoi, setAmbianceFoi] = useState(false); // choix "Foi" fait à l'onboarding — distinct de l'adhésion payante ci-dessus
  const [theSustainModalOpen, setTheSustainModalOpen] = useState(false);
  // Badge "nouvelle actualité" — compare la dernière édition disponible à la
  // dernière vue par l'utilisateur.
  const [unseenNewsCount, setUnseenNewsCount] = useState(0);
  // Remonté ici (au lieu de rester interne à Header) : l'effet "petit son"
  // plus bas dans ce même composant Layout en a besoin dans sa portée pour
  // calculer le total notifications + actualités non lues.
  const [headerNotifications, setHeaderNotifications] = useState([]);
  useEffect(() => {
    getHeaderNotifications("default").then((notifications) => setHeaderNotifications(notifications?.items || [])).catch(() => {});
  }, []);
  // Corrigé : ne marque plus l'actualité comme "vue" à la simple ouverture
  // du chat (mobile ou PC) — seulement quand l'utilisateur clique
  // vraiment sur l'onglet Actualité dans ChatPanel.jsx (markNewsTabSeen).
  // Ce useEffect se redéclenche à l'ouverture/fermeture du chat pour
  // refléter ce que ChatPanel a marqué de son côté (état non partagé
  // entre les deux composants) — couvre aussi le calcul initial au montage.
  // Transformé en vrai compte (pas juste vrai/faux) pour que la cloche du
  // header puisse afficher un nombre exact, comme le badge de l'onglet
  // Actualité — les deux lisent maintenant la même vraie source.
  useEffect(() => {
    Promise.all([getNewsHistory().catch(() => ({ items: [] })), getLastSeenNewsId().catch(() => null)])
      .then(([history, lastSeen]) => {
        const items = Array.isArray(history?.items) ? history.items : [];
        if (!items.length) { setUnseenNewsCount(0); return; }
        if (!lastSeen) { setUnseenNewsCount(items.length); return; }
        const idx = items.findIndex((item) => item.id === lastSeen);
        // Bug corrigé : si l'édition marquée "vue" n'est plus retrouvée dans la
        // liste (repli /news-history différent, id changé, édition purgée...),
        // le code traitait TOUT comme non lu à nouveau (items.length) — ce qui
        // rallumait le badge + le bip sonore à chaque changement de page tant
        // que la condition restait vraie, donnant l'impression de
        // notifications répétées sans raison. Un lastSeen existant mais
        // introuvable veut dire "déjà vu, juste hors de la fenêtre" : 0, pas
        // items.length.
        setUnseenNewsCount(idx === -1 ? 0 : idx);
      });
  }, [copilotOpen, location.pathname]);

  // Petit son quand le décompte augmente vraiment (nouvelle notification
  // pendant que l'app est ouverte) — jamais au chargement initial de la
  // page, sinon chaque rechargement "sonnerait" pour du contenu déjà vu.
  const prevNotifCountRef = useRef(null);
  useEffect(() => {
    const total = unseenNewsCount + headerNotifications.filter((item) => item.unread).length;
    if (prevNotifCountRef.current !== null && total > prevNotifCountRef.current) {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator(); const gain = ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        osc.type = "sine"; osc.frequency.value = 880;
        gain.gain.setValueAtTime(0.08, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
        osc.start(); osc.stop(ctx.currentTime + 0.25);
      } catch { /* audio non disponible (autoplay bloqué, etc.) — silencieux */ }
    }
    prevNotifCountRef.current = total;
  }, [unseenNewsCount, headerNotifications]);
  
  useEffect(() => {
    // Ne vide jamais un nom déjà affiché (par ex. déjà rempli par authMe()
    // ci-dessous, si cet appel se résout en premier) — ne définit que si
    // /prefs a vraiment un prénom à donner.
    getProfile().then((profile) => { if (profile?.first_name) setProfileName(profile.first_name); }).catch(() => {});
  }, [settingsOpen]);
  useEffect(() => {
    authMe().then((user) => {
      setTheSustainMember(Boolean(user?.thesustain_member));
      setAmbianceFoi((user?.settings || {}).ambiance === "foi");
      // Corrige AUTH-03 / DATA-01 : le nom affiché ne venait que de /prefs
      // (un magasin de préférences facultatif, souvent vide juste après une
      // connexion OAuth/thesustain/démo), jamais de l'identité réelle
      // renvoyée par /auth/me — d'où le repli permanent sur "Mon compte".
      // On complète ici avec le vrai nom du fournisseur si /prefs n'en a
      // pas donné, sans jamais écraser un prénom que l'utilisateur aurait
      // lui-même personnalisé dans ses réglages.
      setProfileName((current) => current || user?.first_name || user?.name || "");
    }).catch(() => { setTheSustainMember(false); setAmbianceFoi(false); });
  }, [settingsOpen]);

  const openSettings = (section = "general") => {
    setSettingsSection(section);
    setSettingsOpen(true);
  };
  const openCopilot = () => {
    // Ne marque plus l'actualité comme vue à la simple ouverture du chat —
    // seulement quand l'utilisateur clique vraiment sur l'onglet Actualité
    // (voir markNewsTabSeen dans ChatPanel.jsx). Sinon le compteur exact
    // tombait à 0 avant même d'avoir consulté quoi que ce soit.
    setCopilotOpen(true);
  };
  const baseContext = {
    "/": "Vision de l'entrepreneur: objectifs, alignement, mindset.",
    "/vision": "Vision de l'entrepreneur: objectifs, alignement, mindset.",
    "/pilotage": "Pilotage financier: trésorerie, factures, dépenses.",
    "/roadmap": "Roadmap 30/60/90: sprints Build-Measure-Learn générés par IA à partir du projet, du marché cible et de l'hypothèse à tester.",
    "/bien-etre": "Bien-être et énergie: focus, rituels, mindset anti-abandon.",
  }[location.pathname] || "";
  const context = visionContext?.label && (location.pathname === "/" || location.pathname === "/vision")
    ? `${baseContext} Onglet Vision actif : ${visionContext.label}. Aide l’utilisateur à choisir une seule prochaine action.`
    : baseContext;

  const hasAuthToken = typeof window !== "undefined" && localStorage.getItem("cours_auth_token");
  if (!hasAuthToken) return <Navigate to="/bienvenue" replace />;

  return (
    <div className="App layout-left" data-testid="app-root">
      <div className="sky-bg" />
      <Sidebar onSettings={openSettings} onCopilote={openCopilot} unseenNewsCount={unseenNewsCount} />

      <div className="app-body">
        <Header onSettings={openSettings} profileName={profileName} theSustainMember={theSustainMember} ambianceFoi={ambianceFoi} onOpenTheSustain={() => setTheSustainModalOpen(true)} onOpenCopilot={openCopilot} unseenNewsCount={unseenNewsCount} headerNotifications={headerNotifications} setHeaderNotifications={setHeaderNotifications} />
        <div className="flex">
          <main className={`flex-1 min-w-0 w-full px-4 sm:px-8 pb-28 xl:pb-8 max-w-none transition-[padding] duration-300 ${copilotOpen ? "md:pr-[396px]" : ""}`}>
            <Outlet />
          </main>
          {!isMobile && <button
            type="button"
            onClick={() => setCopilotOpen((open) => !open)}
            className={`hidden md:flex fixed top-1/2 z-[70] -translate-y-1/2 items-center gap-2 rounded-l-2xl border border-r-0 border-white/20 bg-white/[0.10] px-3 py-3 text-sm font-semibold text-white shadow-2xl backdrop-blur-xl transition-[right] duration-200 ${copilotOpen ? "right-[380px]" : "right-0"}`}
            aria-label={copilotOpen ? "Replier le Copilote" : "Déplier le Copilote"}
            title={copilotOpen ? "Replier le Copilote" : "Déplier le Copilote"}
            data-testid="copilot-drawer-toggle"
          >
            {unseenNewsCount > 0 && <span className="absolute -left-1 top-1 h-2.5 w-2.5 rounded-full bg-red-500" data-testid="copilot-news-badge" title="Nouvelle actualité" />}
            <span className="[writing-mode:vertical-rl] rotate-180 tracking-wide">Copilote</span>
          </button>}
          {!isMobile && (
            <aside className={`hidden md:flex fixed right-0 top-0 z-[60] h-screen w-[380px] shrink-0 border-l border-white/20 bg-white/[0.08] backdrop-blur-xl shadow-2xl transition-transform duration-300 ${copilotOpen ? "translate-x-0" : "translate-x-full"}`} data-testid="copilot-right-drawer">
              <ChatPanel context={context} initialAsk={copilotAsk} />
            </aside>
          )}
        </div>
        <BottomNav onCopilote={openCopilot} hasUnseenNews={unseenNewsCount > 0} />
      </div>

      {/* Copilote mobile : même composant, même style que le panneau PC —
          ouvert en plein écran par-dessus l'app, refermable. Avant, il
          REMPLAÇAIT l'accueil mobile, ce qui faisait disparaître le header
          et la navigation basse. */}
      {isMobile && copilotOpen && (
        <div className="fixed inset-0 z-[120] flex flex-col bg-[#0B1F3A] md:hidden" data-testid="copilot-mobile-fullscreen">
          <div className="flex items-center justify-between border-b border-white/12 px-4 py-3">
            <span className="text-sm font-semibold text-white">Copilote</span>
            <button onClick={() => setCopilotOpen(false)} aria-label="Fermer le Copilote" data-testid="copilot-mobile-close"
              className="flex h-9 w-9 items-center justify-center rounded-full border border-white/15 text-white/80">
              <X size={18} />
            </button>
          </div>
          <div className="min-h-0 flex-1"><ChatPanel context={context} initialAsk={copilotAsk} /></div>
        </div>
      )}

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} initialSection={settingsSection} />
      <TheSustainModal open={theSustainModalOpen} onClose={() => setTheSustainModalOpen(false)} />
      <InstallBanner />
      <WelcomeTour />
    </div>
  );
}
