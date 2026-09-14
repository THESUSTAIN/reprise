import React, { useEffect, useState } from "react";
import "./App.css";
import "./app-cockpit.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, Outlet } from "react-router-dom";
import { Toaster } from "sonner";
import Layout from "./components/Layout";
import CampusLayout from "./components/CampusLayout";
import ChatPanel from "./components/ChatPanel";
import Pilotage from "./pages/Pilotage";
import Roadmap from "./pages/Roadmap";
import Agents from "./pages/Agents";
import Croissance from "./pages/Croissance";
import Travail from "./pages/Travail";
import Login from "./pages/Login";
// Cette page était référencée par la route /login-boutique sans jamais être
// importée : au rendu de <Routes>, l'identifiant LoginBoutique déclenchait un
// ReferenceError DANS le corps de App(), donc AU-DESSUS de AppErrorBoundary.
// Aucune limite d'erreur ne pouvait l'attraper : React démontait tout l'arbre
// et le navigateur affichait une page blanche sur app.zayado.net.
import LoginBoutique from "./pages/LoginBoutique";
import Onboarding from "./pages/Onboarding";
// Espace vendeur marketplace : rendu hors du <Layout /> sombre, il a son
// propre habillage clair (un vendeur juge ses photos sur fond blanc).
import EspaceVendeur from "./pages/EspaceVendeur";
import AdminModeration from "./pages/AdminModeration";
import VisionBoard from "./pages/VisionBoard";
import BienEtre from "./pages/BienEtre";
import Aujourdhui from "./pages/Aujourdhui";
import Contexte from "./pages/Contexte";
import Collaborateur from "./pages/Collaborateur";
import TheSustain from "./pages/TheSustain";
import CampusComingSoon from "./pages/CampusComingSoon";
import { authMe } from "./lib/api";
// Note : les pages publiques (Landing, Boutique, Blog, pages légales, etc.)
// vivent dans main.jsx → PublicApp, le vrai point d'entrée chargé par
// index.html pour tout domaine ≠ app.zayado.net. App.jsx ne sert QUE le
// cockpit SaaS (chargé quand isAppHost est vrai) — les dupliquer ici créait
// de la confusion sans utilité, elles ont été retirées.

// Accueil : "Aujourd'hui", porte d'entree quotidienne Cap Vivant (tache #21 —
// avant : le Vision Board abstrait etait l'accueil direct, remplace ici par
// un vrai point de depart quotidien). Sur mobile, pas de panneau lateral
// possible a cette largeur : c'est le copilote qui EST l'accueil mobile,
// en plein ecran (demande explicite conservee).
function AppHome() {
  const navigate = useNavigate();
  const [isMobile, setIsMobile] = useState(() => typeof window !== "undefined" && window.innerWidth < 769);
  useEffect(() => {
    const update = () => setIsMobile(window.innerWidth < 769);
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);
  useEffect(() => {
    if (!isMobile) return undefined;
    const previousOverflow = document.body.style.overflow;
    const previousOverscroll = document.documentElement.style.overscrollBehavior;
    document.body.style.overflow = "hidden";
    document.documentElement.style.overscrollBehavior = "none";
    return () => {
      document.body.style.overflow = previousOverflow;
      document.documentElement.style.overscrollBehavior = previousOverscroll;
    };
  }, [isMobile]);
  if (isMobile) {
    return (
      <div className="fixed inset-0 z-[150] overflow-hidden overscroll-none bg-[#0B1F3A]" data-testid="mobile-copilot-home">
        <ChatPanel
          context="Accueil quotidien Cap Vivant."
          onMenu={() => window.dispatchEvent(new CustomEvent("cours:open-mobile-nav"))}
        />
      </div>
    );
  }
  return <Aujourdhui />;
}

// TheSustain est une entrée volontaire réservée aux comptes liés à

// l’association. Une valeur absente ou une session inconnue vaut toujours
// « non-membre » : le module n’est pas exposé par un lien direct.
function TheSustainAccess() {
  const [checking, setChecking] = useState(true);
  const [allowed, setAllowed] = useState(false);
  useEffect(() => {
    authMe()
      .then((user) => setAllowed(Boolean(user?.thesustain_member)))
      .catch(() => setAllowed(false))
      .finally(() => setChecking(false));
  }, []);
  if (checking) return <div className="glass flex min-h-48 items-center justify-center text-sm text-white/60">Vérification de l’accès…</div>;
  return allowed ? <TheSustain /> : <Navigate to="/contexte" replace />;
}

// Limite d'erreur du cockpit. Elle affichait auparavant « Erreur de chargement
// V1 » suivi d'une pile d'appels brute en plein écran : incompréhensible pour
// un utilisateur, et sans aucun moyen de s'en sortir. On explique, on propose
// une sortie, et on garde le détail technique replié pour le support.
class AppErrorBoundary extends React.Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) { console.error("[Zayado cockpit]", error, info?.componentStack); }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div style={{ minHeight: "100vh", background: "#0B1F3A", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", padding: 24, fontFamily: "Inter, system-ui, sans-serif" }}>
        <div style={{ maxWidth: 520, width: "100%", background: "rgba(255,255,255,.06)", border: "1px solid rgba(255,255,255,.15)", borderRadius: 20, padding: "32px 28px" }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Cet écran n'a pas pu s'afficher</h1>
          <p style={{ fontSize: 14, lineHeight: 1.6, color: "rgba(255,255,255,.65)", marginTop: 10 }}>
            Un incident a interrompu l'affichage du cockpit. Vos données sont intactes — rien n'a été perdu ni modifié.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 20 }}>
            <button onClick={() => window.location.reload()} style={{ background: "#DEC2A3", color: "#0A1128", border: "none", borderRadius: 999, padding: "11px 20px", fontSize: 14, fontWeight: 700, cursor: "pointer" }}>Recharger</button>
            <button onClick={() => { window.location.href = "/"; }} style={{ background: "transparent", color: "#fff", border: "1px solid rgba(255,255,255,.25)", borderRadius: 999, padding: "11px 20px", fontSize: 14, fontWeight: 600, cursor: "pointer" }}>Retour à l'accueil</button>
          </div>
          <p style={{ fontSize: 12.5, color: "rgba(255,255,255,.45)", marginTop: 20 }}>
            Si cela se répète, envoyez le détail ci-dessous à <a href="mailto:support@zayado.net" style={{ color: "#DEC2A3" }}>support@zayado.net</a>.
          </p>
          <details style={{ marginTop: 12 }}>
            <summary style={{ fontSize: 12.5, color: "rgba(255,255,255,.45)", cursor: "pointer" }}>Détail technique</summary>
            <pre style={{ whiteSpace: "pre-wrap", fontSize: 11, color: "rgba(255,255,255,.45)", marginTop: 8, maxHeight: 180, overflow: "auto" }}>{String(this.state.error?.stack || this.state.error?.message || this.state.error)}</pre>
          </details>
        </div>
      </div>
    );
  }
}

/* ─────────────────────────────────────────────────────────────────────────
 * Garde de session.
 *
 * Sans elle, un visiteur déconnecté atteignait l'accueil du cockpit : chaque
 * requête repartait en 401, tous les compteurs affichaient 0, aucune action
 * ne répondait, et rien n'indiquait qu'il fallait simplement se reconnecter.
 * On vérifie donc la session AVANT d'afficher quoi que ce soit, et on renvoie
 * vers la page de connexion en mémorisant la destination voulue.
 * ──────────────────────────────────────────────────────────────────────── */
function RequireAuth() {
  const location = useLocation();
  const [etat, setEtat] = useState("verification"); // verification | ok | anonyme

  useEffect(() => {
    let annule = false;
    authMe()
      .then((user) => { if (!annule) setEtat(user ? "ok" : "anonyme"); })
      .catch(() => { if (!annule) setEtat("anonyme"); });
    return () => { annule = true; };
  }, []);

  if (etat === "verification") {
    return (
      <div style={{ minHeight: "100vh", background: "#0B1F3A", color: "#fff", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 14, fontFamily: "Inter, system-ui, sans-serif" }}>
        <div style={{ width: 34, height: 34, border: "3px solid rgba(255,255,255,.15)", borderTopColor: "#DEC2A3", borderRadius: "50%", animation: "zay-spin .8s linear infinite" }} />
        <p style={{ margin: 0, fontSize: 13.5, color: "rgba(255,255,255,.6)" }}>Vérification de votre session…</p>
        <style>{"@keyframes zay-spin{to{transform:rotate(360deg)}}"}</style>
      </div>
    );
  }

  if (etat === "anonyme") {
    try { sessionStorage.setItem("zay_redirect_after_login", location.pathname + location.search); } catch { /* noop */ }
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

function App() {
  return (
    <AppErrorBoundary><div className="App">
      <BrowserRouter>
        <Routes>
          <Route element={<RequireAuth />}>
            <Route path="/vendeur" element={<EspaceVendeur />} />
            <Route path="/admin/moderation" element={<AdminModeration />} />
          <Route element={<Layout />}>
            <Route path="/" element={<AppHome />} />
            <Route path="/vision" element={<VisionBoard />} />
            <Route path="/mouvement" element={<Travail />} />
            <Route path="/taches" element={<Travail initialView="engagements" />} />
            <Route path="/mindset" element={<BienEtre />} />
            <Route path="/contexte" element={<Contexte />} />
            <Route path="/collaborateur" element={<Collaborateur />} />
            <Route path="/thesustain" element={<TheSustainAccess />} />
            {/* Anciennes routes conservees comme alias — evite un 404 si un
                lien/favori pointe encore vers l'ancien chemin (tache #40). */}
            <Route path="/travail" element={<Travail />} />
            <Route path="/bien-etre" element={<BienEtre />} />
            <Route path="/pilotage" element={<Pilotage />} />
            <Route path="/roadmap" element={<Roadmap />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/croissance" element={<Croissance />} />
          </Route>
          <Route element={<Layout />}>
            <Route path="/campus" element={<CampusComingSoon />} />
            <Route path="/campus/entreprise" element={<CampusComingSoon />} />
            <Route path="/campus/missions" element={<CampusComingSoon />} />
            <Route path="/campus/coach" element={<CampusComingSoon />} />
            <Route path="/campus/progression" element={<CampusComingSoon />} />
            <Route path="/campus/portfolio" element={<CampusComingSoon />} />
            <Route path="/campus/alternance" element={<CampusComingSoon />} />
          </Route>
          </Route>
          {/* Routes accessibles sans session : la connexion elle-même, et
              l'onboarding qui suit immédiatement la création du compte. */}
          <Route path="/login" element={<Login />} />
          <Route path="/login-boutique" element={<LoginBoutique />} />
          <Route path="/onboarding" element={<Onboarding />} />
          {/* Filet anti-404 : une URL inconnue ramenait l'utilisateur sur une
              page vide sans explication. */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster theme="dark" position="top-right" richColors />
    </div></AppErrorBoundary>
  );
}

export default App;
