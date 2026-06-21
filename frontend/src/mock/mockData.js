// Mock data for Zayado Settings clone

export const userProfile = {
  initials: 'JD',
  fullName: 'Jean Dupont',
  email: 'jean.dupont@zayado.net',
  phone: '+33 6 12 34 56 78',
  company: 'Zayado SAS',
  memberSince: 'Jan 2024',
  plan: 'Professional',
  storageUsed: '2.4 GB / 10 GB',
  storagePercent: 24,
};

export const navItems = [
  { id: 'dashboard',   label: 'Dashboard',          icon: 'LayoutDashboard',   path: '/' },
  { id: 'vision',      label: 'Vision Board',       icon: 'Eye',               path: '/vision-board' },
  { id: 'pilotage',    label: 'Pilotage',           icon: 'LineChart',         path: '/pilotage' },
  { id: 'bienetre',    label: 'Bien-être',          icon: 'HeartPulse',        path: '/bien-etre' },
  { id: 'espace',      label: 'Espace de travail',  icon: 'Briefcase',         path: '/espace' },
  { id: 'croissance',  label: 'Croissance',         icon: 'TrendingUp',        path: '/croissance' },
  { id: 'wordpress',   label: 'WordPress',          icon: 'Globe',             path: '/wordpress',  adminOnly: true },
  { id: 'admin',       label: 'Admin',              icon: 'ShieldCheck',       path: '/admin',      adminOnly: true },
  { id: 'parametres',  label: 'Paramètres',         icon: 'SlidersHorizontal', path: '/parametres' },
];

// Quick jump grid (9-dots button in header) — modules transversaux Zayado
export const quickJumpModules = [
  { id: 'accueil',     label: 'Accueil',                icon: 'Home',     url: 'https://zayado.net',                external: true },
  { id: 'thesustain',  label: 'TheSustain',             icon: 'Leaf',     url: 'https://thesustain.net',            external: true },
  { id: 'boutique',    label: 'Boutique mutualisation', icon: 'Store',    url: 'https://zayado.net/nos-services',   external: true },
];

// Dashboard mock data (Zayado / MyExtension AI flavour)
export const dashboardKpis = [
  {
    id: 'ca',
    label: 'CA du mois',
    value: '12 480 €',
    sub: '+ 1 240 € aujourd\u2019hui',
    delta: '+18,2%',
    deltaPositive: true,
    deltaNote: 'vs mois dernier',
    icon: 'TrendingUp',
    tone: 'navy',
  },
  {
    id: 'salaire',
    label: 'Salaire possible',
    value: '4 320 €',
    sub: 'apr\u00e8s charges & cotisations',
    delta: '+23,1%',
    deltaPositive: true,
    deltaNote: 'vs mois dernier',
    icon: 'Wallet',
    tone: 'gold',
  },
  {
    id: 'leads',
    label: 'Leads actifs',
    value: '47',
    sub: '8 d\u00e9tect\u00e9s aujourd\u2019hui',
    delta: '-3,2%',
    deltaPositive: false,
    deltaNote: 'vs mois dernier',
    icon: 'Users',
    tone: 'navy',
  },
  {
    id: 'energie',
    label: 'Score \u00e9nergie',
    value: '4 / 5',
    sub: 'check-in fait \u00e0 8h12',
    delta: '+2,1%',
    deltaPositive: true,
    deltaNote: 'vs semaine pass\u00e9e',
    icon: 'HeartPulse',
    tone: 'green',
  },
];

export const dashboardActivity = [
  { id: 1, title: 'Nouveau lead d\u00e9tect\u00e9', desc: 'Marie Lambert \u2014 score 8/10', time: 'Il y a 2 min', icon: 'UserPlus', tone: 'navy' },
  { id: 2, title: 'Facture pay\u00e9e', desc: 'Client #A-114 \u2014 1 290 \u20ac', time: 'Il y a 12 min', icon: 'CreditCard', tone: 'green' },
  { id: 3, title: 'Brouillon IA pr\u00eat', desc: 'Article \u00ab\u00a0Solopreneur & charge mentale\u00a0\u00bb', time: 'Il y a 38 min', icon: 'FileEdit', tone: 'gold' },
  { id: 4, title: 'Mission du jour g\u00e9n\u00e9r\u00e9e', desc: 'Relancer 3 prospects en attente', time: 'Il y a 1 h', icon: 'Target', tone: 'navy' },
  { id: 5, title: 'Tr\u00e9sorerie en alerte douce', desc: 'Solde projet\u00e9 J+30 \u2014 vigilance', time: 'Il y a 2 h', icon: 'AlertTriangle', tone: 'danger' },
];

export const dashboardAgents = [
  { id: 'copilote', name: 'Co-pilote IA', status: 'Actif', requests: '1 240 actions', avg: 'mémoire longue', icon: 'Sparkles' },
  { id: 'expansion', name: 'Expansion Agent', status: 'Actif', requests: '47 leads', avg: 'TERRAIN + NET', icon: 'Radar' },
  { id: 'pilotage', name: 'Pilotage financier', status: 'Actif', requests: '12 KPI synchros', avg: 'Bridge API', icon: 'LineChart' },
  { id: 'wellbeing', name: 'Bien-être', status: 'En veille', requests: 'check-in du matin', avg: 'streak 6j', icon: 'HeartHandshake' },
];

export const dashboardQuickActions = [
  { id: 'vision', label: 'Vision Board', icon: 'Eye' },
  { id: 'expansion', label: 'Expansion Agent', icon: 'Radar' },
  { id: 'pilotage', label: 'Pilotage', icon: 'LineChart' },
  { id: 'atelier', label: 'Atelier IA', icon: 'Wand2' },
];

export const languages = [
  { code: 'fr', label: 'Français' },
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Español' },
  { code: 'de', label: 'Deutsch' },
  { code: 'zh', label: '中文' },
  { code: 'ja', label: '日本語' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'ar', label: 'العربية' },
];

export const timezones = [
  { code: 'utc', label: 'UTC (GMT+0)' },
  { code: 'et', label: 'Eastern Time (GMT-5)' },
  { code: 'pt', label: 'Pacific Time (GMT-8)' },
  { code: 'cet', label: 'Central European (GMT+1)' },
  { code: 'ist', label: 'India (GMT+5:30)' },
  { code: 'jst', label: 'Japan (GMT+9)' },
  { code: 'aest', label: 'Australia Eastern (GMT+10)' },
];

export const notificationPrefs = [
  { id: 'email', title: 'Email Notifications', desc: 'Receive notifications via email', icon: 'Mail', enabled: true },
  { id: 'push', title: 'Push Notifications', desc: 'Get push notifications on your device', icon: 'Smartphone', enabled: true },
  { id: 'product', title: 'Product Updates', desc: 'News about new features and updates', icon: 'Zap', enabled: false },
  { id: 'security', title: 'Security Alerts', desc: 'Important security notifications', icon: 'ShieldAlert', enabled: true },
];

export const securityToggles = [
  { id: '2fa', title: 'Two-Factor Authentication', desc: 'Add an extra layer of security', icon: 'KeyRound', enabled: false },
  { id: 'data', title: 'Data Sharing', desc: 'Share anonymous usage data', icon: 'Database', enabled: false },
];

export const headerNotifications = [
  { id: 1, title: 'Nouveau client', desc: 'Marie Lambert a rejoint votre espace', time: 'Il y a 5 min', unread: true, icon: 'UserPlus' },
  { id: 2, title: 'Paiement reçu', desc: 'Facture #2025-114 — 1 290 €', time: 'Il y a 1 h', unread: true, icon: 'CreditCard' },
  { id: 3, title: 'Mise à jour MyExtension AI', desc: 'Version 2.4 disponible', time: 'Il y a 3 h', unread: true, icon: 'Sparkles' },
  { id: 4, title: 'Rappel', desc: 'Réunion à 15h avec l\'équipe', time: 'Hier', unread: false, icon: 'Bell' },
];

export const headerMessages = [
  { id: 1, name: 'Sophie Martin', message: 'Bonjour, peux-tu valider le devis ?', time: '2 min', unread: true, initials: 'SM' },
  { id: 2, name: 'Thomas Bernard', message: 'Le rapport est prêt à être consulté.', time: '15 min', unread: true, initials: 'TB' },
  { id: 3, name: 'Équipe Zayado', message: 'Nouveau document partagé', time: '1 h', unread: false, initials: 'EZ' },
  { id: 4, name: 'Camille Roux', message: 'Merci pour votre retour !', time: '3 h', unread: false, initials: 'CR' },
];
