# Déploiement Railway — `/app/public-site`

Tout est déjà prêt côté code. Voici les étapes côté Railway :

## 1. Créer le service Railway

1. Va sur https://railway.app/dashboard
2. Sélectionne ton projet Zayado existant (ou crée-en un)
3. Clique **"+ New"** → **"Empty Service"**
4. Renomme-le : `public-site` (ou `zayado-website`)

## 2. Brancher la source

Tu as 2 options :

### Option A — GitHub (recommandée)
1. Pousse `/app/public-site` sur un repo GitHub (via "Save to GitHub" dans Emergent)
2. Sur Railway → service **public-site** → **Settings** → **Source** → **Connect Repo** → choisis le repo
3. **Root Directory** → `public-site` (si tu pousses tout le monorepo) OU `/` (si tu pousses seulement `/app/public-site`)

### Option B — CLI Railway
```bash
cd /app/public-site
railway login
railway link  # link to your project
railway up
```

## 3. Configurer les variables d'environnement

Sur Railway → service `public-site` → **Variables** → ajoute exactement ces 3 lignes :

```
VITE_API_URL = https://<ton-backend-railway-url>.up.railway.app
VITE_SAAS_URL = https://app.zayado.net
VITE_WP_URL = https://cms.zayado.net
```

> ⚠️ Important : `VITE_API_URL` doit pointer vers **le service backend Zayado** (celui qui sert l'API FastAPI). Si ton backend tourne déjà sur Railway, c'est l'URL publique de ce service. Vérifie qu'il a CORS autorisant `zayado.net`.

## 4. Build & Start commands

Railway détecte automatiquement Vite via Nixpacks grâce au `railway.json` :
```json
{
  "build": { "buildCommand": "yarn install && yarn build" },
  "deploy": { "startCommand": "yarn start" }
}
```
`yarn start` lance `vite preview --host 0.0.0.0 --port $PORT` (PORT injecté par Railway).

## 5. Domaine personnalisé

1. Service `public-site` → **Settings** → **Networking** → **Custom Domain**
2. Ajoute `zayado.net` (et/ou `www.zayado.net`)
3. Railway te donne un enregistrement DNS de type CNAME ou A à ajouter chez ton registrar (OVH / Cloudflare / etc.)
4. Une fois propagé (5-30 min), `https://zayado.net` sert ta Landing

## 6. CORS côté backend

Sur le service backend Railway, ajoute dans **Variables** :
```
CORS_ORIGINS = https://zayado.net,https://www.zayado.net,https://app.zayado.net
```
Puis **Restart** le service backend. (déjà supporté par `/app/backend/server.py`)

## 7. Vérification

Après déploiement :
- `https://zayado.net/` → Landing
- `https://zayado.net/#/boutique` → Boutique avec produits live
- `https://zayado.net/#/tarifs` → Tarifs
- Si tu modifies un texte dans WP Admin → 30s plus tard tu le vois en live

## 8. Coût Railway

Pour un site statique Vite : **~0.50 €/mois** (très peu de CPU/RAM, juste le serveur Vite preview qui sert les fichiers statiques compilés).

## Build URL avant déploiement

Pour tester en local que le build fonctionne :
```bash
cd /app/public-site
yarn install
yarn build
yarn start  # → http://localhost:4173
```

---

## ⚙️ Architecture finale en prod

```
zayado.net              → Railway service "public-site"  (Vite preview)
                                ↓ fetch
app.zayado.net          → Railway service "saas-app" (le cockpit, ton React actuel)
                                ↓ /api/*
api.zayado.net          → Railway service "backend" (FastAPI)
                                ↓ HTTP
cms.zayado.net          → Hostinger / Plesk (WordPress, source unique de contenu)
```

WordPress = moteur. Cockpit = pilote. Public-site = vitrine. Tout converge proprement.
