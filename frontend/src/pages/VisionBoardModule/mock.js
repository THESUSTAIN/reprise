// Données du module Vision Board (autonome, bilingue fr/en).
const IMG = {
  goals:   "https://images.unsplash.com/photo-1646931335361-e3c46150b11a?w=900&q=80",
  vibes:   "https://images.unsplash.com/photo-1495001258031-d1b407bc1776?w=900&q=80",
  goalsPen:"https://images.unsplash.com/photo-1610540604745-3e96fba9ccef?w=900&q=80",
  board:   "https://images.unsplash.com/photo-1686087350079-9f6ca138583c?w=900&q=80",
  peak:    "https://images.unsplash.com/photo-1571782605941-8c8fd0d43df6?w=900&q=80",
  fjord:   "https://images.unsplash.com/photo-1606664817180-00391bdfb9d0?w=900&q=80",
  hill:    "https://images.unsplash.com/photo-1492681290082-e932832941e6?w=900&q=80",
  victory: "https://images.unsplash.com/photo-1598601065215-751bf8798a2c?w=900&q=80",
  calm:    "https://images.unsplash.com/photo-1519638399535-1b036603ac77?w=900&q=80",
  city:    "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=900&q=80",
  travel:  "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=900&q=80",
  read1:   "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&q=80",
};

const CANVA = "https://www.canva.com/design/new";

export const BOARD_CENTER = { x: 660, y: 420, label: { fr: "MA VISION", en: "MY VISION" } };

export const BOARD_CARDS = [
  { id: "c1", type: "image", x: 220, y: 120, w: 220, h: 170, image: IMG.peak,
    title: { fr: "Liberté & grands espaces", en: "Freedom & wide open spaces" } },
  { id: "c2", type: "note", x: 1000, y: 150, w: 220, h: 130, color: "#D6A85F", important: true,
    title: { fr: "Objectif CA", en: "Revenue goal" },
    body: { fr: "Atteindre 100K€ de CA annuel d'ici 12 mois.", en: "Reach 100K€ annual revenue in 12 months." } },
  { id: "c3", type: "image", x: 1010, y: 350, w: 220, h: 170, image: IMG.travel,
    title: { fr: "Travailler depuis partout", en: "Work from anywhere" } },
  { id: "c4", type: "note", x: 220, y: 400, w: 220, h: 130, color: "#5e8a5a",
    title: { fr: "Équilibre", en: "Balance" },
    body: { fr: "Protéger mes matinées & mon sommeil.", en: "Protect my mornings & sleep." } },
  { id: "c5", type: "color", x: 470, y: 700, w: 230, h: 110,
    title: { fr: "Palette de marque", en: "Brand palette" }, colors: ["#0a1f4e", "#4a6a9e", "#DEC2A3", "#F1E2CC"] },
  { id: "c6", type: "image", x: 900, y: 650, w: 220, h: 160, image: IMG.city,
    title: { fr: "Rayonner en ville", en: "Shine in the city" } },
  { id: "c7", type: "note", x: 470, y: 130, w: 210, h: 120, color: "#8b6fbf",
    title: { fr: "Impact", en: "Impact" },
    body: { fr: "Aider 10 000 solopreneurs à s'aligner.", en: "Help 10,000 solopreneurs align." } },
  { id: "c8", type: "image", x: 250, y: 800, w: 220, h: 160, image: IMG.victory,
    title: { fr: "Célébrer les victoires", en: "Celebrate the wins" } },
  { id: "c9", type: "note", x: 560, y: 830, w: 230, h: 120, color: "#5e8a5a", important: true,
    title: { fr: "Salaire cible", en: "Target salary" },
    body: { fr: "Me verser 3 000€/mois de façon sereine.", en: "Pay myself 3,000€/mo calmly." } },
  { id: "c10", type: "image", x: 1030, y: 790, w: 210, h: 165, image: IMG.hill,
    title: { fr: "Nouveaux horizons", en: "New horizons" } },
];

export const BOARD_TOOLS = [
  { id: "text",   icon: "Type",       label: { fr: "Texte", en: "Text" } },
  { id: "image",  icon: "Image",      label: { fr: "Image", en: "Image" } },
  { id: "check",  icon: "ListChecks", label: { fr: "Liste", en: "List" } },
  { id: "link",   icon: "Link2",      label: { fr: "Lien", en: "Link" } },
  { id: "color",  icon: "Palette",    label: { fr: "Couleur", en: "Color" } },
  { id: "ai",     icon: "Sparkles",   label: { fr: "IA", en: "AI" } },
  { id: "ai-doc", icon: "FileText",   label: { fr: "AI Doc", en: "AI Doc" } },
];

export const PILLARS = [
  { id: "p1", icon: "TrendingUp", color: "#4a6a9e",
    title: { fr: "Croissance", en: "Growth" },
    description: { fr: "Développer un business rentable et durable.", en: "Build a profitable, sustainable business." },
    progress: 66,
    objectives: [
      { text: { fr: "Signer 3 clients récurrents", en: "Sign 3 recurring clients" }, done: true },
      { text: { fr: "Lancer une offre signature", en: "Launch a signature offer" }, done: true },
      { text: { fr: "Atteindre 10K€/mois", en: "Reach 10K€/month" }, done: false },
    ] },
  { id: "p2", icon: "HeartPulse", color: "#5e8a5a",
    title: { fr: "Bien-être", en: "Well-being" },
    description: { fr: "Préserver mon énergie et mon équilibre.", en: "Preserve my energy and balance." },
    progress: 50,
    objectives: [
      { text: { fr: "Rituel matinal quotidien", en: "Daily morning ritual" }, done: true },
      { text: { fr: "Coupure écran à 21h", en: "Screen cutoff at 9pm" }, done: false },
    ] },
  { id: "p3", icon: "Globe", color: "#DEC2A3",
    title: { fr: "Rayonnement", en: "Reach" },
    description: { fr: "Devenir une référence dans mon domaine.", en: "Become a reference in my field." },
    progress: 40,
    objectives: [
      { text: { fr: "Publier 2 contenus/semaine", en: "Publish 2 pieces/week" }, done: true },
      { text: { fr: "Atteindre 5K abonnés", en: "Reach 5K followers" }, done: false },
      { text: { fr: "Prise de parole publique", en: "Public speaking" }, done: false },
    ] },
  { id: "p4", icon: "Wallet", color: "#8b6fbf",
    title: { fr: "Liberté financière", en: "Financial freedom" },
    description: { fr: "Sécuriser mes revenus et investir.", en: "Secure income and invest." },
    progress: 30,
    objectives: [
      { text: { fr: "3 mois de trésorerie d'avance", en: "3 months of cash buffer" }, done: true },
      { text: { fr: "Automatiser 1 revenu passif", en: "Automate 1 passive income" }, done: false },
    ] },
];

export const VISION_BOOK = {
  cover: IMG.board,
  title: { fr: "Mon Vision Book 2026", en: "My Vision Book 2026" },
  subtitle: { fr: "La feuille de route de mes rêves", en: "The roadmap of my dreams" },
  pages: [
    { id: "b1", image: IMG.peak, category: { fr: "Ambition", en: "Ambition" },
      title: { fr: "Voir grand", en: "Think big" },
      body: { fr: "Chaque sommet atteint en ouvre un nouveau. Ma vision me guide plus haut.", en: "Every summit reached opens a new one. My vision guides me higher." } },
    { id: "b2", image: IMG.calm, category: { fr: "Équilibre", en: "Balance" },
      title: { fr: "Sérénité & focus", en: "Serenity & focus" },
      body: { fr: "Une énergie stable est le socle de la performance durable.", en: "Stable energy is the foundation of lasting performance." } },
    { id: "b3", image: IMG.travel, category: { fr: "Liberté", en: "Freedom" },
      title: { fr: "Travailler depuis partout", en: "Work from anywhere" },
      body: { fr: "Concevoir une activité qui me libère au lieu de m'enfermer.", en: "Design a business that frees me instead of confining me." } },
    { id: "b4", image: IMG.city, category: { fr: "Impact", en: "Impact" },
      title: { fr: "Rayonner", en: "Shine" },
      body: { fr: "Transmettre, inspirer, laisser une trace utile.", en: "Share, inspire, leave a useful mark." } },
  ],
};

export const MEMORY_HIGHLIGHTS = [
  { id: "h1", image: IMG.peak, label: { fr: "Sommets", en: "Summits" } },
  { id: "h2", image: IMG.fjord, label: { fr: "Évasion", en: "Escape" } },
  { id: "h3", image: IMG.victory, label: { fr: "Victoires", en: "Wins" } },
  { id: "h4", image: IMG.calm, label: { fr: "Sérénité", en: "Serenity" } },
  { id: "h5", image: IMG.city, label: { fr: "Ville", en: "City" } },
];

export const MEMORIES = [
  { id: "m1", image: IMG.victory, type: "reminder", timeAgo: { fr: "Il y a 1 an", en: "1 year ago" },
    title: { fr: "Ton premier client signé", en: "Your first signed client" },
    message: { fr: "Souviens-toi de ce jour — tu as prouvé que c'était possible.", en: "Remember this day — you proved it was possible." },
    cta: { fr: "Revivre", en: "Relive" } },
  { id: "m2", image: IMG.fjord, type: "memory", timeAgo: { fr: "Il y a 3 mois", en: "3 months ago" },
    title: { fr: "Ta retraite créative", en: "Your creative retreat" },
    message: { fr: "L'endroit où ta vision est devenue claire.", en: "The place where your vision became clear." },
    cta: { fr: "Ajouter au board", en: "Add to board" } },
];

export const NOTIF_SETTINGS = [
  { id: "n1", on: true, label: { fr: "Rappels de souvenirs", en: "Memory reminders" },
    desc: { fr: "Recevoir un souvenir marquant chaque semaine.", en: "Get a meaningful memory every week." } },
  { id: "n2", on: true, label: { fr: "Progrès des piliers", en: "Pillar progress" },
    desc: { fr: "Être notifié quand un objectif avance.", en: "Be notified when a goal moves forward." } },
  { id: "n3", on: false, label: { fr: "Inspiration quotidienne", en: "Daily inspiration" },
    desc: { fr: "Une image ou citation par jour.", en: "One image or quote per day." } },
];

export const TEMPLATE_CATEGORIES = [
  { id: "all",          label: { fr: "Tous", en: "All" } },
  { id: "vision",       label: { fr: "Vision", en: "Vision" } },
  { id: "strategy",     label: { fr: "Stratégie", en: "Strategy" } },
  { id: "productivity", label: { fr: "Productivité", en: "Productivity" } },
  { id: "creative",     label: { fr: "Créatif", en: "Creative" } },
];

export const STUDIO_PRESETS = [IMG.peak, IMG.city, IMG.travel, IMG.victory, IMG.calm, IMG.fjord, IMG.board, IMG.hill];

export const STUDIO_TEMPLATES = [
  { id: "magazine", label: { fr: "Couverture magazine", en: "Magazine cover" },
    accent: "#D6A85F", image: IMG.city,
    fields: { brand: "VISIONNAIRE", title: { fr: "L'entrepreneure de l'année", en: "Entrepreneur of the year" },
              tag: { fr: "Portrait · Réussite", en: "Portrait · Success" } } },
  { id: "milestone", label: { fr: "Jalon financier", en: "Financial milestone" },
    accent: "#5e8a5a", image: IMG.peak,
    fields: { brand: "OBJECTIF ATTEINT", title: { fr: "100 000 € de CA", en: "100,000 € revenue" },
              tag: { fr: "Décembre 2026", en: "December 2026" } } },
  { id: "home", label: { fr: "Maison de rêve", en: "Dream home" },
    accent: "#4a6a9e", image: IMG.travel,
    fields: { brand: "MON FUTUR CHEZ-MOI", title: { fr: "Villa lumineuse au bord de l'eau", en: "Bright villa by the water" },
              tag: { fr: "Vie · Liberté", en: "Life · Freedom" } } },
  { id: "press", label: { fr: "Article de presse", en: "Press article" },
    accent: "#8b6fbf", image: IMG.board,
    fields: { brand: "LA PRESSE EN PARLE", title: { fr: "Une méthode qui inspire des milliers", en: "A method inspiring thousands" },
              tag: { fr: "Interview exclusive", en: "Exclusive interview" } } },
];

export const TEMPLATES = [
  { id: "t1", image: IMG.board, canvaUrl: "https://www.canva.com/templates/?query=vision%20board", category: { fr: "Vision", en: "Vision" },
    badge: { fr: "Populaire", en: "Popular" },
    title: { fr: "Vision Board 2026", en: "Vision Board 2026" },
    desc: { fr: "Un moodboard élégant pour clarifier tes rêves.", en: "An elegant moodboard to clarify your dreams." } },
  { id: "t2", image: IMG.goals, canvaUrl: "https://www.canva.com/templates/?query=90%20day%20action%20plan", category: { fr: "Stratégie", en: "Strategy" },
    title: { fr: "Plan d'action 90 jours", en: "90-day action plan" },
    desc: { fr: "Roadmap trimestrielle prête à remplir.", en: "Quarterly roadmap ready to fill." } },
  { id: "t3", image: IMG.goalsPen, canvaUrl: "https://www.canva.com/templates/?query=smart%20goals%20planner", category: { fr: "Productivité", en: "Productivity" },
    title: { fr: "Objectifs SMART", en: "SMART goals" },
    desc: { fr: "Structure tes objectifs de manière claire.", en: "Structure your goals clearly." } },
  { id: "t4", image: IMG.vibes, canvaUrl: "https://www.canva.com/templates/?query=mood%20board%20colors", category: { fr: "Créatif", en: "Creative" },
    title: { fr: "Mood & couleurs", en: "Mood & colors" },
    desc: { fr: "Palette et ambiance de ta marque.", en: "Your brand palette and mood." } },
  { id: "t5", image: IMG.city, canvaUrl: "https://www.canva.com/templates/?query=business%20model%20canvas", category: { fr: "Stratégie", en: "Strategy" },
    badge: { fr: "Nouveau", en: "New" },
    title: { fr: "Business Model Canvas", en: "Business Model Canvas" },
    desc: { fr: "Vue d'ensemble de ton modèle économique.", en: "Overview of your business model." } },
  { id: "t6", image: IMG.calm, canvaUrl: "https://www.canva.com/templates/?query=morning%20routine%20planner", category: { fr: "Productivité", en: "Productivity" },
    title: { fr: "Rituel matinal", en: "Morning ritual" },
    desc: { fr: "Planifie une routine qui te ressemble.", en: "Plan a routine that fits you." } },
];
