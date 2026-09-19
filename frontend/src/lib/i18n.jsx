/* i18n Zayado — détection auto FR/EN.

   Stratégie :
   1. Lecture localStorage `zay_lang` (override manuel utilisateur)
   2. Sinon navigator.language (ex: 'fr-FR' → 'fr', 'en-US' → 'en')
   3. Sinon IP geolocation mock (defaults FR pour Europe/Afrique, EN ailleurs)
   4. Default FR

   Usage :
     import { useT, setLang, getLang } from "@/lib/i18n";
     const t = useT();
     t("hero.title")  // → "Entreprendre, sans rester seul." (ou EN)
*/
import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from "react";

const STORAGE_KEY = "zay_lang";
const SUPPORTED = ["fr", "en"];

// ── Dictionnaires ─────────────────────────────────────────────────────────
const dict = {
  fr: {
    "nav.shop": "Boutique",
    "nav.app": "L'app",
    "nav.groupement": "Groupement",
    "nav.about": "À propos",
    "nav.contact": "Contact",
    "nav.login": "Se connecter",
    "nav.cart": "Panier",

    "hero.kicker": "La maison des entrepreneurs apaisés",
    "hero.title": "Entreprendre,",
    "hero.title_em": "sans rester seul.",
    "hero.subtitle": "Une boutique d'essentiels pour le corps et l'âme. Une app pour piloter sereinement. Un groupement pour avancer ensemble. Zayado réunit les trois.",
    "hero.cta_shop": "Découvrir la boutique",
    "hero.cta_app": "Essayer l'app gratuitement",
    "hero.trust1": "Sans engagement",
    "hero.trust2": "RGPD strict · données en France",
    "hero.trust3": "1 200+ entrepreneurs accompagnés",

    "values.kicker": "Nos valeurs",
    "values.calme.title": "Calme",
    "values.calme.desc": "On ralentit pour décider juste.",
    "values.lucidite.title": "Lucidité",
    "values.lucidite.desc": "On dit la vérité — même quand elle dérange.",
    "values.trajectoire.title": "Trajectoire",
    "values.trajectoire.desc": "Pas de hacks. Que des choix cohérents.",
    "values.durabilite.title": "Durabilité",
    "values.durabilite.desc": "Production locale, marques engagées.",

    "universes.kicker": "Trois territoires, une intention",
    "universes.title": "Une maison,",
    "universes.title_em": "pas un outil de plus.",
    "universes.shop.title": "Le corps, l'âme.",
    "universes.shop.desc": "Objets, livres, huiles essentielles, lunettes anti-lumière bleue. Petites séries, production locale.",
    "universes.shop.cta": "Découvrir la boutique",
    "universes.app.title": "Piloter, sereinement.",
    "universes.app.desc": "Validation terrain, roadmap, CRM superfans, énergie & focus, collaborateur IA. L'app qui pense avec vous.",
    "universes.app.cta": "Essayer l'app",
    "universes.group.title": "Avancer ensemble.",
    "universes.group.desc": "Assurance, juridique, comptable, coworking, marketing. 9 partenaires éco-engagés, tarifs négociés.",
    "universes.group.cta": "Voir les partenaires",

    "tools.kicker": "Notre écosystème",
    "tools.title": "Connecté aux outils",
    "tools.title_em": "que vous utilisez déjà.",
    "tools.subtitle": "Google Drive, Microsoft 365, Brevo, WooCommerce, Stripe, WhatsApp… Zayado s'intègre nativement à votre stack. Pas de double saisie, pas de friction.",

    "group.kicker": "Le groupement",
    "group.title": "9 partenaires",
    "group.title_em": "éco-engagés.",
    "group.subtitle": "Tarifs négociés, charte stricte, valeurs alignées. Nos partenaires sont des indépendants ou des PME françaises, jamais des géants opaques.",

    "testimonials.kicker": "Ils nous font confiance",
    "testimonials.title": "Ce qu'en disent",
    "testimonials.title_em": "les pros.",

    "cta.title": "Prêt·e à construire",
    "cta.title_em": "avec calme",
    "cta.subtitle": "Rejoignez les 1 200+ entrepreneurs qui ont choisi de ralentir pour aller plus loin.",
    "cta.shop": "Visiter la boutique",
    "cta.signup": "Créer mon compte",

    "footer.col1": "Découvrir",
    "footer.col2": "Service",
    "footer.col3": "Légal",
    "footer.tagline": "L'essentiel pour les entrepreneurs qui construisent leur trajectoire avec",
    "footer.tagline_em": "calme.",
    "footer.made": "Conçu en France · Petites séries · RGPD strict",
    "footer.rights": "Tous droits réservés",
  },
  en: {
    "nav.shop": "Shop",
    "nav.app": "The app",
    "nav.groupement": "Network",
    "nav.about": "About",
    "nav.contact": "Contact",
    "nav.login": "Log in",
    "nav.cart": "Cart",

    "hero.kicker": "The home for calm entrepreneurs",
    "hero.title": "Build your business,",
    "hero.title_em": "without going it alone.",
    "hero.subtitle": "A shop of essentials for body and mind. An app to lead serenely. A network to move forward together. Zayado brings all three.",
    "hero.cta_shop": "Visit the shop",
    "hero.cta_app": "Try the app for free",
    "hero.trust1": "No commitment",
    "hero.trust2": "Strict GDPR · data hosted in France",
    "hero.trust3": "1,200+ founders supported",

    "values.kicker": "Our values",
    "values.calme.title": "Calm",
    "values.calme.desc": "We slow down to decide rightly.",
    "values.lucidite.title": "Lucidity",
    "values.lucidite.desc": "We tell the truth — even when it stings.",
    "values.trajectoire.title": "Trajectory",
    "values.trajectoire.desc": "No hacks. Only coherent choices.",
    "values.durabilite.title": "Sustainability",
    "values.durabilite.desc": "Local production, ethical brands only.",

    "universes.kicker": "Three territories, one intention",
    "universes.title": "A home,",
    "universes.title_em": "not just another tool.",
    "universes.shop.title": "The body, the soul.",
    "universes.shop.desc": "Objects, books, essential oils, blue-light glasses. Small batches, local production.",
    "universes.shop.cta": "Discover the shop",
    "universes.app.title": "Lead, serenely.",
    "universes.app.desc": "Validation, roadmap, superfan CRM, focus & energy, AI co-pilot. The app that thinks with you.",
    "universes.app.cta": "Try the app",
    "universes.group.title": "Move forward together.",
    "universes.group.desc": "Insurance, legal, accounting, coworking, marketing. 9 ethical partners, negotiated rates.",
    "universes.group.cta": "See partners",

    "tools.kicker": "Our ecosystem",
    "tools.title": "Connected to the tools",
    "tools.title_em": "you already use.",
    "tools.subtitle": "Google Drive, Microsoft 365, Brevo, WooCommerce, Stripe, WhatsApp… Zayado integrates natively with your stack. No double entry, no friction.",

    "group.kicker": "The network",
    "group.title": "9 ethical",
    "group.title_em": "partners.",
    "group.subtitle": "Negotiated rates, strict charter, aligned values. Our partners are independent freelancers or French SMEs — never opaque giants.",

    "testimonials.kicker": "They trust us",
    "testimonials.title": "What the",
    "testimonials.title_em": "pros say.",

    "cta.title": "Ready to build",
    "cta.title_em": "calmly",
    "cta.subtitle": "Join the 1,200+ founders who chose to slow down to go further.",
    "cta.shop": "Visit the shop",
    "cta.signup": "Create my account",

    "footer.col1": "Discover",
    "footer.col2": "Service",
    "footer.col3": "Legal",
    "footer.tagline": "Essentials for founders building their path with",
    "footer.tagline_em": "calm.",
    "footer.made": "Designed in France · Small batches · Strict GDPR",
    "footer.rights": "All rights reserved",
  },
};

// ── Détection ─────────────────────────────────────────────────────────────
function detectFromNavigator() {
  if (typeof navigator === "undefined") return null;
  const langs = [navigator.language, ...(navigator.languages || [])];
  for (const l of langs) {
    const code = (l || "").toLowerCase().split("-")[0];
    if (SUPPORTED.includes(code)) return code;
  }
  return null;
}

// detectFromIP désactivée — évite Google Translate auto + dégradation SEO
// Le changement de langue reste possible via le bouton manuel
async function detectFromIP() {
  return null; // Désactivé intentionnellement
}

function detectInitial() {
  // 1. Override utilisateur (bouton manuel)
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && SUPPORTED.includes(stored)) return stored;
  }
  // 2. Navigator language
  const nav = detectFromNavigator();
  if (nav) return nav;
  // 3. Default FR — détection IP désactivée (causait Google Translate auto)
  return "fr";
}

// ── Context React ─────────────────────────────────────────────────────────
const I18nContext = createContext({ lang: "fr", setLang: () => {}, t: (k) => k });

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    // Init synchrone (navigator + localStorage), IP en async ensuite
    if (typeof window === "undefined") return "fr";
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && SUPPORTED.includes(stored)) return stored;
    return detectFromNavigator() || "fr"; // navigator uniquement, pas d'IP
  });

  // Détection IP désactivée — causait Google Translate auto et SEO dégradé
  // Le changement de langue est 100% manuel via le bouton dans l'interface

  const setLang = useCallback((newLang) => {
    if (!SUPPORTED.includes(newLang)) return;
    setLangState(newLang);
    try { localStorage.setItem(STORAGE_KEY, newLang); } catch {}
    document.documentElement.lang = newLang;
  }, []);

  useEffect(() => { document.documentElement.lang = lang; }, [lang]);

  const t = useCallback((key) => {
    return dict[lang]?.[key] || dict.fr[key] || key;
  }, [lang]);

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useT() {
  return useContext(I18nContext).t;
}

export function useLang() {
  return useContext(I18nContext);
}
