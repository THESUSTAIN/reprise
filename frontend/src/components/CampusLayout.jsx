import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  BarChart3, BookOpenCheck, BriefcaseBusiness, Building2, Compass,
  GraduationCap, Moon, Sparkles, Sun, UserRound,
} from "lucide-react";
import { getProfile } from "../lib/api";

const CAMPUS_ITEMS = [
  { id: "today", label: "Aujourd’hui", short: "Aujourd’hui", path: "/campus", exact: true, Icon: Compass },
  { id: "enterprise", label: "Mon entreprise", short: "Entreprise", path: "/campus/entreprise", Icon: Building2 },
  { id: "missions", label: "Missions", short: "Missions", path: "/campus/missions", Icon: BriefcaseBusiness },
  { id: "coach", label: "Coach IA", short: "Coach", path: "/campus/coach", Icon: Sparkles },
  { id: "progress", label: "Progression", short: "Progrès", path: "/campus/progression", Icon: BarChart3 },
  { id: "portfolio", label: "Portfolio", short: "Portfolio", path: "/campus/portfolio", Icon: BookOpenCheck },
  { id: "alternance", label: "Alternance", short: "Alternance", path: "/campus/alternance", Icon: GraduationCap },
];

function isCurrent(item, pathname) {
  return item.exact ? pathname === item.path : pathname.startsWith(item.path);
}

export default function CampusLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [isLight, setIsLight] = useState(() => document.documentElement.classList.contains("ambiance-clarte"));
  const [profileName, setProfileName] = useState("");

  useEffect(() => { getProfile().then((profile) => setProfileName(profile?.first_name || "")).catch(() => setProfileName("")); }, []);

  const toggleTheme = () => {
    const next = !isLight;
    document.documentElement.classList.toggle("ambiance-clarte", next);
    setIsLight(next);
    try {
      const raw = JSON.parse(localStorage.getItem("cours-main-settings-preferences") || "{}");
      localStorage.setItem("cours-main-settings-preferences", JSON.stringify({ ...raw, ambiance: next ? "clarte" : "sens" }));
    } catch { /* aucune préférence persistante disponible */ }
  };

  return (
    <div className="min-h-screen bg-[#081734] text-white" data-testid="campus-app-root">
      {/* Fond harmonisé sur .sky-bg (index.css) — Campus avait son propre
          dégradé (#071330/#05081a), jamais utilisé ailleurs dans l'app,
          construit indépendamment du shell partagé. */}
      <div className="fixed inset-0 -z-10" aria-hidden="true" style={{
        background: `
          radial-gradient(ellipse at 20% 10%, rgba(45,81,150,0.45) 0%, transparent 50%),
          radial-gradient(ellipse at 80% 8%, rgba(30,60,110,0.35) 0%, transparent 55%),
          linear-gradient(180deg, #172C5C 0%, #101F47 42%, #0B1F3A 76%, #081734 100%)
        `,
      }} />

      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[104px] flex-col items-center border-r border-white/10 bg-[#0B1F3A]/70 px-3 py-5 backdrop-blur-xl md:flex" data-testid="campus-sidebar">
        <button onClick={() => navigate("/")} className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/20 bg-white/[.08]" aria-label="Retour à MyExtension Business">
          <img src="/logo-zayado.png" alt="MyExtension Campus" className="h-8 w-8 object-contain" />
        </button>
        <div className="mt-3 text-center"><p className="text-[9px] font-bold uppercase tracking-[.18em] text-[#F1E2CC]">Campus</p><p className="mt-1 text-[9px] leading-tight text-white/45">Pratique & progrès</p></div>
        <nav className="mt-8 flex w-full flex-1 flex-col items-center gap-2" aria-label="Navigation Campus">
          {CAMPUS_ITEMS.map((item) => {
            const Icon = item.Icon;
            const active = isCurrent(item, location.pathname);
            return <button key={item.id} onClick={() => navigate(item.path)} title={item.label} data-testid={`campus-side-${item.id}`} className={`group relative flex h-10 w-10 items-center justify-center rounded-xl transition-all duration-200 ${active ? "bg-[#DEC2A3] text-[#0A1128] shadow-[0_8px_22px_rgba(222, 194, 163,.22)]" : "text-white/60 hover:bg-white/[.08] hover:text-white"}`}><Icon size={17} /><span className="pointer-events-none absolute left-full ml-3 whitespace-nowrap rounded-md border border-white/15 bg-[#0B1F3A] px-2.5 py-1.5 text-xs text-white opacity-0 shadow-xl transition-opacity group-hover:opacity-100">{item.label}</span></button>;
          })}
        </nav>
      </aside>

      <div className="md:pl-[104px]">
        <header className="sticky top-0 z-30 flex min-h-[70px] items-center justify-between gap-3 border-b border-white/10 bg-[#0B1F3A]/35 px-4 py-3 backdrop-blur-xl sm:px-7" data-testid="campus-header">
          <div className="flex min-w-0 items-center gap-3">
            <button onClick={() => navigate("/campus")} className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/15 bg-white/[.06] md:hidden" aria-label="Accueil Campus"><GraduationCap size={18} className="text-[#F1E2CC]" /></button>
            <div className="min-w-0"><p className="text-[10px] font-semibold uppercase tracking-[.16em] text-[#F1E2CC]">MyExtension</p><p className="font-head text-base font-semibold text-white">Campus</p></div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={toggleTheme} className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/15 bg-white/[.05] text-white/75 transition-colors hover:bg-white/[.10]" title="Changer de thème" aria-label="Changer de thème">{isLight ? <Moon size={17} /> : <Sun size={17} />}</button>
            <span className="flex h-9 min-w-9 items-center justify-center rounded-xl border border-white/15 bg-white/[.06] px-2 text-xs font-bold text-[#F1E2CC]" title={profileName || "Mon compte"}>{profileName ? profileName.charAt(0).toUpperCase() : <UserRound size={16} />}</span>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1280px] px-4 pb-28 pt-6 sm:px-8 sm:pt-8 md:pb-10"><Outlet /></main>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-40 flex gap-1 overflow-x-auto border-t border-white/15 bg-[#0B1F3A]/95 px-2 py-2 backdrop-blur-xl md:hidden" aria-label="Navigation Campus mobile" data-testid="campus-bottom-nav">
        {CAMPUS_ITEMS.map((item) => { const Icon = item.Icon; const active = isCurrent(item, location.pathname); return <button key={item.id} onClick={() => navigate(item.path)} className={`flex min-w-[74px] flex-col items-center gap-1 rounded-xl px-2 py-1.5 text-[10px] font-medium ${active ? "bg-[#DEC2A3] text-[#0A1128]" : "text-white/65"}`}><Icon size={15} />{item.short}</button>; })}
      </nav>
    </div>
  );
}
