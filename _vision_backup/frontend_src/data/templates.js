// Rich bilingual content for the 5 vision board templates.
// Helper: pick localized value -> L(obj, lang)
export const L = (obj, lang) => (obj && typeof obj === "object" && ("fr" in obj) ? obj[lang] : obj);

export const templates = [
  {
    id: "pillars",
    category: "holistic",
    accent: "#E05A47",
    accentVar: "clay",
    name: { fr: "Les Piliers de Vie", en: "Life Pillars" },
    subtitle: { fr: "La Roue de l'Équilibre", en: "The Wheel of Balance" },
    tagline: {
      fr: "Une croissance harmonieuse à travers vos cinq secteurs clés.",
      en: "Harmonious growth across your five core sectors.",
    },
    description: {
      fr: "Une approche holistique qui divise votre vision en secteurs de vie essentiels. Chaque pilier reçoit la même attention pour éviter les déséquilibres et cultiver une vie entière, pas seulement une carrière.",
      en: "A holistic approach that divides your vision into essential life sectors. Each pillar gets equal attention to avoid imbalance and cultivate a whole life, not just a career.",
    },
    bestFor: { fr: "Équilibre de vie & développement personnel", en: "Life balance & personal growth" },
    quote: {
      fr: "L'équilibre n'est pas une destination, c'est une pratique quotidienne.",
      en: "Balance is not a destination, it is a daily practice.",
    },
    heroImage:
      "https://images.unsplash.com/photo-1600618528240-fb9fc964b853?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200",
    cardImage:
      "https://images.unsplash.com/photo-1570506097811-83004c7e4691?crop=entropy&cs=srgb&fm=jpg&q=85&w=800",
    sectors: [
      { icon: "briefcase", color: "#E05A47", name: { fr: "Carrière", en: "Career" }, focus: { fr: "Impact & sens professionnel", en: "Impact & professional meaning" }, goals: { fr: ["Prendre un poste à responsabilité", "Lancer un projet qui compte"], en: ["Step into a leadership role", "Launch a project that matters"] } },
      { icon: "wallet", color: "#D97706", name: { fr: "Finances", en: "Finances" }, focus: { fr: "Liberté & sécurité", en: "Freedom & security" }, goals: { fr: ["Constituer 6 mois d'épargne", "Diversifier mes revenus"], en: ["Build a 6-month safety net", "Diversify my income streams"] } },
      { icon: "heart-pulse", color: "#10B981", name: { fr: "Santé & Bien-être", en: "Health & Wellness" }, focus: { fr: "Énergie & vitalité", en: "Energy & vitality" }, goals: { fr: ["Bouger 4 fois par semaine", "Un sommeil réparateur"], en: ["Move 4 times a week", "Restorative sleep"] } },
      { icon: "users", color: "#8B5CF6", name: { fr: "Relations & Amour", en: "Relationships & Love" }, focus: { fr: "Liens profonds & présence", en: "Deep bonds & presence" }, goals: { fr: ["Nourrir mes amitiés clés", "Temps de qualité en famille"], en: ["Nurture my key friendships", "Quality time with family"] } },
      { icon: "sparkles", color: "#EC4899", name: { fr: "Développement Personnel", en: "Personal Growth" }, focus: { fr: "Apprentissage & créativité", en: "Learning & creativity" }, goals: { fr: ["Lire 24 livres", "Apprendre une nouvelle compétence"], en: ["Read 24 books", "Learn a brand-new skill"] } },
    ],
  },
  {
    id: "roadmap",
    category: "planning",
    accent: "#D97706",
    accentVar: "ochre",
    name: { fr: "La Feuille de Route", en: "Chronological Roadmap" },
    subtitle: { fr: "Roadmap Temporelle Q1–Q4", en: "Temporal Roadmap Q1–Q4" },
    tagline: {
      fr: "Reliez vos rêves à des actions concrètes, trimestre par trimestre.",
      en: "Connect your dreams to concrete actions, quarter by quarter.",
    },
    description: {
      fr: "Idéal pour planifier l'année, ce modèle organise vos objectifs par trimestres. Chaque phase possède une intention claire et des jalons mesurables pour transformer l'ambition en progression réelle.",
      en: "Ideal for planning the year, this template organizes your goals by quarters. Each phase carries a clear intention and measurable milestones to turn ambition into real progress.",
    },
    bestFor: { fr: "Planification annuelle & objectifs mesurables", en: "Annual planning & measurable goals" },
    quote: {
      fr: "Un objectif sans échéance n'est qu'un souhait.",
      en: "A goal without a timeline is just a wish.",
    },
    heroImage:
      "https://images.unsplash.com/photo-1763046289892-857b83dc070f?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200",
    cardImage:
      "https://images.unsplash.com/photo-1499750310107-5fef28a66643?crop=entropy&cs=srgb&fm=jpg&q=85&w=800",
    quarters: [
      { q: "Q1", color: "#E05A47", title: { fr: "Structuration & Alignement", en: "Structure & Alignment" }, focus: { fr: "Poser des bases solides.", en: "Lay solid foundations." }, milestones: { fr: ["Clarifier la vision annuelle", "Mettre en place les rituels", "Auditer les finances"], en: ["Clarify the yearly vision", "Set up core rituals", "Audit the finances"] } },
      { q: "Q2", color: "#D97706", title: { fr: "Expansion & Action", en: "Expansion & Action" }, focus: { fr: "Passer à l'échelle.", en: "Scale things up." }, milestones: { fr: ["Lancer le projet principal", "Élargir le réseau", "Premiers résultats"], en: ["Launch the main project", "Grow the network", "First results"] } },
      { q: "Q3", color: "#8B5CF6", title: { fr: "Consolidation & Exploration", en: "Consolidation & Exploration" }, focus: { fr: "Ancrer et affiner.", en: "Anchor and refine." }, milestones: { fr: ["Optimiser ce qui marche", "Explorer une piste neuve", "Prendre du recul"], en: ["Optimize what works", "Explore a new lane", "Take a step back"] } },
      { q: "Q4", color: "#10B981", title: { fr: "Célébration & Bilan", en: "Celebration & Review" }, focus: { fr: "Récolter et préparer l'après.", en: "Harvest and prepare what's next." }, milestones: { fr: ["Mesurer les progrès", "Célébrer les victoires", "Préparer l'année suivante"], en: ["Measure the progress", "Celebrate the wins", "Prepare next year"] } },
    ],
  },
  {
    id: "identity",
    category: "mindset",
    accent: "#8B5CF6",
    accentVar: "lilac",
    name: { fr: "Le Modèle Identitaire", en: "The Identity Model" },
    subtitle: { fr: "Vision · Mission · Identité", en: "Vision · Mission · Identity" },
    tagline: {
      fr: "Concentrez-vous sur la personne que vous devez devenir.",
      en: "Focus on the person you need to become.",
    },
    description: {
      fr: "Ce tableau met en avant vos valeurs, votre posture, vos citations inspirantes et l'état d'esprit à adopter. On ne poursuit pas seulement des objectifs : on incarne une identité qui les rend inévitables.",
      en: "This board highlights your values, your posture, your inspiring quotes and the mindset to adopt. You don't just chase goals: you embody an identity that makes them inevitable.",
    },
    bestFor: { fr: "Alignement des valeurs & état d'esprit", en: "Values alignment & mindset" },
    quote: {
      fr: "Ne fixez pas d'objectifs. Devenez la personne pour qui ces objectifs sont naturels.",
      en: "Don't set goals. Become the person for whom those goals are natural.",
    },
    heroImage:
      "https://images.unsplash.com/photo-1542904990-579199bba13a?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200",
    cardImage:
      "https://images.unsplash.com/photo-1495001258031-d1b407bc1776?crop=entropy&cs=srgb&fm=jpg&q=85&w=800",
    columns: [
      { key: "identity", color: "#8B5CF6", title: { fr: "Identité — Qui je suis", en: "Identity — Who I am" }, items: { fr: ["Créateur·rice discipliné·e", "Calme sous pression", "Curieux·se et généreux·se"], en: ["A disciplined creator", "Calm under pressure", "Curious and generous"] } },
      { key: "values", color: "#E05A47", title: { fr: "Valeurs — Ce en quoi je crois", en: "Values — What I believe in" }, items: { fr: ["L'intégrité avant tout", "Le progrès plutôt que la perfection", "La bienveillance active"], en: ["Integrity above all", "Progress over perfection", "Active kindness"] } },
      { key: "mission", color: "#10B981", title: { fr: "Mission — Ce que j'accomplis", en: "Mission — What I accomplish" }, items: { fr: ["Créer un travail qui inspire", "Élever ceux qui m'entourent", "Laisser une trace utile"], en: ["Create work that inspires", "Lift those around me", "Leave a useful mark"] } },
    ],
    affirmations: {
      fr: ["Je suis à la hauteur de mes ambitions.", "Chaque jour, je choisis la discipline.", "Je mérite l'abondance que je crée."],
      en: ["I rise to my ambitions.", "Every day, I choose discipline.", "I deserve the abundance I create."],
    },
  },
  {
    id: "sensory",
    category: "artistic",
    accent: "#EC4899",
    accentVar: "rose",
    name: { fr: "Le Moodboard Sensoriel", en: "The Sensory Moodboard" },
    subtitle: { fr: "Ambiance & Énergie", en: "Atmosphere & Energy" },
    tagline: {
      fr: "Ancrez l'énergie, les couleurs et le ressenti que vous cultivez.",
      en: "Anchor the energy, colors and feeling you want to cultivate.",
    },
    description: {
      fr: "Une approche artistique qui privilégie les couleurs, les textures, les mots-clés et les images. Moins une liste d'objectifs qu'une atmosphère — le ressenti émotionnel que vous voulez habiter au quotidien.",
      en: "An artistic approach that prioritizes colors, textures, keywords and images. Less a list of goals than an atmosphere — the emotional feeling you want to inhabit every day.",
    },
    bestFor: { fr: "Créatifs & ancrage émotionnel", en: "Creatives & emotional anchoring" },
    quote: {
      fr: "Ressentez-le d'abord. Le reste suivra.",
      en: "Feel it first. The rest will follow.",
    },
    heroImage:
      "https://images.unsplash.com/photo-1547447134-cd3f5c716030?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200",
    cardImage:
      "https://images.unsplash.com/photo-1614053622765-81c37c617c20?crop=entropy&cs=srgb&fm=jpg&q=85&w=800",
    palette: ["#E05A47", "#D97706", "#F5D0A9", "#8B5CF6", "#10B981", "#1C1917"],
    keywords: {
      fr: ["Sérénité", "Audace", "Abondance", "Liberté", "Créativité", "Ancrage", "Lumière", "Élan"],
      en: ["Serenity", "Boldness", "Abundance", "Freedom", "Creativity", "Grounding", "Light", "Momentum"],
    },
    textures: {
      fr: ["Lin brut", "Or brossé", "Bois chaud", "Verre fumé"],
      en: ["Raw linen", "Brushed gold", "Warm wood", "Smoked glass"],
    },
    collage: [
      "https://images.unsplash.com/photo-1506143925201-0252c51780b0?crop=entropy&cs=srgb&fm=jpg&q=85&w=600",
      "https://images.unsplash.com/photo-1632613714614-e817d3814a8e?crop=entropy&cs=srgb&fm=jpg&q=85&w=600",
      "https://images.unsplash.com/photo-1620812097331-ff636155488f?crop=entropy&cs=srgb&fm=jpg&q=85&w=600",
      "https://images.unsplash.com/photo-1719938571041-daee17be1bb9?crop=entropy&cs=srgb&fm=jpg&q=85&w=600",
      "https://images.unsplash.com/photo-1461468611824-46457c0e11fd?crop=entropy&cs=srgb&fm=jpg&q=85&w=600",
    ],
  },
  {
    id: "strategic",
    category: "strategic",
    accent: "#10B981",
    accentVar: "emerald",
    name: { fr: "Le Cockpit Stratégique", en: "The Strategic Cockpit" },
    subtitle: { fr: "Tableau de Bord Visuel", en: "Visual Dashboard" },
    tagline: {
      fr: "Alliez inspiration visuelle et indicateurs de performance clairs.",
      en: "Combine visual inspiration with clear performance indicators.",
    },
    description: {
      fr: "Parfait pour les entrepreneurs, ce modèle relie la vision aux chiffres : objectifs financiers, jalons clés et stratégie d'équipe. Un cockpit pour piloter votre projet avec émotion et lucidité.",
      en: "Perfect for entrepreneurs, this template links vision to numbers: financial goals, key milestones and team strategy. A cockpit to steer your venture with both emotion and clarity.",
    },
    bestFor: { fr: "Entrepreneurs & fondateurs", en: "Entrepreneurs & founders" },
    quote: {
      fr: "Ce qui se mesure s'accomplit.",
      en: "What gets measured gets done.",
    },
    heroImage:
      "https://images.unsplash.com/photo-1505330622279-bf7d7fc918f4?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200",
    cardImage:
      "https://images.unsplash.com/photo-1499951360447-b19be8fe80f5?crop=entropy&cs=srgb&fm=jpg&q=85&w=800",
    kpis: [
      { color: "#10B981", value: "1 M€", label: { fr: "Chiffre d'affaires visé", en: "Target revenue" } },
      { color: "#D97706", value: "10 000", label: { fr: "Clients actifs", en: "Active customers" } },
      { color: "#8B5CF6", value: "40 %", label: { fr: "Marge nette", en: "Net margin" } },
      { color: "#E05A47", value: "12", label: { fr: "Membres de l'équipe", en: "Team members" } },
    ],
    milestones: [
      { status: "done", title: { fr: "Lancement du MVP", en: "MVP launch" } },
      { status: "active", title: { fr: "Levée de fonds seed", en: "Seed fundraising" } },
      { status: "next", title: { fr: "Expansion internationale", en: "International expansion" } },
      { status: "next", title: { fr: "Passer la barre du million", en: "Cross the million mark" } },
    ],
    team: {
      fr: ["Recruter un·e Head of Growth", "Structurer l'équipe produit", "Culture d'entreprise forte"],
      en: ["Hire a Head of Growth", "Structure the product team", "Build a strong company culture"],
    },
  },
];
