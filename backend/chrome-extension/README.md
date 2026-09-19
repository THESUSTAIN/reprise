# MyExtension AI — Zayado Copilot (extension navigateur)

Couche IA contextuelle entre votre navigateur et votre Business OS.
Ouverture en **side-panel** : Hub IA, capture intelligente du contexte de page,
et actions directes vers le cockpit (tâche, opportunité, note, CRM).

## Installation (mode développeur)
1. Ouvrez `chrome://extensions`
2. Activez **Mode développeur**
3. **Charger l'extension non empaquetée** → sélectionnez ce dossier
   (ou décompressez `zayado-copilot-extension.zip`).
4. Cliquez sur l'icône Zayado dans la barre → le **side-panel** s'ouvre.

## Utilisation
1. **Connexion** : saisissez votre email MyExtension AI (ex. `thomas@zayado.fr`).
   En préproduction, le lien magique est consommé automatiquement.
2. **Contexte de page** : le titre, l'URL et la sélection sont pré-remplis.
3. **Analyser avec l'IA** : résumé + contact détecté + actions suggérées.
4. **Actions** : Créer une tâche / opportunité / note / Ajouter au CRM →
   enregistré dans votre cockpit (`/api/features/captures`).
5. **Ouvrir le Hub IA** : ouvre le Vision Board.

## Configuration
Base API par défaut : `https://strategy-brain-2.preview.emergentagent.com`.
Modifiable via `chrome.storage.local.zayado_api_base`.

## Endpoints utilisés
- `POST /api/auth/request-link` + `POST /api/auth/verify-link` (connexion)
- `POST /api/vision/brain/page-context` (analyse du contexte)
- `POST /api/features/captures` (capture → cockpit)
