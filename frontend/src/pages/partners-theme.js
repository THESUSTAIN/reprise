/* Theme "Presta-Partenaire by TheSustain" — palette OFFICIELLE TheSustain
   (fond blanc, accents bleu + rouge, comme leur charte).

   Réseau chrétien — visuellement SÉPARÉ de Zayado SaaS pour éviter la
   confusion de marque, la dilution commerciale et les risques légaux liés
   à l'association explicite d'une offre commerciale neutre avec une
   appartenance religieuse.

   Couleurs sourcées des pages exemples HTML fournies par l'utilisateur :
   #3B5998 bleu marque · #AF1C1A rouge CTA · #1F2937 noir titre · #EFF6FF bleu pastel
*/

export const PARTNER = {
  // Backgrounds
  BG: "#FFFFFF",
  BG_CARD: "#FFFFFF",
  BG_SECTION: "#F8FAFC",
  BG_HERO: "#FFFFFF",            // hero blanc (pas dégradé bleu)
  BG_CTA: "#3B5998",             // section CTA finale bleue pleine largeur
  BG_FOOTER: "#0F172A",          // footer très sombre (pas noir pur)
  BORDER: "#E5E7EB",
  // Textes
  TEXT: "#1E3A5F",               // bleu foncé pour titres (couleur "TheSustain")
  TEXT_BODY: "#1F2937",          // corps de texte
  TEXT_MUTED: "#4B5563",
  TEXT_DIM: "#9CA3AF",
  // Couleurs marque
  BLUE: "#3B5998",               // bleu marque (accents, sections)
  BLUE_DARK: "#1E3A5F",          // bleu foncé titres
  BLUE_DEEP: "#2A4073",
  BLUE_PASTEL: "#EFF6FF",
  RED: "#AE1917",                // rouge CTA officiel TheSustain
  RED_DARK: "#7F1717",
  RED_HOVER: "#8C1413",
  // Alias compat
  NAVY: "#1E3A5F",
  AMBER: "#AE1917",
  AMBER_LIGHT: "#AE1917",
  // Boutons
  BTN_PRIMARY_BG: "#AE1917",     // rouge CTA
  BTN_PRIMARY_TEXT: "#FFFFFF",
  BTN_SECONDARY_BG: "#3B5998",
  BTN_SECONDARY_TEXT: "#FFFFFF",
  // Cards
  CARD_BG: "#FFFFFF",
  CARD_TEXT: "#1F2937",
  CARD_MUTED: "#6B7280",
};

export const PARTNER_FONT = {
  // Police officielle TheSustain : sans-serif simple (Inter recommandé)
  serif: "'Inter', system-ui, -apple-system, sans-serif",
  sans: "'Inter', system-ui, -apple-system, sans-serif",
};

// Logos TheSustain (fournis par l'utilisateur)
export const TS_LOGOS = {
  TEXT_BLUE: "/logos/thesustain-text-blue.png",    // entête + login (cursive bleue)
  TEXT_WHITE: "/logos/thesustain-text-white.png",  // sur fond foncé/hero
  HANDS: "/logos/thesustain-hands.png",            // pied de page (mains + croix)
};
