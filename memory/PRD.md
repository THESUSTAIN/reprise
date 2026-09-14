# PRD — Vision Atelier (Vision Board Showcase Gallery)

## Original problem statement
Générer le frontend d'une vitrine présentant 5 modèles de vision board sous forme de planches d'inspiration :
1. Piliers de Vie (Roue de l'Équilibre) — holistique
2. Feuille de Route Chronologique (Roadmap Q1–Q4) — planification
3. Modèle Identitaire (Vision · Mission · Identité) — état d'esprit
4. Moodboard Émotionnel & Sensoriel (Ambiance & Énergie) — artistique
5. Cockpit Stratégique (Tableau de bord visuel) — stratégique

## User choices
- Galerie / vitrine des 5 modèles (pas d'édition)
- Images d'inspiration prédéfinies uniquement
- Style vibrant & artistique
- Avec backend + sauvegarde (favoris)
- Interface bilingue FR/EN

## Architecture
- **Frontend**: React 19, Tailwind, framer-motion, lucide-react, sonner. Single-page shell with AppContext (lang, theme, favorites, session_id).
- **Backend**: FastAPI + MongoDB. Endpoints: `GET /api/templates`, `GET /api/favorites/{session_id}`, `POST /api/favorites/toggle`.
- **Persistence**: Favorites stored in Mongo per browser `session_id` (localStorage `vb_session`). No auth.

## User personas
- Personne cherchant l'inspiration pour créer son propre vision board.
- Entrepreneur / créatif comparant des approches de planification.

## Core requirements (static)
- Bilingual FR/EN across all content.
- Vibrant artistic aesthetic (clay/ochre/lilac/emerald/rose accents, grain texture, glassmorphism).
- 5 rich template detail views, each with a distinct interactive layout.
- Favorites saved to backend, filter tabs by category, light/dark theme.

## Implemented (2026-06)
- Header (brand, favorites counter, FR/EN toggle, theme toggle) — glass pill nav.
- Hero with stacked preview deck + animated CTA.
- Gallery with 6 filter tabs and 5 template cards (favorite heart, open detail).
- Full-screen detail views: Wheel of Balance (radial SVG + sectors), Roadmap Q1–Q4 timeline, Identity manifesto + affirmations, Sensory bento collage + palette/keywords/textures, Strategic cockpit (KPIs + milestones + team).
- Favorites side panel + sonner toasts + backend persistence.
- All backend + frontend flows tested 100% (iteration_1).

## Backlog
- P2: Downloadable/printable board blueprint (PDF).
- P2: More inspiration images per template (mini-gallery inside detail).
- P2: Shareable link to a chosen template.
- P2: ESC/backdrop close (done); a11y refinements.

## Next tasks
- Await user feedback on content/wording and visual direction.
