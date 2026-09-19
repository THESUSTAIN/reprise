/**
 * ZayadoLayout — Header + Footer partagés (style lean-journey).
 * Utilisé sur les pages "publiques" : / (Landing hub) et /myextension-ai.
 * Le menu boutique (/boutique) garde son layout dédié (TheSustainHeader).
 *
 * Les pages conversion (vision, expansion-agent, tester-son-projet)
 * sont rendues SANS ce layout (tunnel pur SEO).
 */
import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

export const ZayadoHeader = () => (
  <header className="sticky top-0 z-50 glass border-b border-outline bg-canvas/85 backdrop-blur">
    <div className="max-w-7xl mx-auto px-6 lg:px-10 h-16 flex items-center justify-between">
      <Link to="/" className="flex items-center gap-2.5" data-testid="logo-zayado">
        <div className="w-9 h-9 rounded-full bg-aubergine flex items-center justify-center">
          <div className="w-3.5 h-3.5 rounded-full border-2 border-cream" />
        </div>
        <span className="text-[19px] tracking-tight font-medium text-ink">
          Zayado<span className="text-aubergine">.</span>
        </span>
      </Link>
      <nav className="hidden md:flex items-center gap-7 text-sm text-ink/70">
        <Link to="/myextension-ai" className="hover:text-aubergine transition" data-testid="nav-myextension">MyExtension AI</Link>
        <Link to="/vision" className="hover:text-aubergine transition" data-testid="nav-vision">Vision Board</Link>
        <Link to="/expansion-agent" className="hover:text-aubergine transition" data-testid="nav-expansion">Expansion Agent</Link>
        <Link to="/boutique" className="hover:text-aubergine transition" data-testid="nav-boutique">Boutique</Link>
      </nav>
      <a
        href="https://app.zayado.net/login"
        target="_self"
        data-testid="header-cta-start"
        className="inline-flex items-center gap-2 bg-aubergine hover:bg-aubergine-deep text-cream px-4 py-2 rounded-full text-sm transition-colors"
      >
        Commencer
        <ArrowRight className="w-4 h-4" />
      </a>
    </div>
  </header>
);

export const ZayadoFooter = () => (
  <footer className="py-10 border-t border-outline bg-canvas">
    <div className="max-w-7xl mx-auto px-6 lg:px-10 flex flex-wrap items-center justify-between gap-4 text-xs text-inkMuted">
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded-full bg-aubergine flex items-center justify-center">
          <div className="w-2 h-2 rounded-full border border-cream" />
        </div>
        © {new Date().getFullYear()} Zayado — entreprendre, sans rester seul.
      </div>
      <div className="flex flex-wrap gap-5">
        <Link to="/legal/mentions-legales" className="hover:text-aubergine">Mentions légales</Link>
        <Link to="/legal/confidentialite" className="hover:text-aubergine">Confidentialité</Link>
        <Link to="/legal/conditions-utilisation" className="hover:text-aubergine">CGU</Link>
        <Link to="/contact" className="hover:text-aubergine">Contact</Link>
      </div>
    </div>
  </footer>
);

export default function ZayadoLayout({ children }) {
  return (
    <div className="min-h-screen bg-canvas flex flex-col">
      <ZayadoHeader />
      <main className="flex-1">{children}</main>
      <ZayadoFooter />
    </div>
  );
}
