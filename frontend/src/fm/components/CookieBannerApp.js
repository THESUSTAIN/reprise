import React, { useEffect, useState } from "react";
import { Cookie } from "lucide-react";

const STORAGE_KEY = "zayado_app_cookie_consent";

export default function CookieBannerApp() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const c = localStorage.getItem(STORAGE_KEY);
      if (!c) setTimeout(() => setVisible(true), 1200);
    } catch (e) { /* noop */ }
  }, []);

  const accept = (value) => {
    try {
      localStorage.setItem(STORAGE_KEY, value);
      localStorage.setItem(STORAGE_KEY + "_at", new Date().toISOString());
    } catch (e) { /* noop */ }
    setVisible(false);
    try { window.dispatchEvent(new CustomEvent("zayado:cookie-consent", { detail: { value } })); } catch (e) { /* noop */ }
  };

  if (!visible) return null;

  return (
    <div
      className="fixed bottom-4 right-4 left-4 sm:left-auto sm:max-w-sm z-[9998] rounded-2xl p-4 shadow-2xl"
      style={{ background: "#1a3a6e", color: "#f6f3ee" }}
      data-testid="cookie-banner-app"
    >
      <div className="flex items-start gap-3 mb-3">
        <div className="w-9 h-9 rounded-xl grid place-items-center shrink-0"
             style={{ background: "#f3e9d0", color: "#b89855" }}>
          <Cookie size={16} />
        </div>
        <p className="text-[12.5px] opacity-90 leading-snug flex-1 min-w-0">
          Cookies essentiels + analytiques pour améliorer Zayado. Aucune pub tierce.
        </p>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={() => accept("accepted")}
          className="flex-1 px-3 py-2 rounded-full text-[12px] font-semibold transition"
          style={{ background: "#f6f3ee", color: "#1a3a6e" }}
          data-testid="cookie-app-accept"
        >
          Accepter
        </button>
        <button
          onClick={() => accept("essential")}
          className="flex-1 px-3 py-2 rounded-full text-[12px] font-medium transition"
          style={{ background: "transparent", color: "#f6f3ee", outline: "1px solid rgba(246,243,238,0.4)" }}
          data-testid="cookie-app-essentials"
        >
          Essentiels
        </button>
      </div>
    </div>
  );
}
