# PRD — MyExtension Business (écosystème Zayado)

## Problème / Vision
Cockpit holistique du solopreneur : « L'IA prépare, vous décidez. » SaaS PWA réunissant pilotage financier, vision, croissance et bien-être. **V1 = frontend uniquement, données mockées, aucun backend/IA branché.**

## Architecture (V1)
- React 19 + CRACO + Tailwind + Framer Motion + Recharts, PWA (manifest + service worker, installable, cache offline basique).
- État global via Context (`src/context/AppContext.jsx`) : auth mockée, thème dark/light, ambiance Élan/Refuge, Faith-Toggle — persistés en localStorage.
- Couche de données isolée : `src/data/mock.js` (structurée pour brancher une API plus tard).
- Aucun backend/DB utilisé.

## Personas
- Solopreneur/indépendant (ex-analyste, quête de sens, refus du hustle toxique) voulant piloter finances + vision + énergie sans jongler entre 10 outils. Utilisateur démo : Sarah Lemoine.

## Direction visuelle
- Fond bleu nuit dégradé, Fraunces (titres) + Poppins (texte), glassmorphism, accents or (#D4AF37) / émeraude (#10B981), dark par défaut + light. Sidebar à icônes + header (recherche, notifications, messages, profil).

## Implémenté (2026-06)
- [x] Phase 1 : setup, PWA (manifest, SW, icônes générées), thème bleu nuit + light, fonts, layout sidebar+header, routing 11 pages, login mocké (bouton « Entrer dans le cockpit »).
- [x] Phase 2 : Cockpit du jour complet (Bonjour Sarah + énergie, inspiration carrousel, 4 KPI + sparklines, Ma Trajectoire timeline+checklist, jauge alignement, donut prospects, barres 12 mois, bloc Co-pilote, activité, livrables IA à valider, programme, énergie semaine, à lire).
- [x] Phase 3 : Vision (modèle identitaire, SWOT, bascule Mode Élan/Refuge animée, versets si Faith-Toggle ON) + Copilote IA (chat simulé, suggestions, livrables).
- [x] Phase 4 : Croissance (pipeline 5 étapes + scoring, avancement au clic), Pilotage/DAF (métriques, cashflow, alertes IA, factures, objectifs), Bien-être (énergie, streak, rituels, signaux, humeur), Contexte, Mindset (accepter/pivoter/refuser).
- [x] Phase 5 : Vision Board (5 modèles : roue d'équilibre, roadmap Q1→Q4, modèle identitaire, moodboard, cockpit stratégique) + Agenda (calendrier semaine, filtre qualif IA, cascade rappels, débrief hebdo).
- [x] Phase 6 : Paramètres (profil, Faith-Toggle OFF défaut, thème, langue FR, notifications) + responsive mobile (drawer) + install PWA.
- Testé E2E par l'agent de test : ~95%, 11 modules OK, 0 erreur runtime. Correctifs appliqués : position des toasts (bottom-right) + minHeight des graphiques.

## Hors périmètre V1 (slots « prêts à brancher »)
- Backend réel, vraie IA, connexion banque, marketplace Zayado, automations Make/Zapier/WhatsApp/Cal.com.

## Backlog priorisé
- P1 : brancher un vrai modèle IA au Copilote (GPT/Claude/Gemini) via couche services.
- P1 : persistance backend (FastAPI + MongoDB) + auth multi-comptes.
- P2 : agrégateur bancaire (Bridge/Powens) pour le DAF réel.
- P2 : automations agenda (rappels multicanaux réels), i18n multilingue.
- P2 : drag & drop réel sur le pipeline, export Vision Board.

## Notes techniques
- Auth mockée : bouton `login-enter-cockpit-btn`. Clés localStorage : mx_authed, mx_theme, mx_ambiance, mx_faith.
