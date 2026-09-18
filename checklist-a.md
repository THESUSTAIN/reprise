# Checklist-A — Refonte MyExtension

> Source unique de suivi (remplace l'ancien REORGANISATION.md, perdu).
> Mise à jour au fil de la conversation. ✓ = validé par l'utilisateur · ☐ = à faire

---

## 1. Marque & positionnement — ✓ VALIDÉ
- **Zayado** = la **marketplace** (marque mère) qui vend des outils.
- **MyExtension** = « l'extension vivante de votre business » = l'**outil SaaS vendu par Zayado**.
- **Soul** : aider l'entrepreneur à **tenir le cap**. On a tous une vision pro, mais beaucoup lâchent ; ce qui fait lâcher = le **mental**, le **corps**, l'**environnement**. L'app agit sur tout ça : organiser ses idées, **agir** les jours d'élan, être **relevé** les jours de doute, rester **ancré** à sa vision, intégrer la **foi** discrètement (sans perdre de clientes).
- **Positionnement (option a, à peaufiner)** : « L'IA qui vous aide à tenir le cap, et à ne jamais lâcher. Elle agit pour votre business, et prend soin de vous. »
- **Héros mis en avant** : l'**état du jour Élan / Refuge** — l'app s'adapte à l'utilisateur.

## 2. Architecture cockpit — ✓ structure validée (noms à confirmer)
4 destinations + Copilote :
- **Aujourd'hui** — état du jour (Élan/Refuge), intention de la semaine, actions préparées par l'IA, RDV, un mot pour tenir.
- **Ma Vision** — vision board éditable + modèles-planches.
- **Copilote** — l'IA agit & veille (idées→action, prospection, relances, finances, décisions). Les agents vivent ici.
- **Mon Refuge** — mental · corps · foi (coach mindset, énergie/anti-burnout, respiration, ancrage & foi, encouragements).

Rangés DEDANS (plus d'onglets séparés) : Mouvement, Croissance, DAF/Pilotage, Agents, Mindset, Contexte. Roadmap = déjà dans **Collaborateur**.

## 3. Menu « + » (rôle par rôle) — ☐ à implémenter (URLs réglables en admin)
- **Entrepreneur (business)** : Espace · Collaborer · Équiper mon business (→ URL admin, vers la boutique). *Rien d'autre.*
- **Chrétien** : + bouton **TheSustain** (→ URL admin).
- **Étudiant seul** (inscrit + pièces) : voit **uniquement Campus**.
- **Étudiant + indépendant** : **Business + Campus**.

## 4. Vision board — ✓ VALIDÉ
- Modèles-planches sélectionnables, **un à la fois**, page **aérée**, canvas **éditable** (ajout d'éléments).
- Modèles : Piliers de vie · Roadmap Q1–Q4 · Identitaire · Moodboard sensoriel · Cockpit stratégique · **Golden Circle** · **Pyramide de la clarté** · **Carte mentale** ✓.

## 5. Chat / Copilote — ✓ VALIDÉ
- **Ne pas supprimer** le chat latéral. **Pas dans le menu.**
- Emplacement : **bulle flottante en bas à droite** présente partout + destination **Copilote**.
- Copilote = **orchestrateur** : je parle / chips d'actions rapides → l'IA agit → résultats en **cartes dans le fil** avec « Voir le détail » qui ouvre la vue profonde (Pilotage, Mouvement…). On n'empile pas les pages dans le Copilote.

## 6. SEO / mots-clés — ✓ VALIDÉ
- Mots-clés surtout sur la **landing publique** (pas dans le cockpit). Le slogan reste émotionnel (option a).
- Cibler les features recherchées : *vision board entrepreneur*, *agent IA / assistant IA business*, *copilote IA entrepreneur*, *application organisation idées*, *pilotage financier / DAF*, *motivation / anti-procrastination entrepreneur*.

## 7. Nettoyage — ✓ FAIT
- Suppression de **43 anciennes pages** publiques/marketing/légales/boutique/simulateurs non utilisées (orphelines, non importées).
- Suppression des notes obsolètes (README public, deploy notes).
- Public actif conservé temporairement : `PublicHome`, `VisionBoardPublic` (seront refaits dans la refonte publique).

---

## Reste à faire (ordre proposé)
- ☐ **Maquette visuelle** « Aujourd'hui » (Élan/Refuge) + nav 4 — à valider avant branchement
- ☐ Nouvelle **nav cockpit** (4 destinations) + ranger l'existant dedans
- ☐ **Menu « + »** rôle par rôle + réglages **admin** (URLs Espace / Boutique / TheSustain)
- ☐ **Vision board** éditable + modèles (dont carte mentale, Golden Circle, Pyramide de clarté)
- ☐ Page **Aujourd'hui** adaptative pilotée par l'IA
- ☐ **Copilote** orchestrateur (capacités + cartes résultats + liens détail)
- ☐ Refonte **site public** (landing SEO)
- ☐ Corriger **404 `/api/chat/messages`** (persistance copilote) — connu
- ☐ Backlog prod : OAuth prod, Mollie, MySQL, rotation des secrets
