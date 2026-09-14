# Zayado — Public site (zayado.net)

Public-facing storefront and content site for Zayado. Pulls products + blog from WordPress (cms.zayado.net) read-only and links users back to the cockpit (app.zayado.net) for sign-up.

## Stack
- React 18 + Vite 5
- React Router 6
- Tailwind CSS 3
- lucide-react icons

## Local dev
```bash
cd /app/public-site
yarn install
yarn dev           # http://localhost:5173
```

## Build & preview
```bash
yarn build         # → dist/
yarn start         # vite preview on $PORT (default 4173)
```

## Environment variables
Copy `.env.example` to `.env` and fill:
- `VITE_API_URL` — Zayado backend (FastAPI) e.g. `https://api.zayado.net`. Used for the `/api/public/contact` form.
- `VITE_SAAS_URL` — Cockpit app URL e.g. `https://app.zayado.net`. Used for all "Cockpit" / "Démarrer" CTAs.
- `VITE_WP_URL` — WordPress CMS URL e.g. `https://cms.zayado.net`. Used to fetch products + blog posts read-only.

## Railway deploy
The `railway.json` at the root tells Railway to use Nixpacks with:
```
yarn install && yarn build   # build
yarn start                   # start (vite preview on $PORT)
```

In the Railway project:
1. Create a new service from this directory (`/app/public-site`).
2. Set the env vars above (Variables tab).
3. Add a public domain (or attach `zayado.net`).

## Architecture
- Single source of truth: **WordPress (cms.zayado.net)** — products, posts, legal pages.
- The cockpit (app.zayado.net) is the **admin/master** : creating a product there pushes to WP via `/api/wp/products`.
- The public site only **reads** from WP REST API + WooCommerce REST API.
- Checkout stays on WooCommerce (`/produit/{slug}/`).

## Pages
- `/` — Landing
- `/boutique` — Product grid (WC)
- `/boutique/:slug` — Product detail (WC)
- `/tarifs` — SaaS pricing → cockpit
- `/blog` — Posts (WP)
- `/a-propos`, `/contact`
- `/mentions-legales`, `/confidentialite`, `/cgv` — pulled from WP pages by slug

## Legacy
Raw `.jsx` files from `a-main.zip` are preserved in `src/pages/legacy/` for future migration.
