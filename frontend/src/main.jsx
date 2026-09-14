import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import "./index.css";
import App from "./App.jsx";

import { AuthProvider } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";

import Landing, { PublicHeader, UnifiedFooter } from "@/pages/LandingHub";
import WPSiteSettings from "@/components/WPSiteSettings";
import MyExtensionAI from "@/pages/MyExtensionAI";
import Vision from "@/pages/Vision";
import AntiBurnout from "@/pages/AntiBurnout";
import Echeances from "@/pages/Echeances";
import InstanceDediee from "@/pages/InstanceDediee";
import ExpansionAgent from "@/pages/ExpansionAgent";
import TesterSonProjet from "@/pages/TesterSonProjet";
import ValiderSonProjet from "@/pages/ValiderSonProjet";
import PublicBoutique from "@/pages/PublicBoutique";
import Apropos from "@/pages/Apropos";
import Blog from "@/pages/Blog";
import CreationEntreprise from "@/pages/CreationEntreprise";
import Tarifs from "@/pages/Tarifs";
import Contact from "@/pages/Contact";
import FAQ from "@/pages/FAQ";
import SimulateursHub from "@/pages/SimulateursHub";
import NosServices from "@/pages/NosServices";
import ServiceTunnel from "@/pages/ServiceTunnel";
import Avantages from "@/pages/Avantages";
import Temoignages from "@/pages/Temoignages";
import VisionBoardPublic from "@/pages/VisionBoardPublic";
import WordPressPage from "@/pages/WordPressPage";
import LegacyPreview from "@/components/LegacyPreview";
import CGV from "@/pages/legal/CGV";
import ConditionsUtilisation from "@/pages/legal/ConditionsUtilisation";
import Confidentialite from "@/pages/legal/Confidentialite";
import LivraisonRetours from "@/pages/legal/LivraisonRetours";
import MentionsLegales from "@/pages/legal/MentionsLegales";

// Auto-detect basename so the same build works:
//  - in production (zayado.net) → basename = "/"
//  - in Emergent preview (/api/preview-site/) → basename = "/api/preview-site"
const __preview_prefix = "/api/preview-site";
const __basename = typeof window !== "undefined"
  && window.location.pathname.startsWith(__preview_prefix)
  ? __preview_prefix
  : "/";

function PublicApp() {
  return (
    <HelmetProvider>
      <WPSiteSettings />
      <BrowserRouter basename={__basename}>
        <ThemeProvider>
          <AuthProvider>
            <Routes>
              <Route path="/" element={<Landing />} />

              {/* SaaS landings + conversion tunnels */}
              <Route path="/myextension-ai" element={<MyExtensionAI />} />
              <Route path="/vision" element={<Vision />} />
              <Route path="/anti-burnout" element={<AntiBurnout />} />
              <Route path="/echeances" element={<Echeances />} />
              <Route path="/instance-dediee" element={<InstanceDediee />} />
              <Route path="/expansion-agent" element={<ExpansionAgent />} />
              <Route path="/valider-son-projet" element={<ValiderSonProjet />} />
              <Route path="/tester-son-projet" element={<TesterSonProjet />} />

              {/* SEO public pages — Création (custom React) + Simulators (legacy HTML iframed from app-main) */}
              <Route path="/creation-entreprise" element={<CreationEntreprise />} />
              <Route path="/simulateurs" element={<SimulateursHub />} />
              <Route path="/nos-services" element={<NosServices />} />
              <Route path="/avantages" element={<Avantages />} />
              <Route path="/services/finance-pilotage" element={<ServiceTunnel />} />
              <Route path="/services/gestion-administrative" element={<ServiceTunnel />} />
              <Route path="/services/creation-structuration" element={<ServiceTunnel />} />
              <Route path="/services/cession-reprise" element={<ServiceTunnel />} />
              <Route path="/simulateur-rentabilite" element={
                <LegacyPreview
                  src={`${__basename === "/" ? "" : __basename}/preview/simulateur-rentabilite.html`}
                  title="Simulateur de Rentabilité Gratuit pour Entreprise | ZAYADO"
                  description="Testez la viabilité financière de votre projet en 2 minutes. Calculez vos marges, vos prévisions de croissance et validez la rentabilité de votre future activité."
                />
              } />
              <Route path="/simulateur-statut-juridique" element={
                <LegacyPreview
                  src={`${__basename === "/" ? "" : __basename}/preview/simulateur-statut-juridique.html`}
                  title="Quel Statut Juridique Choisir ? Simulateur Gratuit | ZAYADO"
                  description="SASU, EURL, Auto-entrepreneur ? Répondez à quelques questions et découvrez instantanément le statut idéal pour optimiser vos impôts et protéger votre patrimoine."
                />
              } />
              <Route path="/analyse-sante-financiere" element={
                <LegacyPreview
                  src={`${__basename === "/" ? "" : __basename}/preview/analyse-financiere.html`}
                  title="Analyse Santé Financière Gratuite pour Entreprise | ZAYADO"
                  description="Diagnostiquez la santé financière de votre activité : rentabilité, endettement, solvabilité. Recevez votre rapport gratuit en 2 minutes."
                />
              } />

              {/* Aliases /fr/... → same components for FR-prefixed SEO URLs */}
              <Route path="/fr/creation-entreprise" element={<CreationEntreprise />} />
              <Route path="/fr/simulateurs" element={<SimulateursHub />} />
              <Route path="/fr/nos-services" element={<NosServices />} />
              <Route path="/fr/avantages" element={<Avantages />} />
              <Route path="/fr/simulateur-rentabilite" element={
                <LegacyPreview
                  src={`${__basename === "/" ? "" : __basename}/preview/simulateur-rentabilite.html`}
                  title="Simulateur de Rentabilité Gratuit pour Entreprise | ZAYADO"
                  description="Testez la viabilité financière de votre projet en 2 minutes. Calculez vos marges, vos prévisions de croissance et validez la rentabilité de votre future activité."
                />
              } />
              <Route path="/fr/simulateur-statut-juridique" element={
                <LegacyPreview
                  src={`${__basename === "/" ? "" : __basename}/preview/simulateur-statut-juridique.html`}
                  title="Quel Statut Juridique Choisir ? Simulateur Gratuit | ZAYADO"
                  description="SASU, EURL, Auto-entrepreneur ? Répondez à quelques questions et découvrez instantanément le statut idéal pour optimiser vos impôts et protéger votre patrimoine."
                />
              } />
              <Route path="/fr/analyse-sante-financiere" element={
                <LegacyPreview
                  src={`${__basename === "/" ? "" : __basename}/preview/analyse-financiere.html`}
                  title="Analyse Santé Financière Gratuite pour Entreprise | ZAYADO"
                  description="Diagnostiquez la santé financière de votre activité : rentabilité, endettement, solvabilité. Recevez votre rapport gratuit en 2 minutes."
                />
              } />

              {/* Pages publiques avec le header/footer de LandingHub */}
              <Route path="/a-propos" element={
                <div className="min-h-screen flex flex-col" style={{ background: "var(--zayado-cream)" }}>
                  <PublicHeader />
                  <main className="flex-1"><Apropos /></main>
                  <UnifiedFooter />
                </div>
              } />
              <Route path="/blog" element={
                <div className="min-h-screen flex flex-col" style={{ background: "var(--zayado-cream)" }}>
                  <PublicHeader />
                  <main className="flex-1"><Blog /></main>
                  <UnifiedFooter />
                </div>
              } />
              <Route path="/blog/:slug" element={
                <div className="min-h-screen flex flex-col" style={{ background: "var(--zayado-cream)" }}>
                  <PublicHeader />
                  <main className="flex-1"><Blog /></main>
                  <UnifiedFooter />
                </div>
              } />

              {/* PublicBoutique is the Kiabi-style shop wrapper (header + nav + footer) */}
              <Route path="/boutique" element={<PublicBoutique />} />
              <Route path="/boutique/recherche" element={<PublicBoutique />} />
              <Route path="/boutique/:slug" element={<PublicBoutique />} />
              <Route path="/shop" element={<PublicBoutique />} />
              <Route path="/shop/recherche" element={<PublicBoutique />} />
              <Route path="/shop/selection" element={<PublicBoutique />} />
              <Route path="/shop/:slug" element={<PublicBoutique />} />
              <Route path="/favoris" element={<PublicBoutique />} />
              <Route path="/panier" element={<PublicBoutique />} />
              <Route path="/checkout" element={<PublicBoutique />} />
              <Route path="/contact" element={
                <div className="min-h-screen flex flex-col" style={{ background: "var(--zayado-cream)" }}>
                  <PublicHeader />
                  <main className="flex-1"><Contact /></main>
                  <UnifiedFooter />
                </div>
              } />
              <Route path="/faq" element={
                <div className="min-h-screen flex flex-col" style={{ background: "var(--zayado-cream)" }}>
                  <PublicHeader />
                  <main className="flex-1"><FAQ /></main>
                  <UnifiedFooter />
                </div>
              } />
              <Route path="/tarifs" element={<Tarifs />} />
              <Route path="/fr/tarifs" element={<Tarifs />} />
              <Route path="/compte" element={<PublicBoutique />} />
              <Route path="/compte/commandes" element={<PublicBoutique />} />
              <Route path="/compte/profil" element={<PublicBoutique />} />
              <Route path="/compte/preferences" element={<PublicBoutique />} />

              {/* Legacy pages — same wrapper, distinct page content */}
              <Route path="/roadmap" element={<PublicBoutique />} />
              <Route path="/services-pro" element={<PublicBoutique />} />
              <Route path="/partenaires" element={<PublicBoutique />} />
              <Route path="/partenaires/recherche" element={<PublicBoutique />} />
              <Route path="/devenir-partenaire" element={<PublicBoutique />} />
              <Route path="/equipe" element={<PublicBoutique />} />
              <Route path="/groupement" element={<PublicBoutique />} />

              {/* Legal pages — own layout */}
              <Route path="/legal/cgv" element={<CGV />} />
              <Route path="/legal/conditions-utilisation" element={<ConditionsUtilisation />} />
              <Route path="/legal/confidentialite" element={<Confidentialite />} />
              <Route path="/legal/livraison-retours" element={<LivraisonRetours />} />
              <Route path="/legal/mentions-legales" element={<MentionsLegales />} />

              {/* WordPress catch-all — n'importe quelle page WP publiée */}
              <Route path="/wp/:slug" element={<WordPressPage />} />
              <Route path="/page/:slug" element={<WordPressPage />} />
              <Route path="/vision-board" element={<VisionBoardPublic />} />
              {/* Témoignages page CACHÉE (demande user) — pas de route publique */}

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    </HelmetProvider>  );
}

// Sur le domaine de prévisualisation Emergent, on force le cockpit SaaS
// (l'étude UX porte sur l'app, pas le site public). En production, le split
// d'origine par hostname reste actif.
const isAppHost = typeof window !== "undefined"
  && (/(^|\.)app\.zayado\.net$/i.test(window.location.hostname)
      || /\.preview\.emergentagent\.com$/i.test(window.location.hostname)
      || window.location.hostname === "localhost");

/* ─────────────────────────────────────────────────────────────────────────
 * Filet de sécurité anti-écran-blanc.
 *
 * Sans limite d'erreur au-dessus de la racine, la moindre exception pendant
 * un rendu fait démonter tout l'arbre par React : l'utilisateur se retrouve
 * face à une page entièrement blanche, sans message, sans moyen de savoir
 * quoi faire. C'est exactement ce qui se produisait sur app.zayado.net.
 *
 * Ce composant garantit qu'une panne reste lisible et récupérable : on
 * explique ce qui se passe, on propose de recharger, et on conserve le
 * détail technique replié pour le support.
 * ──────────────────────────────────────────────────────────────────────── */
class RootErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // Trace conservée pour le support ; jamais affichée telle quelle en grand.
    console.error("[Zayado] Erreur non rattrapée :", error, info?.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div style={{
        minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
        background: "#FDFBF6", padding: 24, fontFamily: "Inter, system-ui, sans-serif", color: "#0B1B3A",
      }}>
        <div style={{
          maxWidth: 520, width: "100%", background: "#fff", border: "1px solid #E8E2D8",
          borderRadius: 20, padding: "32px 28px", boxShadow: "0 10px 40px rgba(11,27,58,.08)",
        }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>La page n'a pas pu s'afficher</h1>
          <p style={{ fontSize: 14, lineHeight: 1.6, color: "#5C6472", marginTop: 10 }}>
            Un incident technique a interrompu le chargement. Vos données ne sont pas perdues.
            Rechargez la page : dans la plupart des cas, cela suffit.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 20 }}>
            <button
              onClick={() => window.location.reload()}
              style={{ background: "#0B1B3A", color: "#fff", border: "none", borderRadius: 999, padding: "11px 20px", fontSize: 14, fontWeight: 600, cursor: "pointer" }}
            >
              Recharger la page
            </button>
            <button
              onClick={() => { window.location.href = "/"; }}
              style={{ background: "transparent", color: "#0B1B3A", border: "1px solid #D9D2C6", borderRadius: 999, padding: "11px 20px", fontSize: 14, fontWeight: 600, cursor: "pointer" }}
            >
              Revenir à l'accueil
            </button>
          </div>
          <p style={{ fontSize: 12.5, color: "#8A8578", marginTop: 20 }}>
            Si le problème persiste, écrivez à <a href="mailto:support@zayado.net" style={{ color: "#0B1B3A" }}>support@zayado.net</a> en
            copiant le détail ci-dessous.
          </p>
          <details style={{ marginTop: 12 }}>
            <summary style={{ fontSize: 12.5, color: "#8A8578", cursor: "pointer" }}>Détail technique</summary>
            <pre style={{ fontSize: 11, whiteSpace: "pre-wrap", color: "#8A8578", marginTop: 8, maxHeight: 180, overflow: "auto" }}>
              {String(this.state.error?.stack || this.state.error?.message || this.state.error)}
            </pre>
          </details>
        </div>
      </div>
    );
  }
}

// Le loader de index.html s'appuyait sur root.children.length > 1, condition
// jamais vraie une fois React monté : on le retire explicitement ici.
if (typeof document !== "undefined") {
  const bootLoader = document.getElementById("boot-loader");
  if (bootLoader) bootLoader.remove();
  window.__ZAYADO_MOUNTED__ = true;
}

// ── Préview Emergent : session démo automatique ─────────────────────────
// Sur le domaine de prévisualisation uniquement, on ouvre automatiquement le
// compte test « Thomas » (déjà peuplé) s'il n'y a pas de session. Cela permet
// d'étudier l'UX du cockpit sans friction. N'a AUCUN effet en production.
async function ensurePreviewSession() {
  try {
    const isPreview = typeof window !== "undefined"
      && /\.preview\.emergentagent\.com$/i.test(window.location.hostname);
    if (!isPreview) return;
    if (localStorage.getItem("cours_auth_token")) return;
    const r = await fetch("/api/auth/demo-login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "thomas@zayado.fr" }),
    });
    if (r.ok) {
      const d = await r.json();
      if (d && d.access_token) localStorage.setItem("cours_auth_token", d.access_token);
    }
  } catch { /* noop — l'app affichera simplement l'écran de connexion */ }
}

// Session démo bornée à 2s : on tente d'obtenir le jeton AVANT le rendu (pour
// que la garde de session le voie), mais on ne bloque JAMAIS l'affichage au-delà
// de 2s — sinon un réseau lent laisserait un écran vide. Passé ce délai, on rend
// quand même (l'app affichera l'écran de connexion, jamais une page blanche).
function renderApp() {
  ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
      <RootErrorBoundary>
        {isAppHost ? <App /> : <PublicApp />}
      </RootErrorBoundary>
    </React.StrictMode>
  );
}

Promise.race([
  ensurePreviewSession(),
  new Promise((resolve) => setTimeout(resolve, 2000)),
]).finally(renderApp);
