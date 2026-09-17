# PRD — Zayado (application importée)

## Contexte
Projet SaaS mature « Zayado » importé (backend FastAPI + SQLAlchemy, ~90 routes ; frontend Vite/React 18). Split site public (zayado.net) / cockpit SaaS (app.zayado.net). Base SQLite en local, MySQL en prod.

## État de l'environnement (mise en route)
- Backend FastAPI **UP** (SQLite, `CAP_VIVANT_LOCAL_DB=1`, `RUN_CRONS=false`), `/api/health` = ok, 811 routes.
- Frontend Vite **UP** sur :3000 (`yarn start`).
- Clés `.env` posées : Unsplash ✓ (photos vision board `source: unsplash`), Mammouth (IA) ✓, Brevo ✓, Google/Microsoft OAuth (redirect = prod), JWT+Fernet générés.
- Preview : compte démo **Thomas** accessible ; **jamais servi en production** (garde-fou par hôte).

## Branding appliqué (cette itération)
- Polices : **Corinthia** (eyebrow `.eyebrow`), **Fraunces** (H1/H2/H3 regular), **Poppins** (texte) — public + SaaS.
- Site public (scopé `.public-site`) : fond blanc, secondaire beige `#f8f3eb`, bleu dégradé `#215480→#001d50`, cartes blanches ombrées, bouton principal blanc/bordure beige, bouton secondaire dégradé bleu, badge promo rouge sang `#a10e10`.
- SaaS : neutres light passés au blanc/beige, **bleu SaaS inchangé** ; bleu du chat/modales **harmonisé** sur le navy canonique (`#1a3a6e / #102945 / #0c1d33`).
- Preview : `main.jsx` — auto-login Thomas (cockpit complet) + barre `Cockpit (Thomas) / Site public` ; **désactivé en production**.

## Modules ciblés pour 1re mise en ligne
Site public / Landing + Vision Board.

## Bugs / non-branchés connus
- `GET /api/chat/messages` et `/api/chat/decision` → 404 (routes inexistantes ; historique copilote non persisté ; le vrai copilote = `/api/growth/copilote`).
- Endpoints publics WP/branding → 500 quand WordPress non configuré (non bloquant, fallback).
- Mollie (paiements), WhatsApp Web, HeyGen, OAuth redirect prod : non branchés / à configurer.

## Roadmap prod (rappel)
1. Branding (fait, à affiner) 2. Landing publique + SEO/forms Brevo 3. Corriger 404 chat 4. Mollie 5. OAuth redirect prod 6. MySQL 7. Crons/worker 8. WhatsApp/HeyGen 9. Sécurité (rotation clés, CORS, image allégée, monitoring).
