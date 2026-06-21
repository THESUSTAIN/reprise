import {
  LayoutDashboard, Compass, TrendingUp, FolderKanban, Plug, Settings, Sparkles, Target,
} from "lucide-react";

/**
 * Contenu des popups de bienvenue, par page.
 * La clé correspond au `pageKey` passé à useWelcomeModal(pageKey).
 */
export const WELCOME_CONTENT = {
  dashboard: {
    icon: LayoutDashboard,
    title: "Bienvenue sur votre Cockpit",
    description: "Votre vue d'ensemble quotidienne — métriques clés, livrables IA à valider et bibliothèque de documents, tout au même endroit.",
    points: [
      "Vos métriques de la semaine, dès que votre banque est connectée",
      "Les livrables générés par votre Collaborateur IA arrivent ici pour validation",
      "Un clic sur le Collaborateur pour avancer sur ce qui compte vraiment",
    ],
  },

  vision: {
    icon: Compass,
    title: "Bienvenue sur Vision Board",
    description: "L'endroit pour clarifier votre cap : pourquoi vous faites ce que vous faites, pour qui, et où vous allez.",
    points: [
      "Renseignez votre Pourquoi, votre Offre, votre Cible et votre objectif de CA",
      "Ces informations nourrissent chaque conversation avec votre Collaborateur IA",
      "Un badge sur le Collaborateur vous guidera tant que ces sections sont vides",
    ],
  },

  croissance: {
    icon: TrendingUp,
    title: "Bienvenue sur Croissance",
    description: "Votre centre de pilotage de l'acquisition. Chaque signal détecté par votre Growth Agent atterrit ici.",
    points: [
      "Leads classés par score de pertinence (1–10)",
      "Génération de réponses IA en un clic, dans votre voix",
      "Suivez votre pipeline du premier contact à la conversion",
    ],
  },

  pilotage: {
    icon: Target,
    title: "Bienvenue sur Pilotage",
    description: "Votre chiffre d'affaires, vos objectifs et votre progression — basés sur vos données bancaires réelles.",
    points: [
      "Connectez votre banque pour un suivi automatique du CA",
      "Visualisez votre progression vers votre objectif mensuel",
      "Recevez des recommandations IA pour ajuster votre trajectoire",
    ],
  },

  bienetre: {
    icon: Sparkles,
    title: "Bienvenue sur Bien-être",
    description: "Votre rituel quotidien d'énergie : un check-in de 2 minutes pour piloter votre forme et prévenir le burn-out.",
    points: [
      "Évaluez chaque matin votre énergie, votre clarté mentale et votre stress",
      "Recevez la charge de travail suggérée par votre Co-pilote",
      "Suivez votre énergie et votre stress sur les 30 derniers jours",
    ],
  },

  espace: {
    icon: FolderKanban,
    title: "Bienvenue dans votre Espace de travail",
    description: "Missions, processus et documents — votre quotidien d'exécution, organisé et soutenu par l'IA.",
    points: [
      "Définissez votre priorité unique du jour",
      "Laissez l'IA générer pitchs, emails et documents pour vous",
      "Importez vos fichiers ou connectez Google Drive / OneDrive pour une synchronisation automatique",
    ],
  },

  integrations: {
    icon: Plug,
    title: "Bienvenue sur Intégrations",
    description: "Connectez les outils que vous utilisez déjà — votre banque, votre cloud, WhatsApp — pour que Zayado travaille avec vos données réelles.",
    points: [
      "Google Drive et OneDrive pour synchroniser vos documents",
      "Votre banque pour un suivi automatique de votre chiffre d'affaires",
      "WhatsApp Business pour vos relances clients",
    ],
  },

  parametres: {
    icon: Settings,
    title: "Bienvenue dans vos Paramètres",
    description: "Personnalisez votre profil, votre abonnement et vos préférences pour que Zayado s'adapte à votre façon de travailler.",
    points: [
      "Complétez votre profil pour des conseils IA plus précis",
      "Gérez votre offre et votre facturation",
      "Activez ou désactivez les notifications selon vos préférences",
    ],
  },

  collaborateur: {
    icon: Sparkles,
    title: "Bienvenue auprès de votre Collaborateur IA",
    description: "Votre copilote business. Il se souvient de vos dernières conversations, vos décisions et vos blocages.",
    points: [
      "Posez vos questions, demandez un email, une analyse, un plan d'action",
      "Il relit vos 10 derniers échanges à chaque nouvelle session",
      "Un badge orange apparaît quand une section de votre profil mérite votre attention",
    ],
  },
};
