import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import "./index.css";
import App from "./App.jsx";

import { AuthProvider } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";

import PublicHome from "@/pages/PublicHome";
import VisionBoardPublic from "@/pages/VisionBoardPublic";

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
    <div className="public-site">
    <HelmetProvider>
      <BrowserRouter basename={__basename}>
        <ThemeProvider>
          <AuthProvider>
            <Routes>
              <Route path="/" element={<PublicHome />} />
              <Route path="/vision-board" element={<VisionBoardPublic />} />

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    </HelmetProvider>
    </div>  );
}

// Sur le domaine de prévisualisation Emergent, on force le cockpit SaaS
// (l'étude UX porte sur l'app, pas le site public). En production, le split
// d'origine par hostname reste actif.
const isAppHost = typeof window !== "undefined"
  && (/(^|\.)app\.zayado\.net$/i.test(window.location.hostname)
      || /\.preview\.emergentagent\.com$/i.test(window.location.hostname)
      || window.location.hostname === "localhost");

// ── Split site public / cockpit SaaS + garde-fou production ──────────────
const _HOST = typeof window !== "undefined" ? window.location.hostname : "";
const isProdAppHost = /(^|\.)app\.zayado\.net$/i.test(_HOST);
const isPreviewHost = /\.preview\.emergentagent\.com$/i.test(_HOST)
  || _HOST === "localhost" || _HOST === "127.0.0.1";
// Mode d'affichage en preview uniquement : "app" (cockpit Thomas) ou "public".
function previewMode() {
  try { return localStorage.getItem("zay_preview_mode") || "app"; } catch { return "app"; }
}
// Cockpit affiché : en PROD seulement sur app.zayado.net ; en PREVIEW selon le mode.
// Le compte démo « Thomas » n'est donc JAMAIS servi en production.
const showApp = isProdAppHost || (isPreviewHost && previewMode() !== "public");

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
    if (!isPreviewHost || !showApp) return; // JAMAIS en production, cockpit uniquement
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
// Barre d'outils PREVIEW uniquement (jamais rendue en production) : bascule
// entre le cockpit démo (Thomas) et le site public, pour avancer sur les deux
// sans impacter la prod.
function PreviewToolbar() {
  if (!isPreviewHost) return null;
  const mode = previewMode();
  const go = (m) => { try { localStorage.setItem("zay_preview_mode", m); } catch { /* noop */ } window.location.href = "/"; };
  const wrap = { position: "fixed", left: "50%", transform: "translateX(-50%)", bottom: 14, zIndex: 99999, display: "flex", gap: 6, background: "rgba(0,29,80,.92)", padding: 6, borderRadius: 999, boxShadow: "0 8px 24px rgba(0,29,80,.35)", fontFamily: "Poppins, system-ui, sans-serif" };
  const b = (active) => ({ border: "none", cursor: "pointer", borderRadius: 999, padding: "7px 14px", fontSize: 12.5, fontWeight: 600, color: active ? "#001d50" : "#fff", background: active ? "#fff" : "transparent" });
  return (
    <div style={wrap} data-testid="preview-toolbar">
      <button data-testid="preview-mode-app" style={b(mode !== "public")} onClick={() => go("app")}>Cockpit (Thomas)</button>
      <button data-testid="preview-mode-public" style={b(mode === "public")} onClick={() => go("public")}>Site public</button>
    </div>
  );
}

function renderApp() {
  ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
      <RootErrorBoundary>
        {showApp ? <App /> : <PublicApp />}
        <PreviewToolbar />
      </RootErrorBoundary>
    </React.StrictMode>
  );
}

Promise.race([
  ensurePreviewSession(),
  new Promise((resolve) => setTimeout(resolve, 2000)),
]).finally(renderApp);
