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
- LOGIN + APP : bleu EXACT du reprise-main d'origine restauré partout, vérifié contre le zip d'origine (`/tmp/r.zip`) : `linear-gradient(180deg, #172C5C 0%, #101F47 42%, #0B1F3A 76%, #081734 100%)` + halos bleus d'origine. Puis alignement renforcé : le login réutilise désormais TOUTES les couches du fond de l'app (halos + voile de nuages clairs animé), sans son voile sombre ni sa texture de points — login et cockpit affichent la même couleur perçue. Le bleu clair (#2E4370→#6483B4) était une déviation de la session précédente — corrigée. Variante clarté : `#172C5C → #101F47 55% → #0B1F3A`
- HEADER mobile : devenu transparent (était dégradé navy opaque) ; desktop l'était déjà
- GRAPHIQUES réels sur Aujourd'hui (recharts) : courbe « Ton énergie · 30 jours » (check-ins wellness) + histogramme « Ton rythme d'actions · 7 jours » (tâches created_at). États vides honnêtes avec CTA, aucune donnée fabriquée
- BULLE COPILOTE flottante dorée en bas à droite sur desktop (remplace la languette verticale), ouvre/replie le panneau Copilote, badge actualité
- MON REFUGE : nouvelle page `/refuge` (4e onglet nav desktop + mobile) — check-in énergie réel (POST wellness/checkin), respiration guidée 4-4-6 animée, pensée du jour, bascule Mode Foi (verset du jour, persistée localStorage `mx_foi`, lue aussi par Aujourd'hui), historique des check-ins
- Tests : 9/9 scénarios PASS (testing agent, iteration_1.json), dont check-in réel + courbe qui apparaît avec 2 points, Mode Foi persistant, login sans noir, mobile sans débordement

### 2026-09-19 (maquettes structure)
- 4 modèles A/B/C/D créés puis ÉCARTÉS par l'utilisateur (« j'aime pas les maquettes ») → on GARDE la structure actuelle validée. Fichiers conservés dans /design-preview pour référence
- 2 propositions de chat créées : /design-preview/c1-chat-pc.html (tiroir droit affiné, onglets Discussion/Actualité en pilules) et /design-preview/c2-chat-mobile.html (plein écran, onglet Actualité, Signal du jour) — COMPARAISON UTILISATEUR EN ATTENTE vs chat actuel
- Boutons : `.gold-bg` redéfini en navy dégradé (#1E3468→#0B1F3A→#081734) + liseré/texte beige (choix utilisateur) — appliqué partout via la classe existante
- BUG CORRIGÉ : double header du chat mobile (header Layout « Copilote » empilé sur celui de ChatPanel) → un seul header, bouton « Retour » via prop onBack ; header chat mobile densifié (sous-titre/contexte masqués <768px)
- Tests : 7/7 PASS (testing agent, iteration_2.json) — tous les boutons des 3 pages vérifiés un par un, responsive 390px sans débordement, bulle Copilote OK

### 2026-09-19 (style chat validé — proposition B)
- Design chat « B » APPLIQUÉ au vrai Copilote : onglets Discussion/Actualité en pilules navy dégradé + contour beige-or, icône Actualité rouge quand non lu, bouton d'envoi rendu visible (était transparent + icône sombre = bug UI), suggestions et actions Actualité en navy/beige, bouton « Envoyer la demande » (Collaborer) harmonisé, bulle Copilote (FAB) passée en navy/beige assortie
- `.gold-bg` global = navy dégradé noir + texte beige → tous les CTA du SaaS (3 pages refondues + pages cachées)
- Maquettes m1-m4 écartées par l'utilisateur ; c1/c2 (chat) : B retenue et appliquée

## Backlog priorisé
- P0 : (aucun bloquant connu)
- P1 : Menu « + » (Explorer) regroupant les modules cachés (Mouvement, Croissance, Pilotage, Mindset…) — les routes existent mais redirigent vers `/`
- P2 : Déplacer Marketplace / Espace Membre dans une section Compte/Paramètres
- P2 : Mettre à jour le WelcomeTour (mentionne encore « Mouvement & Croissance », modules cachés)
- P2 : Refondre les pages restantes une par une dans le nouveau style (Mouvement, Croissance, Pilotage…)

## Notes
- Service worker PWA en network-first : une simple recharge suffit pour voir la nouvelle version
- `WP_CONNECTOR_SECRET` manquant dans les logs backend (non bloquant, intégration WordPress)
