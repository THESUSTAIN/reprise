import {
  api, getObjectifs, getKpis, getHumeur, getProfile, createRituel,
  getSwot, generateSwot,
  createTache,
} from "./api";
import { visionCardsApi as persistedVisionCardsApi } from "./finalVisionApi";

const unavailable = (message) => Promise.reject(new Error(message));
const localRead = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key) || "") ?? fallback; } catch { return fallback; } };
const localWrite = (key, value) => { localStorage.setItem(key, JSON.stringify(value)); return value; };

export const visionApi = {
  getBoard: () => api.get("/vision/board").then((r) => r.data),
  saveBoard: (cards) => api.put("/vision/board", { cards }).then((r) => r.data),
  addCard: (card) => api.post("/vision/board/card", card).then((r) => r.data),
  generateDoc: (prompt, docType = "note") => api.post("/vision/board/generate-doc", { prompt, doc_type: docType }).then((r) => r.data),
  inspire: () => api.post("/vision/board/inspire", { universe: "universel" }).then((r) => r.data),
  photos: (q) => api.get("/vision/board/photos", { params: { q } }).then((r) => r.data),
};

export const visionExtApi = {
  canvaImport: () => unavailable("L’import Canva sera disponible avec le connecteur de production."),
  uploadPhoto: () => unavailable("L’envoi d’image sera disponible avec le stockage de production."),
  shareBoard: () => unavailable("Le partage public sera activé avec le compte de production."),
  generateFromPrompt: () => unavailable("La génération IA est indisponible dans cette prévisualisation."),
  generateBook: () => unavailable("La génération de Vision Book est indisponible dans cette prévisualisation."),
  coach: () => unavailable("Le coach IA est indisponible dans cette prévisualisation."),
  getStarterTemplates: async () => ({ templates: [] }),
  getPillars: async () => {
    const objectifs = await getObjectifs();
    const palette = [
      { color: "#DEC2A3", icon: "TrendingUp" }, { color: "#4CBF88", icon: "HeartPulse" },
      { color: "#7DB7FF", icon: "Globe" }, { color: "#D9986A", icon: "Wallet" },
    ];
    return (Array.isArray(objectifs) ? objectifs : []).map((item, index) => {
      const style = palette[index % palette.length];
      const progress = Math.max(0, Math.min(100, Number(item.avancement ?? item.progress ?? 0)));
      const label = item.nom || item.titre || item.title || "Objectif";
      return {
        id: String(item.id ?? `objectif-${index}`),
        title: label,
        description: item.description || item.detail || "Objectif issu de votre cockpit.",
        category: "business",
        color: style.color,
        icon: style.icon,
        progress,
        objectives: [{ text: label, done: progress >= 100 }],
        pinned_dashboard: false,
      };
    });
  },
  savePillars: async (pillars) => localWrite("cours-main-vision-pillars", pillars),
  getMemories: async () => localRead("cours-main-vision-memories", []),
  getNotifSettings: async () => localRead("cours-main-vision-notifications", {}),
  saveNotifSettings: async (value) => localWrite("cours-main-vision-notifications", value),
};

export const pilotageApi = { overview: async () => getKpis() };
export const wellnessApi = {
  state: async () => {
    const rows = await getHumeur();
    return rows?.[0] || {};
  },
};
export const onboardingApi = { get: async () => getProfile() };
export const tasksApi = {
  create: async ({ label, ...meta }) => createTache({
    titre: label,
    ...meta,
    notes: meta.notes || "Créé depuis Vision",
  }),
};
export const analyseApi = {
  get: async () => getSwot(),
  run: async () => generateSwot(),
};
export const studioApi = {
  generateImage: () => unavailable("La génération d’image IA est indisponible dans cette prévisualisation."),
  generateVideo: () => unavailable("La génération vidéo IA est indisponible dans cette prévisualisation."),
};

export const visionCardsApi = persistedVisionCardsApi;

export const visionBrainApi = {
  panel: async () => {
    const [healthResult, objectifsResult] = await Promise.all([
      api.get("/health-score").then((r) => r.data).catch(() => ({ score: 0 })),
      getObjectifs().catch(() => []),
    ]);
    const score = Number(healthResult?.score || 0);
    const objectifs = Array.isArray(objectifsResult) ? objectifsResult : [];
    const hasMeasuredVision = objectifs.length > 0 || score > 0;
    return {
      alignment_score: hasMeasuredVision ? score : null,
      delta_week: null,
      opportunities: [],
      score_business: {
        overall: hasMeasuredVision ? score : null,
        pillars: hasMeasuredVision ? [
          { name: "Vision", value: score },
          { name: "Exécution", value: 0 },
          { name: "Finance", value: 0 },
          { name: "Impact", value: 0 },
          { name: "Énergie", value: 0 },
          { name: "Croissance", value: 0 },
        ] : [],
      },
      linked_cards: objectifs.slice(0, 4).map((item, index) => ({
        key: String(item.id || index), type: "Objectif", title: item.nom || item.titre || "Objectif", value: item.avancement ?? 0, badge: "Objectif",
      })),
    };
  },
  connections: async () => ({ chain: [] }),
  analyze: async () => analyseApi.run(),
};
