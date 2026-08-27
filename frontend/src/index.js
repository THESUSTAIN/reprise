import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@/index.css";
import App from "@/App";

// Applique le thème persisté avant le premier rendu (évite un flash sombre→clair
// au chargement). Même clé/valeur que le toggle du Header (Layout.jsx).
try {
  const raw = JSON.parse(localStorage.getItem("cours-main-settings-preferences") || "{}");
  // Défaut = mode CLAIR (light) — sauf si l'utilisateur a explicitement choisi
  // le mode sombre via le toggle de l'entête (ambiance "sens" / theme "dark").
  const explicitDark = raw.ambiance === "sens" || raw.theme === "dark";
  if (!explicitDark) document.documentElement.classList.add("ambiance-clarte");
} catch { document.documentElement.classList.add("ambiance-clarte"); }

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      refetchOnWindowFocus: false,
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);

// PWA service worker registration
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {});
  });
}
