import React from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { SAAS_URL } from "@/lib/api";
import { ArrowLeft } from "lucide-react";

/**
 * Shared layout for all legal pages — required by Google OAuth verification
 * (privacy policy must be a DIFFERENT URL than home page).
 */
export default function LegalLayout({ title, lastUpdate, children, testId, path, description }) {
  return (
    <div className="min-h-screen bg-[var(--zayado-cream)]" data-testid={testId}>
      <Helmet>
        <title>{title} — Zayado</title>
        <meta name="description" content={description || `${title} de Zayado, marketplace et services pour indépendants.`} />
        {/* Pages légales : utiles aux visiteurs, sans intérêt SEO — cohérent
            avec la règle déjà appliquée sur les pages transactionnelles. */}
        <meta name="robots" content="noindex, follow" />
        {path && <link rel="canonical" href={`https://zayado.net${path}`} />}
      </Helmet>
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-[var(--zayado-border)]" data-testid="legal-header">
        <div className="max-w-[1280px] mx-auto px-4 md:px-6 py-3 flex items-center justify-between gap-4">
          <Link to="/" className="font-display italic text-xl tracking-tight shrink-0"
                style={{ fontFamily: "var(--font-serif,'DM Serif Display',serif)", color: "var(--zayado-navy)" }}
                data-testid="legal-back-home">
            Zayado
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link to="/boutique"  className="hidden sm:inline hover:opacity-70" style={{ color: "var(--zayado-text)" }}>Boutique</Link>
            <Link to="/tarifs"    className="hidden md:inline hover:opacity-70" style={{ color: "var(--zayado-text)" }}>Tarifs</Link>
            <Link to="/contact"   className="hidden md:inline hover:opacity-70" style={{ color: "var(--zayado-text)" }}>Contact</Link>
            <a href={`${SAAS_URL}/login`}
               className="px-4 py-1.5 rounded-full text-white text-sm font-medium"
               style={{ background: "var(--zayado-navy)" }}
               data-testid="legal-header-cta">
              Se connecter
            </a>
          </nav>
        </div>
      </header>
      <main className="max-w-[900px] mx-auto px-6 pb-20 pt-4">
        <h1 className="font-display text-4xl md:text-5xl mb-3"
            style={{ fontFamily: "var(--font-serif, 'DM Serif Display', serif)" }}>
          {title}
        </h1>
        {lastUpdate && (
          <p className="text-xs uppercase tracking-[0.15em] text-[var(--zayado-muted)] mb-10">
            Dernière mise à jour : {lastUpdate}
          </p>
        )}
        <article className="prose prose-zayado max-w-none text-[var(--zayado-text)] leading-relaxed">
          {children}
        </article>
      </main>
    </div>
  );
}
