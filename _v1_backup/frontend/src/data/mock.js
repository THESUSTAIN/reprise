// Centralized mocked data — structured to be swapped for a real API layer later.
// couche services isolée : chaque module lit ces objets via des sélecteurs simples.

export const user = {
  firstName: "Sarah",
  lastName: "Lemoine",
  role: "Solopreneure · Conseil & Stratégie",
  avatar:
    "https://images.unsplash.com/photo-1614786269829-d24616faf56d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1Mjh8MHwxfHNlYXJjaHwxfHxzb2xvcHJlbmV1ciUyMGV4ZWN1dGl2ZSUyMHdvbWFuJTIwZGFyayUyMGJhY2tncm91bmR8ZW58MHx8fHwxNzg5MzQ0NDgyfDA&ixlib=rb-4.1.0&q=85",
  company: "MyExtension",
  energyToday: 78,
};

export const inspirations = [
  { id: 1, quote: "Le succès, c'est d'aller d'échec en échec sans perdre son enthousiasme.", author: "Winston Churchill" },
  { id: 2, quote: "Fais de ta vie un rêve, et d'un rêve une réalité.", author: "Antoine de Saint-Exupéry" },
  { id: 3, quote: "La discipline est le pont entre les objectifs et les accomplissements.", author: "Jim Rohn" },
  { id: 4, quote: "Ne comptez pas les jours, faites que les jours comptent.", author: "Mohamed Ali" },
];

export const kpis = [
  { id: "ca", key: "ca-du-mois", label: "CA du mois", value: "14 250 €", delta: "+18%", trend: "up", accent: "gold",
    spark: [8,9,7,11,10,12,14].map((v, i) => ({ x: i, y: v })) },
  { id: "tresorerie", key: "tresorerie", label: "Trésorerie nette", value: "31 900 €", delta: "+6%", trend: "up", accent: "emerald",
    spark: [22,24,23,26,28,30,31].map((v, i) => ({ x: i, y: v })) },
  { id: "prospects", key: "prospects", label: "Prospects actifs", value: "23", delta: "+4", trend: "up", accent: "cyan",
    spark: [12,14,15,17,19,21,23].map((v, i) => ({ x: i, y: v })) },
  { id: "bienetre", key: "bien-etre", label: "Score bien-être", value: "78/100", delta: "-3", trend: "down", accent: "rose",
    spark: [82,80,84,79,77,80,78].map((v, i) => ({ x: i, y: v })) },
];

export const trajectory = [
  { id: "today", horizon: "Aujourd'hui", title: "Ancrer les fondations", tasks: [
    { id: "t1", label: "Valider la proposition Groupe Meltis", done: true },
    { id: "t2", label: "Relancer 3 prospects tièdes", done: true },
    { id: "t3", label: "Bloc profond 90 min — offre signature", done: false },
  ]},
  { id: "90j", horizon: "90 jours", title: "Stabiliser le socle récurrent", tasks: [
    { id: "t4", label: "Atteindre 18 k€ de MRR", done: false },
    { id: "t5", label: "Lancer l'offre d'accompagnement trimestriel", done: false },
  ]},
  { id: "1an", horizon: "1 an", title: "Devenir une référence de niche", tasks: [
    { id: "t6", label: "3 partenariats stratégiques signés", done: false },
    { id: "t7", label: "Communauté de 1 000 abonnés qualifiés", done: false },
  ]},
  { id: "3ans", horizon: "3 ans", title: "Liberté & impact", tasks: [
    { id: "t8", label: "Studio de 3 personnes, 250 k€ / an", done: false },
    { id: "t9", label: "Programme phare autoportant", done: false },
  ]},
];

export const alignmentScore = 82;

export const prospectsDonut = [
  { name: "Conseil", value: 9, color: "#D4AF37" },
  { name: "Formation", value: 6, color: "#10B981" },
  { name: "Coaching", value: 5, color: "#06B6D4" },
  { name: "Partenariat", value: 3, color: "#A78BFA" },
];

export const prospects12m = [
  "Jan","Fév","Mar","Avr","Mai","Juin","Juil","Août","Sep","Oct","Nov","Déc",
].map((m, i) => ({ mois: m, nouveaux: [12,9,14,11,16,13,18,10,20,17,21,23][i], gagnes: [3,2,4,3,5,4,6,3,7,5,8,9][i] }));

export const copilote = {
  aiWorkPercent: 64,
  pending: 4,
  validated: 37,
  timeSavedHours: 12.5,
};

export const recentActivity = [
  { id: 1, icon: "check", label: "Facture #2043 encaissée (2 400 €)", time: "il y a 32 min", tone: "emerald" },
  { id: 2, icon: "mail", label: "Nouveau prospect via LinkedIn — Groupe Aria", time: "il y a 1 h", tone: "cyan" },
  { id: 3, icon: "sparkles", label: "Le Copilote a rédigé une relance pour Meltis", time: "il y a 2 h", tone: "gold" },
  { id: 4, icon: "alert", label: "Facture #2038 en retard de 6 jours", time: "il y a 4 h", tone: "rose" },
];

export const deliverables = [
  { id: "d1", title: "Relance prospect — Groupe Meltis", type: "Email", confidence: 92, status: "pending",
    preview: "Bonjour Julien, je reviens vers vous suite à notre échange de mardi. J'ai préparé une proposition ajustée à votre budget Q3…" },
  { id: "d2", title: "Post LinkedIn — offre signature", type: "Contenu", confidence: 87, status: "pending",
    preview: "3 signaux qui montrent qu'il est temps de structurer votre activité (et comment je le fais avec mes clients)…" },
  { id: "d3", title: "Récap financier hebdo", type: "Note DAF", confidence: 95, status: "pending",
    preview: "Trésorerie saine (+6%). 1 facture en retard à relancer. Marge nette à 61%. Objectif MRR : 84% atteint." },
  { id: "d4", title: "Devis — Atelier stratégie Aria", type: "Devis", confidence: 78, status: "pending",
    preview: "Atelier d'une journée + 2 suivis. Montant suggéré : 2 900 € HT. Créneau proposé : semaine du 24." },
];

export const dayProgram = [
  { id: 1, time: "09:00", label: "Bloc profond — offre signature", tag: "Focus", done: true },
  { id: 2, time: "11:30", label: "Appel découverte — Groupe Aria", tag: "Vente", done: true },
  { id: 3, time: "14:00", label: "Relances prospects tièdes", tag: "Croissance", done: false },
  { id: 4, time: "16:30", label: "Revue financière hebdo", tag: "Pilotage", done: false },
  { id: 5, time: "18:00", label: "Marche + gratitude", tag: "Bien-être", done: false },
];

export const weekEnergy = [
  { jour: "Lun", energie: 72 },
  { jour: "Mar", energie: 80 },
  { jour: "Mer", energie: 68 },
  { jour: "Jeu", energie: 84 },
  { jour: "Ven", energie: 78 },
  { jour: "Sam", energie: 90 },
  { jour: "Dim", energie: 65 },
];

export const readingList = [
  { id: 1, title: "L'Effet Cumulé", author: "Darren Hardy", minutes: 12, tag: "Discipline" },
  { id: 2, title: "Deep Work", author: "Cal Newport", minutes: 9, tag: "Focus" },
  { id: 3, title: "Building a StoryBrand", author: "Donald Miller", minutes: 15, tag: "Marketing" },
];

// ---- Copilote chat ----
export const copiloteThread = [
  { id: 1, role: "assistant", text: "Bonjour Sarah 👋 J'ai analysé votre semaine. Vous avez 4 livrables prêts à valider et 3 prospects tièdes à relancer. Par quoi commence-t-on ?" },
  { id: 2, role: "user", text: "Prépare une relance pour Groupe Meltis." },
  { id: 3, role: "assistant", text: "C'est fait. J'ai rédigé une relance chaleureuse et orientée valeur, ajustée à leur budget Q3. Vous pouvez la valider dans les livrables. Souhaitez-vous que je programme l'envoi demain 9h ?" },
];

export const copiloteSuggestions = [
  "Résume ma situation financière",
  "Prépare mes relances de la semaine",
  "Quels prospects prioriser aujourd'hui ?",
  "Rédige un post LinkedIn sur mon offre",
];

// ---- Vision ----
export const vision = {
  vision: "Aider 1 000 solopreneurs à bâtir une activité alignée, rentable et sereine d'ici 2030.",
  mission: "Transformer l'expertise solo en système clair, en remplaçant le chaos par la clarté.",
  values: ["Clarté", "Intégrité", "Liberté", "Impact durable", "Sérénité"],
  verse: "« Tout ce que vous faites, faites-le de bon cœur, comme pour l'essentiel. » — Colossiens 3:23",
};

export const swot = {
  forces: ["Expertise reconnue", "Réseau qualifié", "Offre signature claire"],
  faiblesses: ["Dépendance à 2 gros clients", "Temps admin trop élevé"],
  opportunites: ["Demande en conseil solo en hausse", "Partenariats formation"],
  menaces: ["Concurrence low-cost", "Cycles de vente longs"],
};

export const wins = [
  "Meilleur mois de CA depuis le lancement 🎉",
  "Un client t'a recommandée spontanément",
  "3 semaines de rituel matinal tenu",
  "Tu as dit non à un projet non aligné",
];

// ---- Croissance / pipeline ----
export const pipeline = {
  Nouveaux: [
    { id: "p1", name: "Groupe Aria", value: 2900, score: 78, tag: "Atelier" },
    { id: "p2", name: "Studio Nova", value: 1500, score: 61, tag: "Coaching" },
  ],
  Échange: [
    { id: "p3", name: "Meltis SAS", value: 6200, score: 92, tag: "Conseil" },
    { id: "p4", name: "Clara Béraud", value: 1200, score: 70, tag: "Formation" },
  ],
  Proposition: [
    { id: "p5", name: "Lumen Agency", value: 4800, score: 85, tag: "Conseil" },
  ],
  "Négo": [
    { id: "p6", name: "Groupe Vertu", value: 9000, score: 88, tag: "Accompagnement" },
  ],
  "Gagnés": [
    { id: "p7", name: "Atelier Ébène", value: 3400, score: 100, tag: "Conseil" },
    { id: "p8", name: "Maison Kova", value: 2400, score: 100, tag: "Formation" },
  ],
};

// ---- Pilotage / DAF ----
export const daf = {
  tresorerie: 31900,
  margeNette: 61,
  facturesRetard: 1,
  runwayMonths: 8,
  cashflow: ["Jan","Fév","Mar","Avr","Mai","Juin"].map((m, i) => ({
    mois: m, entrees: [9,11,10,14,13,16][i] * 1000, sorties: [6,7,6,8,7,9][i] * 1000,
  })),
  invoices: [
    { id: "#2043", client: "Atelier Ébène", montant: 2400, statut: "Payée", echeance: "12 juin" },
    { id: "#2041", client: "Maison Kova", montant: 2400, statut: "Payée", echeance: "08 juin" },
    { id: "#2038", client: "Studio Nova", montant: 1500, statut: "En retard", echeance: "04 juin" },
    { id: "#2044", client: "Lumen Agency", montant: 4800, statut: "En attente", echeance: "28 juin" },
  ],
  alerts: [
    { id: 1, tone: "rose", text: "Facture #2038 en retard de 6 jours — relance recommandée." },
    { id: 2, tone: "gold", text: "Objectif MRR à 84% : encore 1 600 € pour atteindre le palier." },
    { id: 3, tone: "emerald", text: "Marge nette solide à 61% — au-dessus de ta cible de 55%." },
  ],
  goals: [
    { id: 1, label: "MRR 18 000 €", progress: 84 },
    { id: 2, label: "Réserve 3 mois de charges", progress: 92 },
    { id: 3, label: "Réduire temps admin à 4h/sem", progress: 58 },
  ],
};

// ---- Bien-être ----
export const wellbeing = {
  energyToday: 78,
  streakDays: 21,
  focusMinutes: 320,
  rituals: [
    { id: 1, label: "Réveil sans écran", done: true },
    { id: 2, label: "10 min de respiration", done: true },
    { id: 3, label: "Marche 20 min", done: false },
    { id: 4, label: "Journal du soir", done: false },
  ],
  signals: [
    { id: 1, tone: "gold", text: "3 journées à +9h détectées cette semaine — pense à un vrai break." },
    { id: 2, tone: "emerald", text: "Ton sommeil s'est amélioré de 12% depuis le rituel du soir." },
  ],
  moodWeek: [
    { jour: "Lun", humeur: 3 }, { jour: "Mar", humeur: 4 }, { jour: "Mer", humeur: 2 },
    { jour: "Jeu", humeur: 4 }, { jour: "Ven", humeur: 3 }, { jour: "Sam", humeur: 5 }, { jour: "Dim", humeur: 4 },
  ],
};

// ---- Contexte ----
export const contexte = {
  echeances: [
    { id: 1, label: "Déclaration TVA", date: "20 juin", tone: "rose" },
    { id: 2, label: "Renouvellement offre Meltis", date: "24 juin", tone: "gold" },
    { id: 3, label: "Webinaire partenaire", date: "27 juin", tone: "cyan" },
  ],
  priorites: [
    { id: 1, label: "Signer Groupe Vertu (9 000 €)", impact: "Élevé" },
    { id: 2, label: "Finaliser offre signature", impact: "Élevé" },
    { id: 3, label: "Automatiser les relances", impact: "Moyen" },
  ],
  infos: [
    { id: 1, label: "Nouveau dispositif d'aide à la formation pro disponible." },
    { id: 2, label: "Ton secteur : +14% de demande en conseil solo ce trimestre." },
  ],
};

// ---- Mindset ----
export const mindsetDecisions = [
  { id: 1, title: "Grand projet agence — 15 k€", context: "Beaucoup de prestige mais 60% de mon temps sur 3 mois.", suggestion: "pivoter",
    note: "Aligné financièrement mais risque de me couper de mon offre signature." },
  { id: 2, title: "Baisser mes tarifs pour Studio Nova", context: "Client sympathique mais budget serré.", suggestion: "refuser",
    note: "Contraire à mon positionnement premium et à ma valeur Intégrité." },
  { id: 3, title: "Partenariat formation avec Lumen", context: "Audience alignée, revenus récurrents possibles.", suggestion: "accepter",
    note: "Renforce la vision 1 an et diversifie les revenus." },
];

// ---- Vision Board ----
export const balanceWheel = [
  { domaine: "Finances", score: 8 },
  { domaine: "Business", score: 7 },
  { domaine: "Santé", score: 6 },
  { domaine: "Relations", score: 7 },
  { domaine: "Croissance perso", score: 9 },
  { domaine: "Sérénité", score: 6 },
];

export const roadmapQuarters = [
  { q: "Q1", theme: "Fondations", items: ["Offre signature", "Système de relances", "Rituels ancrés"] },
  { q: "Q2", theme: "Traction", items: ["MRR 18 k€", "2 partenariats", "Communauté 500"] },
  { q: "Q3", theme: "Effet de levier", items: ["Programme phare", "Automations", "Contenu régulier"] },
  { q: "Q4", theme: "Consolidation", items: ["Réserve 3 mois", "Bilan & vision 2027", "Recrutement freelance"] },
];

export const moodboard = [
  { id: 1, query: "calm morning workspace", label: "Matins clairs" },
  { id: 2, query: "mountain summit sunrise", label: "Sommets" },
  { id: 3, query: "minimalist reading nook", label: "Recul & lecture" },
  { id: 4, query: "ocean horizon serene", label: "Liberté" },
  { id: 5, query: "warm candle journaling", label: "Ancrage" },
  { id: 6, query: "green plants natural light", label: "Énergie douce" },
];

// ---- Agenda ----
export const agendaSlots = [
  { id: 1, day: "Lun", time: "10:00", label: "Découverte — Aria", type: "vente", qualified: true },
  { id: 2, day: "Lun", time: "15:00", label: "Bloc profond", type: "focus", qualified: false },
  { id: 3, day: "Mar", time: "11:00", label: "Suivi — Vertu", type: "vente", qualified: true },
  { id: 4, day: "Mer", time: "09:30", label: "Contenu LinkedIn", type: "croissance", qualified: false },
  { id: 5, day: "Jeu", time: "14:00", label: "Atelier Lumen", type: "vente", qualified: true },
  { id: 6, day: "Ven", time: "16:00", label: "Revue hebdo IA", type: "pilotage", qualified: false },
];

export const reminderCascade = [
  { id: 1, channel: "Email", delay: "J-2", status: "envoyé" },
  { id: 2, channel: "SMS", delay: "J-1", status: "planifié" },
  { id: 3, channel: "WhatsApp", delay: "H-3", status: "planifié" },
  { id: 4, channel: "Appel Copilote", delay: "H-1", status: "en attente" },
];

export const weeklyDebrief = [
  "6 rendez-vous tenus, 1 no-show (taux 86%).",
  "Meilleur créneau de conversion : mardi 11h.",
  "Suggestion : bloque 2 matinées de focus la semaine prochaine.",
];
