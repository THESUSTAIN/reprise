# MyExtension-ai by Zayado — Notes

## Session: Fusion final-main + reprise-main sur nouvelle-main (contour header/sidebar)
Date: 2026-06-21

### Fait
- Installé nouvelle-main dans /app (frontend React + backend FastAPI/SQLAlchemy SQLite local).
- Corrigé bug rendu blanc: cache webpack-dev-server stale (logEnabledFeatures) -> rm -rf node_modules/.cache.
- Header/Sidebar alignés sur la reference okyai-clone:
  - Header band = navy uniforme linear-gradient(to right,#142b45,#1B3A5B,#0c1d31)
  - Scoops header (.zy-header-scoop) = fill #142b45 (flare navy, plus le fond de page)
  - Header margin mx-5 md:mx-10, wordmark variante onDark (navy band les 2 themes)
  - Sidebar inner box = from-#142b45 via-#1B3A5B to-#0c1d31 ; scoops fill #142b45
  - Search = texte clair sur navy (les 2 themes)

### Cles API fournies (dans backend/.env)
- Mollie, Mammouth, Revo/Brevo, Google, Microsoft, Canva, Heyzine.
- NON activé: DATABASE_URL/DB_HOST Hostinger MySQL distant (resterait sur SQLite local en preview).

### Backlog / Next
- Wirer la DB MySQL distante si demandé (DATABASE_URL Hostinger).
- Porter pages stub (Pilotage, Bien-etre, etc.) depuis final-main.
- Vérifier integrations (Mollie paiement, Google/MS OAuth) en e2e.

## Session 2 (2026-06-21) — Corrections light mode + Vision Board + sidebar
- Vision Board (/vision-board) sorti du Layout global -> plus de double header; la page garde sa propre top-nav navy/gold autonome.
- Light mode aligné sur final-main: header BLANC (texte navy), sidebar navy-blue, page cream.
  - .zy-header-band: dark=navy #142b45->#0c1d31 / light=#fff
  - .zy-header-scoop: dark #142b45 / light #fff
  - Helpers .zy-hdr-btn (boutons theme-aware), .zy-hdr-sep; icônes header en text-current; Logo variant theme-aware.
  - .zy-search theme-aware (texte navy sur blanc en light).
- Sidebar plus "noir": outer #0c1d33, inner gradient #2a4a8e->#1f3b73->#0f1e50 (palette final-main), scoops #2a4a8e/#0f1e50.
