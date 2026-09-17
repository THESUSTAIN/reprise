/**
 * WPSiteSettings — injecte dynamiquement favicon + meta description depuis WordPress.
 * Source : GET {VITE_API_URL}/api/wp/site-settings (public).
 * Cache : sessionStorage 10 min pour éviter de spammer l'API à chaque navigation.
 */
import { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";

const CACHE_KEY = "zay_wp_site_settings_v1";
const CACHE_TTL_MS = 10 * 60 * 1000;
const API = import.meta.env.VITE_API_URL || "";

function readCache() {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const { ts, data } = JSON.parse(raw);
    if (Date.now() - ts > CACHE_TTL_MS) return null;
    return data;
  } catch {
    return null;
  }
}

function writeCache(data) {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), data }));
  } catch {
    /* ignore */
  }
}

export default function WPSiteSettings() {
  const [settings, setSettings] = useState(() => readCache());

  useEffect(() => {
    if (settings) return; // déjà en cache
    let cancelled = false;
    fetch(`${API}/api/wp/site-settings`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (cancelled || !data) return;
        setSettings(data);
        writeCache(data);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [settings]);

  if (!settings) return null;
  const { site_icon_url, language } = settings;
  // NOTE: We DELIBERATELY don't inject `description` / `og:description` here.
  // Each page sets its own via <Helmet> — WP-level description would override
  // them due to react-helmet-async's "last mount wins" rule.
  return (
    <Helmet>
      {language && <html lang={language.split("_")[0] || "fr"} />}
      {site_icon_url && <link rel="icon" type="image/png" href={site_icon_url} />}
      {site_icon_url && <link rel="apple-touch-icon" href={site_icon_url} />}
      {site_icon_url && <meta property="og:image" content={site_icon_url} />}
    </Helmet>
  );
}
