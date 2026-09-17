/* Header officiel Presta-Partenaire by TheSustain (calqué sur thesustain-app.vercel.app).
   - Fond blanc, logo bleu cursive + texte "Presta-Partenaire" en bleu foncé gras
   - Nav minimaliste : Accueil / Prestataires / Mémoire / Galerie / Pasteur
   - 2 actions : "Propulsé par Zayado" (lien externe sobre) + CTA rouge "Devenir partenaire"
*/
import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { PARTNER as P, TS_LOGOS } from "../pages/partners-theme";

const NAV = [
  { to: "/partenaires", label: "Accueil" },
  { to: "/partenaires/recherche", label: "Prestataires" },
  { to: "/services-pro", label: "Services Pro" },
  { to: "/memoire", label: "Mémoire" },
  { to: "/galerie-souvenir", label: "Galerie" },
  { to: "/assistant-pasteur", label: "Pasteur" },
];

export default function TheSustainHeader() {
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 bg-white"
            style={{
              boxShadow: "0 2px 10px rgba(0,0,0,0.06)",
              fontFamily: "'Inter', system-ui, sans-serif",
            }}
            data-testid="thesustain-header">
      <div className="max-w-[1280px] mx-auto px-4 md:px-8 h-16 flex items-center justify-between gap-4">
        {/* Logo : avatar bleu cursive + texte */}
        <Link to="/partenaires" className="flex items-center gap-3"
              data-testid="thesustain-header-logo">
          <img src={TS_LOGOS.TEXT_BLUE} alt="TheSustain"
               className="h-10 md:h-11 w-auto object-contain" />
        </Link>

        {/* Nav desktop */}
        <nav className="hidden lg:flex items-center gap-8 text-[15px] font-medium">
          {NAV.map((l) => {
            const active = pathname === l.to ||
              (l.to !== "/partenaires" && pathname.startsWith(l.to));
            return (
              <Link key={l.to} to={l.to}
                    className="transition-colors"
                    style={{ color: active ? P.RED : P.TEXT_BODY }}
                    data-testid={`thesustain-nav-${l.to.split("/").pop() || "home"}`}>
                {l.label}
              </Link>
            );
          })}
        </nav>

        {/* Right utility */}
        <div className="hidden md:flex items-center gap-4">
          <a href="https://zayado.net" target="_blank" rel="noopener noreferrer"
             className="text-[11px] uppercase tracking-wider font-medium hover:underline"
             style={{ color: P.TEXT_DIM }}
             data-testid="thesustain-zayado-link">
            Propulsé par Zayado
          </a>
          <Link to="/devenir-partenaire"
                data-testid="thesustain-header-cta"
                className="inline-flex items-center px-5 py-2.5 text-sm font-bold text-white transition hover:opacity-90"
                style={{ background: P.RED, borderRadius: "8px" }}>
            Devenir partenaire
          </Link>
        </div>

        {/* Burger mobile */}
        <button onClick={() => setOpen(true)}
                className="lg:hidden p-2 rounded-md hover:bg-gray-50"
                data-testid="thesustain-burger">
          <Menu size={22} style={{ color: P.TEXT_BODY }} />
        </button>
      </div>

      {/* Drawer mobile */}
      {open && (
        <div className="fixed inset-0 z-50 bg-black/40 lg:hidden"
             onClick={() => setOpen(false)}
             data-testid="thesustain-drawer">
          <div className="absolute right-0 top-0 h-full w-[85%] max-w-sm bg-white shadow-xl flex flex-col"
               onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b"
                 style={{ borderColor: P.BORDER }}>
              <img src={TS_LOGOS.TEXT_BLUE} alt="TheSustain"
                   className="h-9 w-auto object-contain" />
              <button onClick={() => setOpen(false)}
                      className="p-2 rounded-md hover:bg-gray-100">
                <X size={20} style={{ color: P.TEXT_BODY }} />
              </button>
            </div>
            <nav className="flex-1 overflow-y-auto p-4 space-y-1">
              {NAV.map((l) => (
                <Link key={l.to} to={l.to}
                      onClick={() => setOpen(false)}
                      className="block px-3 py-3 rounded-md text-[15px] font-medium hover:bg-gray-50"
                      style={{ color: P.TEXT_BODY }}>
                  {l.label}
                </Link>
              ))}
              <Link to="/devenir-partenaire" onClick={() => setOpen(false)}
                    className="block mt-4 px-4 py-3 text-center font-bold text-white"
                    style={{ background: P.RED, borderRadius: "8px" }}>
                Devenir partenaire
              </Link>
            </nav>
            <a href="https://zayado.net" target="_blank" rel="noopener noreferrer"
               className="border-t px-4 py-3 text-[11px] uppercase tracking-wider font-medium"
               style={{ color: P.TEXT_DIM, borderColor: P.BORDER }}>
              Propulsé par Zayado
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
