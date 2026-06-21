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

## Session 3 (2026-06-21) — Sidebar uniforme + Vision Board light
- Sidebar: refonte en dégradé navy UNIFORME pleine hauteur (#2a4a8e->#1f3b73->#0f1e50, style final-main). Supprimé le combo outer noir + inner box + scoops qui créait l'effet 2 tons (noir haut/bas + bleu milieu).
- Vision Board: ajout d'un thème LIGHT complet (html:not(.dark) .vb-root) -> fond blanc/cream, cartes blanches, textes navy, boutons OK. Couleurs inline #F6F2EA/#9fb2c9 remplacées par var(--cream)/var(--muted).
- Ajout d'un bouton bascule thème (Sun/Moon) dans la top-nav du Vision Board (data-testid vb-theme-toggle).

## Session 4 (2026-06-21) — Pages + branchement backend + tests
- Sidebar dashboard: même couleur que le header (navy #142b45->#0c1d31).
- Vision Board: logo officiel (composant Logo) au lieu du "M"; boutons en dégradé NAVY (plus de gold/maron); branché au backend MongoDB (vision_board.py + heyzine.py + canva.py portés depuis reprise, motor) -> /api/vision/board|info|copilot-data|analyse|visionbook + /api/canva/* renvoient 200 avec données. Toggle thème ajouté dans sa top-nav.
- 3 pages créées + branchées backend (JWT): Pilotage (/pilotage -> finance overview/forecast/serenity/entry), Bien-être (/bien-etre -> wellness today/checkin/history), Espace (/espace -> projects CRUD + timer). Login réel (/login) + AuthGate.
- Compte test: test@zayado.net / Test1234! (seedé). Backend local = SQLite.
- Tests agent: backend 11/11, frontend flows 100%, aucun bug bloquant.

### Backlog
- finance.py: import-csv-v2 manque `from sqlalchemy import text`; routes import-url/import-csv ont un double préfixe /finance/finance (non bloquant).
- processes.py utilise du SQL MySQL-only (échoue sur SQLite) -> Espace branché sur /projects à la place.
- Pages restantes à porter: Croissance, Intégrations, WordPress, Admin, Onboarding.
- Brancher la vraie base MySQL Hostinger + intégrations (Mollie, Google, Microsoft, Canva) quand souhaité.

## Session 5 (2026-06-21) — Suppression Mongo + Login final-main
- RETIRÉ toutes les routes MongoDB (motor). Vision Board réécrit en store fichier JSON (backend/vision_local.py, vision_store.json) — aucune dépendance Mongo. Endpoints /api/vision/* + /api/canva/* OK (200).
- LOGIN refait fidèle à final-main: passwordless (lien magique /api/auth/request-link + /verify-link, OAuth Google/Microsoft /api/oauth/*, mode invité /api/auth/guest). AUCUNE inscription, AUCUN mot de passe. .env backend: ALLOW_GUEST_LOGIN=true, PUBLIC_FRONTEND_URL.
- À FAIRE (demande user): porter FIDÈLEMENT les pages de final-main (Pilotage.js, BienEtre.js, EspaceDeTravail.js) — actuellement ce sont des versions maison fonctionnelles branchées SQL, PAS les ports exacts final-main.

## Session 6 (2026-06-21) — Fidélité totale final-main + auto-invité + suppression Mongo
- MONGO RETIRÉ : Vision Board en store fichier JSON (vision_local.py). Aucune route motor.
- AUTH : auto-session INVITÉ silencieuse (AuthContext.refresh -> /api/auth/guest, ALLOW_GUEST_LOGIN=true) -> AUCUN écran de connexion. Login passwordless (magic-link + OAuth + invité) conservé mais masqué.
- PAGES final-main PORTÉES FIDÈLEMENT sous alias @fm (src/fm/) : /pilotage, /bien-etre, /espace — TopNav + SideNav + FloatingBottomBar + WelcomeModal (1er passage par page) + design tokens navy/cream/gold (tailwind.config + fm/fm.css). Token JWT partagé (zayado_token). fm/lib/api (fetch) vers le même backend.
- WelcomeModal ajoutée à BienEtre (manquait) + entrée 'bienetre' dans welcomeContent.js.
- Tests agent iteration_2 : backend 11/11, toutes les pages rendent, pas de mur de login, Vision Board OK. Seul souci (modal BienEtre) corrigé + vérifié.

### Reste / backlog
- Coquille reprise (Dashboard/Header/Sidebar) coexiste avec la nav final-main (TopNav) sur ces 3 pages (choix user = option 1).
- Données invité vides : certains endpoints fm (analyse/revenue/finance) renvoient 0 -> brancher la vraie DB MySQL + intégrations pour données réelles.
- Pages restantes à porter (Croissance, Intégrations, WordPress, Admin) + finaliser /login pour la fin.

## Session 7 (2026-06-21) — Mode sombre final-main FINALISÉ (Priorité 1 ✅)
- CORRIGÉ le mode sombre des pages importées /pilotage, /bien-etre, /espace.
- Approche : bloc dark dans fm.css (`html.dark .fm-page`) qui (1) remappe les variables ambiguës (--bg, --surface, --border, --cream-soft, --cream-dark) et (2) neutralise les classes Tailwind couleur "en dur" (.text-[#1F2937], .text-[#6B6358], .bg-[#FBF6EA], .bg-[#F3E9D0], .border-[#E8E2D8]...) + .card-soft + thème Recharts (axes/grille/tooltip).
- Corrigé qq styles inline ambigus dans Pilotage.js / BienEtre.js : textes clairs sur cartes navy passés en var(--cream) (au lieu de var(--bg)), panneau "frozen", icône alerte, fonds #FBF6EA -> var(--cream-soft), tooltips -> var(--bg-card).
- Testing agent iteration_3 : PASS. 0 carte/élément clair détecté en mode sombre sur les 3 pages (scan computed backgroundColor). Light mode non cassé. WelcomeModal OK sur les 3 pages. Aucune double-nav.
- Mineurs non bloquants : pas de data-testid 'page-wellness' (seulement 'page-bien-etre') ; /espace a 3 onglets (Missions/Processus/Documents), pas 4.
