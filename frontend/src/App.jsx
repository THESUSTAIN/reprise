import React, { useEffect, useState } from "react";
import "./App.css";
import "./app-cockpit.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation, Outlet } from "react-router-dom";
import { Toaster } from "sonner";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import LoginBoutique from "./pages/LoginBoutique";
import Onboarding from "./pages/Onboarding";
import EspaceVendeur from "./pages/EspaceVendeur";
import AdminModeration from "./pages/AdminModeration";
import VisionBoard from "./pages/VisionBoard";
import MaVision from "./pages/MaVision";
import Aujourdhui from "./pages/Aujourdhui";
import { authMe } from "./lib/api";

// Accueil : "Aujourd'hui" — identique sur mobile et PC. La navigation basse
// reste visible partout ; le Copilote s'ouvre par-dessus en plein écran
// depuis la nav (jamais comme page d'accueil).
function AppHome() {
  return <Aujourdhui />;
}

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

// Garde de session : on vérifie la session AVANT d'afficher quoi que ce soit,
// et on renvoie vers la connexion en mémorisant la destination voulue.
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

// Refonte en cours : seules les pages retravaillées sont exposées
// (Aujourd'hui + Ma Vision, plus l'atelier visuel un cran plus loin).
// Les autres modules (Mouvement, Croissance, Pilotage, Mindset, Campus…)
// restent dans le code mais leurs URL reviennent à l'accueil le temps de
// leur refonte — plus de mélange ancienne version / refonte dans la preview.
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
              <Route path="/vision" element={<MaVision />} />
              <Route path="/vision/atelier" element={<VisionBoard />} />
            </Route>
          </Route>
          <Route path="/login" element={<Login />} />
          <Route path="/login-boutique" element={<LoginBoutique />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster theme="dark" position="top-right" richColors />
    </div></AppErrorBoundary>
  );
}

export default App;
