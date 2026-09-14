import { api, getKpis, getObjectifs, getVision, getTresorerieHistory } from "./api";

/**
 * Adaptateur des contrats utilisés par le vrai VisionBoard de Final-main.
 * Il garde les signatures Final-main, tout en les reliant aux routes SQL de
 * Cours-main plutôt qu'au backend JWT de Final-main.
 */
export const visionApi = {
  async get() {
    const [savedVision, objectifs] = await Promise.all([getVision(), getObjectifs()]);
    return {
      value: savedVision?.value || "",
      vision_10y: savedVision?.vision_10y || savedVision?.value || "",
      why: savedVision?.why || "",
      values: savedVision?.values || [],
      keywords: savedVision?.keywords || [],
      domains: savedVision?.domains || objectifs || [],
      objective_90d: savedVision?.objective_90d || "",
      board: savedVision?.board || [],
    };
  },
  patch: (data) => api.patch("/vision", data).then((r) => r.data),
  boardGenerate: (data) => api.post("/vision/board/generate", data).then((r) => r.data),
  boardTransform: (data) => api.post("/vision/board/transform", data).then((r) => r.data),
  boardDelete: (itemId) => api.delete(`/vision/board/${itemId}`).then((r) => r.data),
  canvasGet: () => api.get("/vision/board/canvas").then((r) => r.data),
  canvasSave: (data) => api.put("/vision/board/canvas", data).then((r) => r.data),
  liveMetrics: () => api.get("/vision/board/live-metrics").then((r) => r.data),
  liveData: () => api.get("/vision/board/live-data").then((r) => r.data),
  inspire: (universe) => api.post("/vision/board/inspire", { universe }).then((r) => r.data),
  photos: (q) => api.get("/vision/board/photos", { params: { q } }).then((r) => r.data),
  flipbookRefresh: () => api.post("/vision/board/refresh").then((r) => r.data),
  flipbookGenerate: (data) => api.post("/vision/board/generate-flipbook", data).then((r) => r.data),
  templates: () => api.get("/vision/board/templates").then((r) => r.data),
  generateDoc: (prompt, docType = "note") => api.post("/vision/board/generate-doc", { prompt, doc_type: docType }).then((r) => r.data),
};

export const visionCardsApi = {
  list: (boardId = "main") => api.get("/vision/cards", { params: { board_id: boardId } }).then((r) => r.data),
  create: (card) => api.post("/vision/cards", card).then((r) => r.data),
  update: (id, patch) => api.put(`/vision/cards/${id}`, patch).then((r) => r.data),
  remove: (id) => api.delete(`/vision/cards/${id}`).then((r) => r.data),
  migrateLegacy: (boardId = "main") => api.post("/vision/cards/migrate-legacy", {}, { params: { board_id: boardId } }).then((r) => r.data),
  createSnapshot: (label, boardId = "main") => api.post("/vision/cards/snapshots", {}, { params: { board_id: boardId, label } }).then((r) => r.data),
  listSnapshots: (boardId = "main") => api.get("/vision/cards/snapshots", { params: { board_id: boardId } }).then((r) => r.data),
  restoreSnapshot: (id) => api.post(`/vision/cards/snapshots/${id}/restore`).then((r) => r.data),
  deleteSnapshot: (id) => api.delete(`/vision/cards/snapshots/${id}`).then((r) => r.data),
  getPublicStatus: (boardId = "main") => api.get("/vision/cards/public-status", { params: { board_id: boardId } }).then((r) => r.data),
  setPublicStatus: (enabled, boardId = "main") => api.put("/vision/cards/public-status", { enabled, board_id: boardId }).then((r) => r.data),
};

export const visionBrainApi = {
  scoreHistory: (days = 90) => api.get("/vision/brain/score-history", { params: { days } }).then((r) => r.data),
};

export const dashboardApi = {
  summary: async () => {
    const kpis = await getKpis();
    return { ...kpis, revenue: kpis.chiffre_affaires, cash: kpis.tresorerie };
  },
};

export const tasksApi = {
  list: async () => ({ items: [] }),
};
