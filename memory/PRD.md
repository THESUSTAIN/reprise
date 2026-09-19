# PRD — Refonte Cockpit Zayado / MyExtension Business

## Problème initial (demande utilisateur)
Créer la nouvelle interface du cockpit SaaS :
- Page « Aujourd'hui » adaptative (bascule Élan / Refuge)
- Navigation à 4 entrées : Aujourd'hui · Ma Vision · Copilote · Mon Refuge
- Bulle Copilote flottante
- Vrai SaaS branché sur les données réelles, pas une maquette factice
- Style : cartes type okyai.com, dégradé bleu, maquettes validées = `public/design-preview/v3-aujourdhui.html` et `v3-vision.html`
- Ne PAS toucher à la forme du header ni du menu gauche (reprise exacte de reprise-main)
- CACHER toutes les anciennes pages (50+) le temps de la refonte, pour ne pas mélanger ancien/nouveau

## Contraintes utilisateur explicites
- Réutiliser l'existant, ne pas reconstruire de zéro (sensibilité au coût des crédits)
- Répondre en français
- Compte test : thomas@zayado.fr (voir /app/memory/test_credentials.md)

## Architecture
- Frontend : React + Vite (`/app/frontend`), preview forcée en mode cockpit sur le domaine Emergent (`isAppHost` dans `src/main.jsx`)
- Backend : FastAPI + SQLite local (`/app/backend`, `zayado.db`), routes préfixées `/api`
- Auth : JWT, login démo via `POST /api/auth/demo-login` (preview uniquement, session auto Thomas)

## Implémenté (avec dates)
### 2026-07-14 (session précédente)
- Codebase `reprise-main` portée et fonctionnelle (backend FastAPI + SQLite, seed Thomas, clés API)
- Maquettes statiques validées : v3-aujourdhui.html, v3-vision.html
- `Aujourdhui.jsx` et `MaVision.jsx` refondus en React, données réelles (vision, humeur, tâches, jalons, décisions)
- `App.jsx` : seules `/`, `/vision`, `/vision/atelier` exposées ; toutes les autres URL redirigent vers `/`
- `Layout.jsx` : sidebar allégée (Aujourd'hui · Ma Vision · Copilote central), modules cachés

### 2026-09-19 (cette session)
- BUG CORRIGÉ : sur mobile, l'accueil affichait encore l'ANCIEN chat plein écran (« Hub IA · Discussion/Actualité »). La branche mobile de `AppHome` dans `App.jsx` a été supprimée — l'accueil mobile affiche maintenant la nouvelle page « Aujourd'hui » avec nav basse ; le Copilote s'ouvre en surcouche plein écran depuis la nav basse
- Vérifié par captures : desktop + mobile affichent la nouvelle version

## Backlog priorisé
- P0 : (aucun bloquant connu)
- P1 : Bulle Copilote flottante sur desktop (aujourd'hui panneau latéral + languette)
- P1 : Onglet « Mon Refuge » (4e entrée de nav) avec bascule Mode Foi — reprendre la page Mindset & Capacité ou page neuve simple (CHOIX UTILISATEUR EN ATTENTE, question posée)
- P2 : Menu « + » (Explorer) regroupant les modules cachés (Mouvement, Croissance, Pilotage…)
- P2 : Déplacer Marketplace / Espace Membre dans une section Compte/Paramètres
- P2 : Mettre à jour le WelcomeTour (mentionne encore « Mouvement & Croissance », modules cachés)

## Notes
- Service worker PWA en network-first : une simple recharge suffit pour voir la nouvelle version
- `WP_CONNECTOR_SECRET` manquant dans les logs backend (non bloquant, intégration WordPress)
