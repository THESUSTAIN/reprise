import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API });

const listOf = (payload, key = "items") => Array.isArray(payload) ? payload : (Array.isArray(payload?.[key]) ? payload[key] : []);
const asEnergyPercent = (value) => {
  const n = Number(value);
  if (!Number.isFinite(n)) return null;
  return n <= 5 ? Math.round(n * 20) : Math.round(Math.max(0, Math.min(100, n)));
};
const moodLabel = (mood) => ({ 1: "Épuisé", 2: "Fatigué", 3: "Bien", 4: "Motivé", 5: "En feu" })[Number(mood)] || "—";
const moodValue = (mood) => ({ "Épuisé": 1, "Fatigué": 2, "Bien": 3, "Motivé": 4, "En feu": 5 })[mood] || 3;
const priorityLabel = (priority) => ({ high: "Haute", medium: "Moyenne", normal: "Normale", low: "Basse", Haute: "Haute", Moyenne: "Moyenne", Normale: "Normale" })[priority] || "Normale";
const priorityValue = (priority) => ({ Haute: "high", Moyenne: "medium", Basse: "low", Normale: "normal", high: "high", medium: "medium", low: "low", normal: "normal" })[priority] || "normal";
export const normalizeTask = (task = {}) => ({
  ...task,
  titre: task.titre || task.label || "Tâche sans titre",
  statut: task.done ? "Terminé" : task.in_progress ? "En cours" : "A faire",
  priorite: priorityLabel(task.priorite || task.priority),
});
export const normalizeCheckin = (checkin = {}) => ({
  ...checkin,
  energie: asEnergyPercent(checkin.energie ?? checkin.energy),
  humeur: checkin.humeur || moodLabel(checkin.mood),
  date: checkin.date || checkin.created_at || null,
});
export const normalizeHabit = (habit = {}) => ({
  ...habit,
  nom: habit.nom || habit.name || "Habitude",
  done: habit.done ?? habit.done_today ?? false,
  streak: Number(habit.streak || 0),
});

// Vrais comptes utilisateurs (auth.py) — jeton attaché automatiquement dès
// qu'une session est ouverte. Tant que rien n'est stocké (avant login),
// les appels partent sans en-tête — le backend répond 401 sur les routes
// protégées, comme attendu.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("cours_auth_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// En prévisualisation frontend seule, le serveur statique peut renvoyer index.html
// pour une URL /api. Ne jamais laisser ce HTML contaminer les données React.
api.interceptors.response.use((response) => {
  const contentType = String(response.headers?.["content-type"] || "").toLowerCase();
  if (contentType.includes("text/html")) {
    const error = new Error("Backend API indisponible dans cette prévisualisation.");
    error.code = "STATIC_PREVIEW_API";
    return Promise.reject(error);
  }
  return response;
});

// Contrat Final-main réel : l'inscription utilise /api/auth/register.
export const authSignup = (email, password, first_name) =>
  api.post("/auth/register", { email, password, first_name }).then((r) => r.data);
export const authLogin = (email, password) =>
  api.post("/auth/login", { email, password }).then((r) => r.data);
export const authMe = () => api.get("/auth/me").then((r) => r.data);
// URLs de la fenêtre TheSustain — éditables par un admin (PUT /admin/config
// avec {thesustain_urls: {...}}), lues ici en public.
export const getPublicConfig = () => api.get("/config/public").then((r) => r.data);
// Le routeur alias Final-main est monté sous /api/onboarding. Le chemin
// /auth/onboarding n’existe pas et empêchait l’onboarding frontend de persister.
export const authOnboarding = (d) => api.post("/onboarding", d).then((r) => r.data);

// Ajoutés — routes réelles côté backend (auth.py), jamais reliées côté
// frontend jusqu'ici : lien magique, compte de démo, OAuth Google/Microsoft.
export const sendMagicLink = (email) => api.post("/auth/request-link", { email }).then((r) => r.data);
export const verifyMagicLink = (token) => api.post("/auth/verify-link", { token }).then((r) => r.data);
export const demoLogin = (email) => api.post("/auth/demo-login", { email }).then((r) => r.data);
// Renvoie l'URL d'autorisation Google/Microsoft, ou lève une erreur claire
// (503 "GOOGLE_CLIENT_ID non configuré") si les clés OAuth ne sont pas encore
// définies dans Railway — jamais un faux succès silencieux.
export const oauthStart = (provider, redirectUri) =>
  api.get(`/oauth/${provider}/start`, { params: { redirect_uri: redirectUri } }).then((r) => r.data);

// Échange le "code" renvoyé par Google/Microsoft (après redirection sur
// /login?code=...&state=...) contre une session réelle. Sans cet appel, le
// code atterrit sur /login sans jamais être consommé — la connexion semble
// "ne rien faire" alors que Google a bien renvoyé un code valide.
export const oauthExchange = (provider, code, redirectUri) =>
  api.post(`/oauth/${provider}`, { code, redirect_uri: redirectUri }).then((r) => r.data);


export const getPilotageOverview = () => api.get("/pilotage/overview").then((r) => r.data);
export const getKpis = () => getPilotageOverview().then((data) => ({
  tresorerie: Number(data?.summary?.tresorerie || 0),
  chiffre_affaires: Number(data?.summary?.revenus || 0),
  marge_nette: Number(data?.summary?.marge || 0),
  resultat_net: Number((data?.kpis || []).find((item) => item.id === "net")?.value || 0),
  en_retard: Number(data?.pending_invoices || 0),
  total_depenses: Number((data?.kpis || []).find((item) => item.id === "depenses")?.value || 0),
}));
export const getTresorerieHistory = () => getPilotageOverview().then((data) => Array.isArray(data?.monthly) ? data.monthly.map((row) => ({ date: row.month || "—", tresorerie: Number(row.ca || 0) })) : []);
export const getDecision = () => api.get("/pilotage/decision").then((r) => r.data);
export const simulatePilotage = (payload) => api.post("/pilotage/simulate", payload).then((r) => r.data);
export const getHealthScore = () => api.get("/pilotage/health-score").then((r) => r.data);
export const exportCsvUrl = () => `${API}/pilotage/export.csv`;
export const getFactures = () => api.get("/factures").then((r) => r.data);
export const createFacture = (d) => api.post("/factures", d).then((r) => r.data);
export const updateFacture = (id, d) => api.put(`/factures/${id}`, d).then((r) => r.data);
export const deleteFacture = (id) => api.delete(`/factures/${id}`).then((r) => r.data);

export const getDepenses = () => api.get("/depenses").then((r) => r.data);
export const createDepense = (d) => api.post("/depenses", d).then((r) => r.data);
export const deleteDepense = (id) => api.delete(`/depenses/${id}`).then((r) => r.data);

export const getObjectifs = () => api.get("/objectifs").then((r) => r.data);
export const createObjectif = (d) => api.post("/objectifs", d).then((r) => r.data);
export const updateObjectif = (id, d) => api.put(`/objectifs/${id}`, d).then((r) => r.data);
export const deleteObjectif = (id) => api.delete(`/objectifs/${id}`).then((r) => r.data);
export const objectifToAction = (id) => api.post(`/objectifs/${id}/to-action`).then((r) => r.data);

export const getSwot = () => api.get("/vision/swot").then((r) => r.data);
export const generateSwot = () => api.post("/vision/swot/generate").then((r) => r.data);
export const getVisionDocument = () => api.get("/vision/document").then((r) => r.data);
export const generateVisionDocument = () => api.post("/vision/document/generate").then((r) => r.data);

export const getVision = () => api.get("/vision").then((r) => r.data);
export const setVision = (value) => api.put("/vision", { key: "vision", value }).then((r) => r.data);

export const getRituels = () => api.get("/wellness/habits").then((r) => listOf(r.data).map(normalizeHabit));
export const createRituel = (d) => api.post("/wellness/habits", { name: d.nom || d.name || "Habitude" }).then((r) => normalizeHabit(r.data));
export const toggleRituel = (id) => api.post(`/wellness/habits/${id}/toggle`).then((r) => normalizeHabit(r.data));
export const deleteRituel = (id) => api.delete(`/wellness/habits/${id}`).then((r) => r.data);

// Contrat Final-main réel : Bien-être est exposé sous /api/wellness.
export const getWellnessState = () => api.get("/wellness/state").then((r) => r.data);
export const getWellnessToday = () => api.get("/wellness/today").then((r) => r.data);
export const getWellnessHistory = (days = 30) => api.get(`/wellness/history?days=${encodeURIComponent(days)}`).then((r) => r.data);
export const getWellnessWeeklyReport = () => api.get("/wellness/weekly-report").then((r) => r.data);
export const createWellnessCheckin = (d) => api.post("/wellness/checkin", d).then((r) => r.data);
// Les pages historiques manipulent énergie 0-100 et libellés ; le serveur
// Wellness utilise une échelle clinique 1-5. Cette conversion est volontaire
// et ne fabrique aucune mesure supplémentaire.
export const getHumeur = () => getWellnessHistory().then((data) => listOf(data, "checkins").map(normalizeCheckin));
export const createHumeur = ({ energie, humeur, note }) => createWellnessCheckin({
  energy: Math.max(1, Math.min(5, Math.round(Number(energie || 60) / 20))),
  mood: moodValue(humeur),
  stress: Number(energie) <= 35 ? 4 : Number(energie) <= 65 ? 3 : 2,
  notes: note || null,
});

// Corrigé : ces fonctions appelaient toutes /settings/* — une famille de
// routes qui n'existe nulle part côté serveur (vérifié systématiquement).
// Rebranché sur /api/prefs, le vrai magasin générique clé-valeur déjà
// fonctionnel (routes/prefs.py), chaque réglage sous sa propre clé, fusionné
// automatiquement par le backend à chaque PUT.
export const getProfile = () => api.get("/prefs").then((r) => r.data?.profile || {});
export const setProfile = (first_name) => api.put("/prefs", { profile: { first_name } }).then((r) => r.data?.profile || {});
// MyExtension Campus s'appuie sur le moteur de simulation professionnel
// Final-main déjà disponible. Ces appels restent protégés par la session :
// aucune entreprise, mission ou évaluation n'est fabriquée côté interface.
export const getCampusSimulationState = () => api.get("/simulation/state").then((r) => r.data);
export const startCampusSimulation = ({ programme_label, diploma_level }) =>
  api.post("/simulation/start", { programme_label, diploma_level }).then((r) => r.data);
export const getCampusSimulationHistory = () => api.get("/simulation/history").then((r) => r.data);
export const submitCampusMission = (taskId, response_text) =>
  api.post(`/simulation/tasks/${taskId}/submit`, { response_text }).then((r) => r.data);
export const getReminders = () => api.get("/prefs").then((r) => r.data?.reminders || {});
export const setReminders = (weekly_review) => api.put("/prefs", { reminders: { weekly_review } }).then((r) => r.data?.reminders || {});
export const getInspiration = () => api.get("/prefs").then((r) => r.data?.inspiration || {});
export const setInspirationImage = (image_url) => api.put("/prefs", { inspiration: { image_url } }).then((r) => r.data?.inspiration || {});
// Les préférences Actualité sont persistées par les réglages Growth Final-main.
export const getNewsPreferences = () => api.get("/growth/settings").then((r) => r.data);
export const setNewsPreferences = ({ sector, region, frequency_per_week = 1 }) => api.put("/growth/settings", { sector, region, frequency_per_week }).then((r) => r.data);

export const seed = () => api.post("/seed").then((r) => r.data);

// --- Panneau de chat complet (copilote) : upload persistant, historique,
// brief du jour, veille, "travailler avec l'équipe". ---
export const getChatHistory = (session = "default") =>
  api.get(`/chat/messages?session_id=${encodeURIComponent(session)}`).then((r) => r.data);

export async function uploadChatFile(file) {
  // Corrige un bug réel : appelait /chat/uploads (pluriel, avec session_id en
  // query param) — route qui n'existe pas côté serveur. Le vrai endpoint est
  // /chat/upload (singulier), authentifié par JWT (déjà géré par l'intercepteur
  // ci-dessus), sans session_id.
  const form = new FormData();
  form.append("file", file);
  const response = await api.post(`/chat/upload`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

// Google Drive — reconstruit après un bug de build réel : ChatPanel.jsx
// importait ces 4 fonctions, qui n'existaient nulle part dans ce fichier
// (échec de compilation en production : "getDriveStatus is not exported").
// Les vraies routes serveur existent bien (routes/gdrive.py, drive_router
// monté sur /api/drive) — seules les fonctions frontend manquaient.
export const getDriveStatus = () => api.get("/drive/status").then((r) => r.data);
export const connectDrive = () => api.get("/drive/connect").then((r) => r.data); // { authorization_url }
export const listDriveFiles = (folderId = "root") =>
  api.get("/drive/files", { params: { folder_id: folderId } }).then((r) => r.data);
// Télécharge un fichier depuis Drive (réponse binaire), puis le renvoie comme
// pièce jointe de chat via le vrai endpoint /chat/upload — pas de route
// serveur dédiée "importer depuis Drive", on enchaîne les deux appels réels.
export async function importDriveFileToChat(fileId, fileName) {
  const fileResponse = await api.get(`/drive/download/${fileId}`, { responseType: "blob" });
  const blob = fileResponse.data;
  const file = new File([blob], fileName || "fichier", { type: blob.type || "application/octet-stream" });
  return uploadChatFile(file);
}

// Génération d'image — vrai endpoint déjà présent côté serveur (coûte des
// crédits utilisateur, 8 par image ; nouveaux comptes démarrent avec 180).
export async function generateChatImage(prompt, style = "verset_illustre") {
  const response = await api.post(`/chat/image`, { prompt, style });
  return response.data;
}

export async function streamChatMessage({ message, session = "default", context, uploadIds = [], onToken, onDone }) {
  const res = await fetch(`${API}/chat/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: session, context, upload_ids: uploadIds }),
  });
  if (!res.ok) {
    let detail = `Chat error ${res.status}`;
    try { detail = (await res.json())?.detail || detail; } catch { /* réponse non JSON */ }
    throw new Error(detail);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let full = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    full += decoder.decode(value, { stream: true });
    onToken && onToken(full);
  }
  onDone && onDone(full);
  return full;
}

// Le Copilote appelait /chat/messages (streaming) — route qui n'existe nulle
// part côté serveur (vérifié : aucun routeur ne sert /chat/messages, /chat/brief,
// /chat/config, /chat/decision, /chat/news-history ni /chat/news-saved dans ce
// projet). Le VRAI backend fonctionnel du Co-pilote existe, mais sous
// /api/growth/copilote — synchrone (pas de streaming), avec l'historique
// transmis par le client à chaque appel plutôt que persisté côté serveur.
// sendCopilotMessage() est le pont réel utilisé maintenant par ChatPanel ;
// streamChatMessage ci-dessus est conservé tel quel (inchangé, toujours mort)
// pour ne pas casser un éventuel futur vrai backend streaming qui reprendrait
// exactement ce contrat.
export async function sendCopilotMessage({ message, session = "default", history = [] }) {
  const res = await api.post(`/growth/copilote?user_id=${encodeURIComponent(session)}`, {
    message,
    history: history.slice(-8).map((m) => ({ role: m.role, content: m.content })),
  });
  return { reply: res.data?.reply || "", sources: Array.isArray(res.data?.sources) ? res.data.sources : [] };
}

// /chat/brief et /chat/news-digest n'ont pas non plus de route serveur
// (même famille de bug que /chat/messages, voir sendCopilotMessage
// ci-dessus). Les vrais endpoints existent sous /api/growth — mêmes
// champs de base (date, headline, news...) mais PAS les champs détaillés
// que NightRecap/NextSequence espèrent (ia_checklist, value_generated,
// activite_recente) : ces deux composants resteront donc en état vide
// honnête (ils gèrent déjà ce cas, pas de crash) tant que le backend ne
// calcule pas ces champs-là spécifiquement.
export const getCopilotBrief = (session = "default") =>
  api.get(`/growth/daily-brief?user_id=${encodeURIComponent(session)}`).then((r) => r.data);

export const getCopilotConfig = async () => ({});

export const getCopilotDecision = (session = "default") =>
  api.get(`/chat/decision?session_id=${encodeURIComponent(session)}`).then((r) => r.data);

export const applyCopilotDecision = ({ id, session = "default", decision }) =>
  api.post(`/chat/decision/${id}`, { session_id: session, decision }).then((r) => r.data);

export const getCopilotNews = (session = "default", refresh = false) =>
  api.get(`/growth/news-digest?user_id=${encodeURIComponent(session)}${refresh ? "&refresh=true" : ""}`).then((r) => r.data);

export const getNewsHistory = (session = "default") =>
  api.get(`/chat/news-history?session_id=${encodeURIComponent(session)}`).then((r) => r.data);

// Recherche globale (Cmd+K) — cherche dans les vraies données (projets,
// tâches, prospects), pas seulement les pages du menu.
export const globalSearch = (q) => api.get("/search", { params: { q } }).then((r) => r.data?.results || []);

// Badge de notification "nouvelle actualité" (Layout.jsx) — compare la
// dernière édition disponible à la dernière vue par l'utilisateur.
export const getLastSeenNewsId = () => api.get("/prefs").then((r) => r.data?.last_seen_news_id || null);
export const setLastSeenNewsId = (newsId) => api.put("/prefs", { last_seen_news_id: newsId }).then((r) => r.data?.last_seen_news_id || null);

export const archiveNewsEdition = (session = "default", item) =>
  api.post("/chat/news-history", { session_id: session, ...item }).then((r) => r.data);

export const getSavedNews = (session = "default") =>
  api.get(`/chat/news-saved?session_id=${encodeURIComponent(session)}`).then((r) => r.data);

export const saveNewsItem = (session = "default", item) =>
  api.post("/chat/news-saved", { session_id: session, ...item }).then((r) => r.data);

export const deleteSavedNews = (session = "default", itemId) =>
  api.delete(`/chat/news-saved/${encodeURIComponent(itemId)}?session_id=${encodeURIComponent(session)}`).then((r) => r.data);

// Demande Collaborateur : le backend déduit le propriétaire depuis le JWT,
// sans accepter d'identifiant de compte arbitraire dans l'URL.
export const sendCopilotWorkRequest = ({ message, channel = "chat", contact = "" }) =>
  api.post("/growth/work-request", { message, channel, contact }).then((r) => r.data);

export const euro = (n) =>
  new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n || 0);

export const getVisionMemory = () => api.get("/prefs").then((r) => r.data?.vision_memory || {});
export const setVisionMemory = (memory) => api.put("/prefs", { vision_memory: { memory } }).then((r) => r.data?.vision_memory || {});
export const getPlan = () => api.get("/prefs").then((r) => r.data?.plan || {});
export const setPlan = (plan) => api.put("/prefs", { plan: { plan } }).then((r) => r.data?.plan || {});
// Stockage de la config Odoo réel (via /api/prefs) — mais aucune vraie
// intégration de synchronisation n'existe côté serveur (POST /odoo/sync
// n'a pas de route). Le bouton "Synchroniser" échouera donc proprement
// tant qu'une vraie intégration Odoo n'est pas construite — pas de faux
// succès simulé.
export const getOdooConfig = () => api.get("/prefs").then((r) => r.data?.odoo || {});
export const setOdooConfig = (d) => api.put("/prefs", { odoo: d }).then((r) => r.data?.odoo || {});
export const syncOdoo = () => api.post("/odoo/sync").then((r) => r.data);

export const getWellnessCorrelations = () => api.get("/wellness/correlations").then((r) => r.data);
export const getYearPixels = () => getWellnessHistory(366).then((data) => ({
  days: listOf(data, "checkins").map((row) => ({
    date: row.date ? String(row.date).slice(0, 10) : null,
    energie: asEnergyPercent(row.energy),
  })).filter((row) => row.date),
}));

// Aucun flux Messages distinct n’est encore fourni par Final-main. Le Header
// n’affiche donc aucun faux message et ne déclenche pas de requête 404.
export const getHeaderMessages = async () => ({ items: [] });
export const markHeaderMessagesRead = async () => ({ items: [] });
// Le Header Final-main lit les notifications via les routes profil réelles.
export const getHeaderNotifications = () => api.get("/notifications").then((r) => r.data);
export const markHeaderNotificationsRead = () => api.post("/notifications/read").then((r) => r.data);
export const getLanguage = async () => ({ language: localStorage.getItem("mx_language") || "fr" });
export const setLanguage = async (language) => { localStorage.setItem("mx_language", language); return { language }; };
export const logoutSession = async () => { localStorage.removeItem("cours_auth_token"); return { ok: true }; };

const CAP_STAGE_TO_GROWTH = { "Nouveaux": "detected", "Contactés": "contacted", "Propositions": "discussing", "Négociation": "discussing", "Gagnés": "signed", "Perdus": "lost" };
const GROWTH_STAGE_TO_CAP = { detected: "Nouveaux", contacted: "Contactés", discussing: "Négociation", signed: "Gagnés", lost: "Perdus" };
export const getGrowthPipeline = () => api.get("/growth/pipeline").then((r) => r.data);
export const getProspects = () => getGrowthPipeline().then((data) => listOf(data, "stages").flatMap((stage) => listOf(stage, "leads").map((lead) => ({
  ...lead,
  nom: lead.nom || lead.name || "Prospect",
  entreprise: lead.entreprise || lead.company || lead.sub || "",
  valeur_estimee: Number(lead.valeur_estimee || lead.value || 0),
  etape: GROWTH_STAGE_TO_CAP[stage.id] || "Nouveaux",
}))));
export const createProspect = (d) => api.post("/growth/leads", { name: d.nom || d.name, company: d.entreprise || d.company || null, email: d.email || null, snippet: d.notes || d.snippet || "", source: "manual", stage: "detected" }).then((r) => r.data);
export const moveProspect = (id, etape) => api.patch(`/growth/pipeline/${id}`, { stage: CAP_STAGE_TO_GROWTH[etape] || "detected" }).then((r) => r.data);
export const qualifyProspect = (id, notes) => api.post(`/growth/leads/${id}/qualify`, { notes }).then((r) => r.data);
export const getValidationQueue = () => api.get("/collaborateur/queue?limit=20").then((r) => r.data);
export const createValidationDraft = (draft) => api.post("/collaborateur/queue", draft).then((r) => r.data);
export const validateDraft = (id) => api.post(`/collaborateur/queue/${id}/validate`).then((r) => r.data);
export const dismissDraft = (id) => api.post(`/collaborateur/queue/${id}/dismiss`).then((r) => r.data);
export const deleteProspect = async () => { throw new Error("La suppression d’un prospect n’est pas encore disponible côté serveur."); };
export const getPipelineStats = () => getProspects().then((items) => {
  const signed = items.filter((item) => item.etape === "Gagnés");
  const active = items.filter((item) => !["Gagnés", "Perdus"].includes(item.etape));
  return {
    valeur_pipeline: active.length ? active.reduce((sum, item) => sum + Number(item.valeur_estimee || 0), 0) : null,
    taux_conversion: items.length && signed.length ? Math.round((signed.length / items.length) * 100) : null,
    panier_moyen: signed.length ? signed.reduce((sum, item) => sum + Number(item.valeur_estimee || 0), 0) / signed.length : null,
  };
});

// Projets et minuteur : contrats Final-main réels sous /api/projects.
export const getProjets = () => api.get("/projects").then((r) => r.data);
export const createProjet = (d) => api.post("/projects", d).then((r) => r.data);
export const updateProjet = (id, d) => api.put(`/projects/${id}`, d).then((r) => r.data);
export const deleteProjet = (id) => api.delete(`/projects/${id}`).then((r) => r.data);
export const startProjectTimer = (id) => api.post(`/projects/${id}/start`).then((r) => r.data);
export const stopProjectTimer = (id) => api.post(`/projects/${id}/stop`).then((r) => r.data);
// Tâches Final-main réelles sous /api/tasks.
export const getTaches = () => api.get("/tasks").then((r) => listOf(r.data).map(normalizeTask));
export const createTache = (d) => api.post("/tasks", {
  label: d.titre || d.label || "Tâche",
  priority: priorityValue(d.priorite || d.priority),
  notes: d.notes || null,
  project_id: d.project_id || null,
  planned_for: d.planned_for || null,
  estimated_minutes: d.estimated_minutes ? Number(d.estimated_minutes) : null,
  decision_id: d.decision_id || null,
  vision_pillar_id: d.vision_pillar_id || null,
  strategic_milestone_id: d.strategic_milestone_id || null,
  defer_reason: d.defer_reason || null,
}).then((r) => normalizeTask(r.data));
export const updateTache = (id, d) => api.patch(`/tasks/${id}`, d).then((r) => r.data);
export const updateTacheStatut = (id, statut) => api.patch(`/tasks/${id}`, { done: statut === "Terminé", in_progress: statut === "En cours" }).then((r) => normalizeTask(r.data));
export const deleteTache = (id) => api.delete(`/tasks/${id}`).then((r) => r.data);
export const generateTaches = () => api.post("/tasks/generate").then((r) => r.data);

// Vision — jalons et décisions stratégiques. Les objets restent vides tant que
// l'utilisateur ne les crée pas ; aucun jalon ni décision n'est généré localement.
export const getStrategicMilestones = () => api.get("/strategy/milestones").then((r) => listOf(r.data));
export const createStrategicMilestone = (d) => api.post("/strategy/milestones", d).then((r) => r.data);
export const updateStrategicMilestone = (id, d) => api.patch(`/strategy/milestones/${id}`, d).then((r) => r.data);
export const deleteStrategicMilestone = (id) => api.delete(`/strategy/milestones/${id}`).then((r) => r.data);
export const getStrategicDecisions = () => api.get("/strategy/decisions").then((r) => listOf(r.data));
export const createStrategicDecision = (d) => api.post("/strategy/decisions", d).then((r) => r.data);
export const updateStrategicDecision = (id, d) => api.patch(`/strategy/decisions/${id}`, d).then((r) => r.data);
export const applyStrategicDecision = (id) => api.post(`/strategy/decisions/${id}/apply`).then((r) => r.data);
export const getStrategyOverview = () => api.get("/strategy/overview").then((r) => r.data);

// Vue agrégée de Mon Mouvement et recommandations Final-main.
export const getTravailOverview = () => api.get("/travail/overview").then((r) => r.data);
export const getTravailRecommendations = () => api.get("/travail/recommendations").then((r) => r.data);
export const getTravailEvents = (day = "") => api.get(`/travail/events${day ? `?day=${encodeURIComponent(day)}` : ""}`).then((r) => r.data);
export const createTravailEvent = (d) => api.post("/travail/events", d).then((r) => r.data);
export const updateTravailEvent = (id, d) => api.patch(`/travail/events/${id}`, d).then((r) => r.data);
export const deleteTravailEvent = (id) => api.delete(`/travail/events/${id}`).then((r) => r.data);

// Final-main n’expose pas encore de route CRUD pour la liste Documents de Mon
// Documents : routes Final-main réelles sous /api/documents. Aucun document n’est
// injecté localement ; la liste reste vide tant que l’utilisateur n’en crée pas.
export const getDocumentsTravail = () => api.get("/documents").then((r) => listOf(r.data).map((document) => ({
  ...document,
  nom: document.nom || document.name || "Document sans titre",
  url: document.url || null,
})));
export const createDocumentTravail = ({ nom, url = "", content = "" }) => api.post("/documents", {
  name: nom,
  type: url ? "link" : "general",
  url: url || null,
  content: content || "",
  source: "humain",
}).then((r) => r.data);
export const deleteDocumentTravail = (id) => api.delete(`/documents/${id}`).then((r) => r.data);

// Même chose que pour Odoo ci-dessus : stockage réel via /api/prefs, mais
// pas de vraie synchronisation bancaire côté serveur pour l'instant.
export const getBankAggregatorConfig = () => api.get("/prefs").then((r) => r.data?.bank_aggregator || {});
export const setBankAggregatorConfig = (d) => api.put("/prefs", { bank_aggregator: d }).then((r) => r.data?.bank_aggregator || {});
export const syncBankAggregator = () => api.post("/bank-aggregator/sync").then((r) => r.data);

// Lot 9 — intégrations réelles : cycle de vie connecté, testé et révocable.
export const getConnectionProviders = () => api.get("/connections/providers").then((r) => Array.isArray(r.data) ? r.data : []);
export const getConnections = () => api.get("/connections").then((r) => Array.isArray(r.data) ? r.data : []);
export const testConnection = (id) => api.post(`/connections/${id}/test`).then((r) => r.data);
export const revokeConnection = (id) => api.delete(`/connections/${id}`).then((r) => r.data);
export const createConnection = (provider, credentials, label) => api.post("/connections", { provider, credentials, label }).then((r) => r.data);


// Lot 10 — historique persistant des simulations, toujours scopé au compte JWT.
export const getSimulationHistory = () => api.get("/pilotage/simulations").then((r) => listOf(r.data));
export const saveSimulationHistory = (payload) => api.post("/pilotage/simulations", payload).then((r) => r.data);

// Lots 11–12 — second cerveau et capacités IA contrôlées.
export const getMemoryList = () => api.get("/memory/list").then((r) => listOf(r.data));
export const storeMemory = (content, category = "general") => api.post("/memory/store", { content, category, source: "manual" }).then((r) => r.data);
export const deleteMemory = (id) => api.delete(`/memory/${id}`).then((r) => r.data);
export const getAiPermissions = () => api.get("/prefs").then((r) => r.data?.ai_permissions || {});
export const saveAiPermissions = (permissions) => api.put("/prefs", { ai_permissions: permissions }).then((r) => r.data?.ai_permissions || {});
