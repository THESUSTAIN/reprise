import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@/index.css";
import App from "@/App";

// Applique le thème persisté avant le premier rendu (évite un flash sombre→clair
// au chargement). Même clé/valeur que le toggle du Header (Layout.jsx).
try {
  const raw = JSON.parse(localStorage.getItem("cours-main-settings-preferences") || "{}");
  // Défaut = mode SOMBRE (dark). Le mode clair s'active via le toggle de l'entête
  // (ambiance "clarte" / theme "light"), persisté en localStorage.
  if (raw.ambiance === "clarte" || raw.theme === "light") document.documentElement.classList.add("ambiance-clarte");
} catch { /* noop */ }

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
