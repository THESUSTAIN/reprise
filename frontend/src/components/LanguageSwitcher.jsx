/* Bouton de traduction multilingue — IP geolocation + Google Translate widget
   Détecte automatiquement la langue de l'utilisateur via son IP (ipapi.co)
   et propose un dropdown pour basculer entre FR/EN/ES/DE/IT/PT/NL.
   Utilise le widget Google Translate (charge à la demande, masque sa barre native).
*/
import React, { useEffect, useRef, useState } from "react";
import { Globe, Check } from "lucide-react";

const LANGS = [
  { code: "fr", label: "Français", flag: "🇫🇷" },
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "es", label: "Español", flag: "🇪🇸" },
  { code: "de", label: "Deutsch", flag: "🇩🇪" },
  { code: "it", label: "Italiano", flag: "🇮🇹" },
  { code: "pt", label: "Português", flag: "🇵🇹" },
  { code: "nl", label: "Nederlands", flag: "🇳🇱" },
];

// Mapping pays → langue par défaut (IP geolocation)
const COUNTRY_TO_LANG = {
  GB: "en", US: "en", IE: "en", CA: "en", AU: "en", NZ: "en",
  FR: "fr", BE: "fr", CH: "fr", LU: "fr", MC: "fr",
  ES: "es", MX: "es", AR: "es", CO: "es", PE: "es", CL: "es",
  DE: "de", AT: "de",
  IT: "it", SM: "it",
  PT: "pt", BR: "pt",
  NL: "nl",
};

const STORAGE_KEY = "zayado_lang";
const IP_CACHE_KEY = "zayado_ip_country";

function loadGoogleTranslate() {
  if (window.__zayGTLoaded) return;
  window.__zayGTLoaded = true;

  window.googleTranslateElementInit = function () {
    if (!window.google?.translate?.TranslateElement) return;
    new window.google.translate.TranslateElement(
      {
        pageLanguage: "fr",
        includedLanguages: LANGS.map((l) => l.code).join(","),
        autoDisplay: false,
        layout: window.google.translate.TranslateElement.InlineLayout.SIMPLE,
      },
      "zay-google-translate-hidden",
    );
  };

  const s = document.createElement("script");
  s.src = "//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
  s.async = true;
  document.body.appendChild(s);
}

function applyLanguage(code) {
  // Le widget Google Translate expose un <select class="goog-te-combo"> caché.
  // En plus du dispatch change event, on set le cookie googtrans qui sert de
  // backup robuste : si le widget recharge plus tard, il restaure la traduction.
  const host = window.location.hostname;
  const parts = host.split(".");
  const variants = [undefined, host];
  if (parts.length > 1) variants.push("." + parts.slice(-2).join("."));

  // 1) Set/Clear cookie googtrans (mécanisme officiel Google Translate)
  variants.forEach((d) => {
    const dom = d ? `; domain=${d}` : "";
    if (code === "fr") {
      document.cookie = `googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/${dom};`;
    } else {
      document.cookie = `googtrans=/fr/${code}; path=/${dom};`;
    }
  });

  // 2) Tente de dispatcher le change sur le select natif si déjà monté
  const targetValue = code === "fr" ? "" : code;
  const doApply = (sel) => {
    sel.value = targetValue;
    sel.dispatchEvent(new Event("change"));
  };

  const existing = document.querySelector(".goog-te-combo");
  if (existing) { doApply(existing); return; }

  // 3) Sinon, on attend l'apparition du select (MutationObserver + polling)
  let done = false;
  const observer = new MutationObserver(() => {
    const sel = document.querySelector(".goog-te-combo");
    if (sel && !done) { done = true; observer.disconnect(); doApply(sel); }
  });
  observer.observe(document.body, { childList: true, subtree: true });
  let attempts = 0;
  const iv = setInterval(() => {
    attempts += 1;
    const sel = document.querySelector(".goog-te-combo");
    if (sel && !done) { done = true; observer.disconnect(); clearInterval(iv); doApply(sel); }
    else if (attempts > 75) {
      // Fallback ultime : recharge la page, le cookie googtrans fera le job au prochain load
      observer.disconnect();
      clearInterval(iv);
      if (!done && code !== "fr") window.location.reload();
    }
  }, 200);
}

async function detectCountryViaIP() {
  // Cache 24h pour éviter de spammer les APIs
  try {
    const cached = JSON.parse(localStorage.getItem(IP_CACHE_KEY) || "null");
    if (cached && cached.ts && Date.now() - cached.ts < 24 * 60 * 60 * 1000) {
      return cached.country;
    }
  } catch {}
  // Liste d'endpoints CORS-friendly avec fallback
  const endpoints = [
    { url: "https://api.country.is/", extract: (j) => j.country },
    { url: "https://ipapi.co/json/", extract: (j) => j.country_code || j.country },
    { url: "https://ipwho.is/", extract: (j) => j.country_code },
  ];
  for (const ep of endpoints) {
    try {
      const res = await fetch(ep.url, { cache: "no-store" });
      if (!res.ok) continue;
      const j = await res.json();
      const country = (ep.extract(j) || "").trim().toUpperCase();
      if (country && country.length === 2) {
        localStorage.setItem(IP_CACHE_KEY, JSON.stringify({ country, ts: Date.now() }));
        return country;
      }
    } catch {}
  }
  return null;
}

export default function LanguageSwitcher({ variant = "light" }) {
  const [open, setOpen] = useState(false);
  const [lang, setLang] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEY) || "fr"; } catch { return "fr"; }
  });
  const ref = useRef(null);

  // Chargement initial : widget. Pas de détection IP automatique (le site
  // reste en français par défaut, l'utilisateur peut changer manuellement
  // via le bouton globe — sinon la prod auto-traduit Zayado en anglais pour
  // les visiteurs étrangers, ce qui casse l'UX et le SEO).
  useEffect(() => {
    loadGoogleTranslate();

    let stored = null;
    try { stored = localStorage.getItem(STORAGE_KEY); } catch {}

    if (stored && stored !== "fr") {
      // Pref stockée non-FR → applique après le chargement du widget
      setTimeout(() => applyLanguage(stored), 800);
    }
    // Note : on ne déclenche PLUS detectCountryViaIP() au mount.
    // Cela évite que les bots crawlers (US) indexent une version EN.
  }, []);

  // Fermer le dropdown au clic extérieur
  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const onSelect = (code) => {
    setLang(code);
    try { localStorage.setItem(STORAGE_KEY, code); } catch {}
    applyLanguage(code);
    setOpen(false);
  };

  const current = LANGS.find((l) => l.code === lang) || LANGS[0];
  const isDark = variant === "dark";

  return (
    <div className="relative" ref={ref} data-testid="language-switcher">
      <button
        onClick={() => setOpen(!open)}
        className={
          "inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-colors " +
          (isDark
            ? "text-white/90 hover:bg-white/10 border border-white/20"
            : "text-[var(--zayado-text)] hover:bg-[var(--zayado-cream)] border border-transparent")
        }
        aria-label="Changer la langue"
        data-testid="language-switcher-button"
      >
        <Globe size={13} />
        <span className="hidden sm:inline">{current.flag}</span>
        <span className="uppercase tracking-wider">{current.code}</span>
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-2 min-w-[180px] bg-white rounded-xl shadow-xl border border-[var(--zayado-border)] overflow-hidden z-[100]"
          data-testid="language-switcher-menu"
        >
          <div className="px-3 py-2 text-[10px] uppercase tracking-wider font-bold border-b border-[var(--zayado-border)]"
               style={{ color: "var(--zayado-muted)" }}>
            Langue · Language
          </div>
          {LANGS.map((l) => (
            <button
              key={l.code}
              onClick={() => onSelect(l.code)}
              className="w-full px-3 py-2 text-left text-sm flex items-center gap-2.5 hover:bg-[var(--zayado-cream)] transition-colors"
              data-testid={`language-option-${l.code}`}
            >
              <span className="text-base">{l.flag}</span>
              <span className="flex-1" style={{ color: "var(--zayado-text)" }}>{l.label}</span>
              {l.code === lang && <Check size={14} style={{ color: "var(--zayado-gold)" }} />}
            </button>
          ))}
          <div className="px-3 py-2 text-[10px] border-t border-[var(--zayado-border)]"
               style={{ color: "var(--zayado-muted)" }}>
            Traduction propulsée par Google
          </div>
        </div>
      )}

      {/* Élément invisible pour le widget Google Translate */}
      <div id="zay-google-translate-hidden" style={{ display: "none" }} />
    </div>
  );
}
