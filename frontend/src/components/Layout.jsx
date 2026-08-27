import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect, useCallback, useRef } from "react";
import {
  Compass, Eye, HeartPulse, MessageCircle, Gem, Search, Bell,
  LayoutGrid, ChevronDown, Settings as SettingsIcon, HelpCircle, LogOut, X, Mail, Globe, TrendingUp, Rocket, Briefcase, GraduationCap, Sun, Moon,
} from "lucide-react";
import { toast } from "sonner";
import ChatPanel from "./ChatPanel";
import SettingsModal from "./SettingsModal";
import TheSustainModal from "./TheSustainModal";
import InstallBanner from "./InstallBanner";
import { authMe, getProfile, getHeaderMessages, getHeaderNotifications, markHeaderMessagesRead, markHeaderNotificationsRead, setLanguage, logoutSession, getNewsHistory, getLastSeenNewsId, globalSearch } from "../lib/api";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "./ui/dropdown-menu";

const ITEMS = [
  { id: "aujourdhui", label: "Hub IA", shortLabel: "Hub IA", Icon: MessageCircle, path: "/", exact: true },
  { id: "moncap", label: "Vision", shortLabel: "Vision", Icon: Eye, path: "/vision" },
  { id: "croissance", label: "Croissance", shortLabel: "Croissance", Icon: TrendingUp, path: "/croissance" },
  { id: "daf", label: "DAF IA", shortLabel: "DAF IA", Icon: Briefcase, path: "/pilotage" },
  { id: "espace", label: "Espace", shortLabel: "Espace", Icon: LayoutGrid, path: "/collaborateur" },
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
  { label: "TheSustain · Foi & vocation", path: "/thesustain", requiresTheSustain: true },
  { label: "Paramètres", action: "settings" },
];

const ECOSYSTEM_ITEMS = [
  { id: "collaborateur", label: "Collaborateur", path: "/collaborateur", Icon: Compass, available: true },
  { id: "campus", label: "Campus", path: "/campus", Icon: GraduationCap, available: true },
  { id: "business", label: "Équiper mon business", path: "https://zayado.net/boutique", Icon: Gem, available: true, external: true },
  { id: "espace", label: "Espace", path: "https://espace.zayado.net", Icon: Briefcase, available: true, external: true },
  { id: "thesustain", label: "TheSustain · Foi & vocation", path: "/thesustain", Icon: Eye, available: true, requiresTheSustain: true },
];

/* ─────────────── Sidebar (rail 96px, modèle exact) ─────────────── */
function Sidebar({ onSettings, onCopilote }) {
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
    if (item.action === "open-kairos") return onCopilote();
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
              const Icon = item.Icon;
              return (
                <li key={item.id} className={`w-full flex justify-center ${MENU_GROUP_STARTS.has(item.id) ? "menu-group-start" : ""}`}>
                  <button onClick={() => onItemClick(item)} data-testid={`side-${item.id}`} aria-label={item.label}
                    className={`menu-link group relative w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200 ${active ? "active" : ""} ${item.action ? "menu-link-action" : ""}`}>
                    <Icon size={16} strokeWidth={1.85} />
                    <span className={`menu-tooltip pointer-events-none absolute left-full ml-3 top-1/2 -translate-y-1/2 whitespace-nowrap rounded-md text-white text-xs px-2.5 py-1.5 transition-opacity z-50 ${scrolling ? "!opacity-0" : "opacity-0 group-hover:opacity-100"}`}>
                      {item.label}
                    </span>
                  </button>
                </li>
              );
            })}
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
function Header({ onSettings, profileName, theSustainMember, ambianceFoi, onOpenTheSustain, onOpenCopilot }) {
  const navigate = useNavigate();
  const [searchOpen, setSearchOpen] = useState(false);
  const [q, setQ] = useState("");
  const [headerMessages, setHeaderMessages] = useState([]);
  const [headerNotifications, setHeaderNotifications] = useState([]);
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
    Promise.all([getHeaderMessages(headerSession), getHeaderNotifications(headerSession)])
      .then(([messages, notifications]) => { setHeaderMessages(messages?.items || []); setHeaderNotifications(notifications?.items || []); })
      .catch(() => {});
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
        <button className="header-icon-btn header-icon-badge" title="Notifications — ouvre le chat" aria-label="Notifications" data-testid="header-notifications-btn"
          onClick={() => { onOpenCopilot?.(); markHeaderNotificationsRead(headerSession).then(() => setHeaderNotifications((items) => items.map((item) => ({ ...item, unread: false })))).catch(() => {}); }}>
          <Bell size={18} />{headerNotifications.filter((item) => item.unread).length > 0 && <span className="header-badge">{headerNotifications.filter((item) => item.unread).length}</span>}
        </button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="header-icon-btn" title="Modules" data-testid="header-apps-btn"><LayoutGrid size={18} /></button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="ecosystem-menu w-72 border-white/15 p-3 text-white">
            <DropdownMenuLabel className="ecosystem-menu-title px-1 pb-2 text-[11px] uppercase tracking-[0.18em] text-white/65">Écosystème MyExtension AI</DropdownMenuLabel>
            <div className="ecosystem-grid grid grid-cols-2 gap-2">
              {ECOSYSTEM_ITEMS.filter((item) => !item.requiresTheSustain || theSustainMember || ambianceFoi).map((item) => {
                const Icon = item.Icon;
                return <button key={item.id} type="button" data-testid={`ecosystem-${item.id}`} onClick={() => { if (item.id === "thesustain") { onOpenTheSustain(); return; } if (item.available && item.external) window.open(item.path, "_blank", "noopener,noreferrer"); else if (item.available) navigate(item.path); else toast.info(`${item.label} sera disponible dans le prochain lot.`); }} className={`ecosystem-card flex flex-col items-center justify-center gap-1.5 rounded-xl border border-white/10 p-3 text-center ${item.available ? "" : "is-disabled"}`}><span className="ecosystem-card-icon"><Icon size={19} /></span><span className="ecosystem-card-label text-[11px] font-medium leading-tight">{item.label}</span></button>;
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
                <div className="min-w-0"><p className="text-sm font-semibold">{profileName || "Mon compte"}</p><p className="text-xs text-white/50">Espace personnel</p></div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-white/10" />
            <DropdownMenuItem className="cursor-pointer" data-testid="profile-parametres" onClick={() => onSettings()}>
              <SettingsIcon className="w-4 h-4 mr-2" /> Paramètres
            </DropdownMenuItem>
            <DropdownMenuItem className="cursor-pointer" onClick={() => toast.info("Aide & support bientôt disponible.")}>
              <HelpCircle className="w-4 h-4 mr-2" /> Aide & Support
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
              <Search size={16} className="text-white/40" />
              <input autoFocus value={q} onChange={(e) => setQ(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && results[0] && go(results[0])}
                placeholder="Aller à…" data-testid="global-search-input"
                className="flex-1 bg-transparent border-none outline-none text-[15px] text-white placeholder:text-white/40" />
              <kbd className="text-[11px] text-white/40 border border-white/15 rounded px-1.5">Esc</kbd>
            </div>
            <div className="border-t border-white/10 mt-1 pt-1">
              {results.map((r) => (
                <button key={r.id || r.path || r.action} onClick={() => go(r)} data-testid={`search-result-${r.label}`}
                  className="block w-full text-left px-3 py-2 rounded-lg text-sm text-white/85 hover:bg-white/10 transition-colors">
                  {r.label}{r.type && <span className="ml-2 text-[11px] text-white/35">{r.type}</span>}
                </button>
              ))}
              {results.length === 0 && <p className="px-3 py-2 text-[13px] text-white/40">Aucun résultat.</p>}
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
  const isActive = (item) => item.action
    ? location.pathname === "/"
    : (item.exact ? location.pathname === item.path : location.pathname.startsWith(item.path));
  return (
    <nav className="bottom-nav" data-testid="bottom-nav">
      {ITEMS.map((item) => (
        <button key={item.id} className={`relative ${isActive(item) ? "active" : ""}`} data-testid={`bottomnav-${item.id}`}
          onClick={() => (item.action ? (location.pathname === "/" ? navigate("/") : onCopilote()) : navigate(item.path))}>
          {item.action && hasUnseenNews && <span className="absolute right-2 top-1 h-2 w-2 rounded-full bg-red-500" data-testid="bottomnav-news-badge" />}
          <item.Icon size={17} strokeWidth={1.8} />
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
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  useEffect(() => {
    const update = () => setIsMobile(window.innerWidth < 769);
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);
  // Le chat plein écran (accueil mobile) est trop à l'étroit avec le header
  // (58px) + la bottom nav (72px) autour ("le chat est petit") — on les
  // masque sur cette seule route/largeur et on les remplace par une feuille
  // de nav légère ouverte depuis la petite barre du chat (voir App.js).
  const hideChromeForMobileChat = isMobile && location.pathname === "/";
  useEffect(() => {
    const onOpenMobileNav = () => setMobileNavOpen(true);
    window.addEventListener("cours:open-mobile-nav", onOpenMobileNav);
    return () => window.removeEventListener("cours:open-mobile-nav", onOpenMobileNav);
  }, []);
  useEffect(() => { setMobileNavOpen(false); }, [location.pathname]);

  // Bug d'audit : Vision (VisionBoard.jsx) et Bien-être émettent déjà
  // "cours:open-copilot" ("Transformer en action", "Parler au copilote")
  // mais rien ne l'écoutait — les boutons ne faisaient rien.
  useEffect(() => {
    setCopilotOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const onOpenCopilot = (e) => {
      setCopilotAsk(e.detail?.ask || null);
      if (window.innerWidth < 769) { navigate("/"); setCopilotOpen(false); }
      else setCopilotOpen(true);
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
  const [hasUnseenNews, setHasUnseenNews] = useState(false);
  // Corrigé : ne marque plus l'actualité comme "vue" à la simple ouverture
  // du chat (mobile ou PC) — seulement quand l'utilisateur clique
  // vraiment sur l'onglet Actualité dans ChatPanel.jsx (markNewsTabSeen).
  // Ce useEffect se redéclenche à l'ouverture/fermeture du chat pour
  // refléter ce que ChatPanel a marqué de son côté (état non partagé
  // entre les deux composants) — couvre aussi le calcul initial au montage.
  useEffect(() => {
    Promise.all([getNewsHistory().catch(() => ({ items: [] })), getLastSeenNewsId().catch(() => null)])
      .then(([history, lastSeen]) => {
        const items = Array.isArray(history?.items) ? history.items : [];
        const latest = items[0]?.id || null;
        setHasUnseenNews(Boolean(latest) && latest !== lastSeen);
      });
  }, [copilotOpen, location.pathname]);
  
  useEffect(() => {
    getProfile().then((profile) => setProfileName(profile?.first_name || "")).catch(() => setProfileName(""));
  }, [settingsOpen]);
  useEffect(() => {
    authMe().then((user) => {
      setTheSustainMember(Boolean(user?.thesustain_member));
      setAmbianceFoi((user?.settings || {}).ambiance === "foi");
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
    if (window.innerWidth < 769) { navigate("/"); setCopilotOpen(false); }
    else setCopilotOpen(true);
  };
  const baseContext = {
    "/": "Vision de l'entrepreneur: objectifs, alignement, mindset.",
    "/vision": "Vision de l'entrepreneur: objectifs, alignement, mindset.",
    "/pilotage": "Pilotage financier: trésorerie, factures, dépenses.",
    "/bien-etre": "Bien-être et énergie: focus, rituels, mindset anti-abandon.",
  }[location.pathname] || "";
  const context = visionContext?.label && (location.pathname === "/" || location.pathname === "/vision")
    ? `${baseContext} Onglet Vision actif : ${visionContext.label}. Aide l’utilisateur à choisir une seule prochaine action.`
    : baseContext;

  return (
    <div className="App layout-left" data-testid="app-root">
      <div className="sky-bg" />
      <Sidebar onSettings={openSettings} onCopilote={openCopilot} />

      <div className="app-body">
        {!hideChromeForMobileChat && (
          <Header onSettings={openSettings} profileName={profileName} theSustainMember={theSustainMember} ambianceFoi={ambianceFoi} onOpenTheSustain={() => setTheSustainModalOpen(true)} onOpenCopilot={openCopilot} />
        )}
        <div className="flex">
          <main className={`flex-1 min-w-0 w-full px-4 sm:px-8 pb-28 xl:pb-8 max-w-none transition-[padding] duration-300 ${copilotOpen ? "md:pr-[396px]" : ""}`}>
            <Outlet />
          </main>
          <button
            type="button"
            onClick={() => setCopilotOpen((open) => !open)}
            className={`hidden md:flex fixed top-1/2 z-[70] -translate-y-1/2 items-center gap-2 rounded-l-2xl border border-r-0 border-white/20 bg-white/[0.10] px-3 py-3 text-sm font-semibold text-white shadow-2xl backdrop-blur-xl transition-[right] duration-200 ${copilotOpen ? "right-[380px]" : "right-0"}`}
            aria-label={copilotOpen ? "Replier le Copilote" : "Déplier le Copilote"}
            title={copilotOpen ? "Replier le Copilote" : "Déplier le Copilote"}
            data-testid="copilot-drawer-toggle"
          >
            {hasUnseenNews && <span className="absolute -left-1 top-1 h-2.5 w-2.5 rounded-full bg-red-500" data-testid="copilot-news-badge" title="Nouvelle actualité" />}
            <span className="[writing-mode:vertical-rl] rotate-180 tracking-wide">Copilote</span>
          </button>
          <aside className={`hidden md:flex fixed right-0 top-0 z-[60] h-screen w-[380px] shrink-0 border-l border-white/20 bg-white/[0.08] backdrop-blur-xl shadow-2xl transition-transform duration-300 ${copilotOpen ? "translate-x-0" : "translate-x-full"}`} data-testid="copilot-right-drawer">
            <ChatPanel context={context} initialAsk={copilotAsk} />
          </aside>
        </div>
        <BottomNav onCopilote={openCopilot} hasUnseenNews={hasUnseenNews} />
      </div>

      {mobileNavOpen && (
        <div className="fixed inset-0 z-[90] flex items-end md:hidden" onClick={() => setMobileNavOpen(false)} data-testid="mobile-nav-sheet">
          <div className="absolute inset-0 bg-black/60" />
          <div className="relative w-full rounded-t-2xl border-t border-white/15 bg-[#0B1F3A] pb-[env(safe-area-inset-bottom)]" onClick={(e) => e.stopPropagation()}>
            <div className="mx-auto mt-2 h-1 w-10 rounded-full bg-white/20" />
            <ul className="grid grid-cols-4 gap-1 px-4 py-4">
              {ITEMS.map((item) => (
                <li key={item.id}>
                  <button onClick={() => { navigate(item.path); setMobileNavOpen(false); }} className="flex w-full flex-col items-center gap-1.5 rounded-xl px-2 py-3 text-white/80 hover:bg-white/10" data-testid={`mobile-nav-${item.id}`}>
                    <item.Icon size={18} />
                    <span className="text-[11px] leading-tight text-center">{item.shortLabel || item.label}</span>
                  </button>
                </li>
              ))}
              <li>
                <button onClick={() => { openSettings(); setMobileNavOpen(false); }} className="flex w-full flex-col items-center gap-1.5 rounded-xl px-2 py-3 text-white/80 hover:bg-white/10" data-testid="mobile-nav-settings">
                  <SettingsIcon size={18} />
                  <span className="text-[11px] leading-tight text-center">Paramètres</span>
                </button>
              </li>
            </ul>
          </div>
        </div>
      )}

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} initialSection={settingsSection} />
      <TheSustainModal open={theSustainModalOpen} onClose={() => setTheSustainModalOpen(false)} />
      <InstallBanner />
    </div>
  );
}
