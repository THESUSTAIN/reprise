import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API_PREFIX = '/api';

export const apiClient = axios.create({
  baseURL: `${BACKEND_URL}${API_PREFIX}`,
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('zayado_token');
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('zayado_token');
    }
    return Promise.reject(err);
  },
);

// Helpers
const get = (url, params) => apiClient.get(url, { params }).then((r) => r.data);
const post = (url, data) => apiClient.post(url, data).then((r) => r.data);
const put = (url, data) => apiClient.put(url, data).then((r) => r.data);
const del = (url) => apiClient.delete(url).then((r) => r.data);

// AUTH (final-main backend)
export const authApi = {
  login: (email, password) => post('/auth/login', { email, password }),
  register: (data) => post('/auth/register', data),
  me: () => get('/auth/me'),
  logout: () => post('/auth/logout'),
};

// HEALTH
export const healthApi = {
  ping: () => get('/health'),
};

// VISION BOARD (final-main routes)
export const visionApi = {
  templates: () => get('/vision/board/templates'),
  generateFlipbook: (data) => post('/vision/board/generate-flipbook', data),
  getFlipbook: () => get('/vision/board/flipbook'),
  deleteFlipbook: () => del('/vision/board/flipbook'),
  previewHtml: (template) => get('/vision/board/preview-html', { template }),
  generate: (data) => post('/vision/board/generate', data),
};

// DASHBOARD
export const dashboardApi = {
  summary: () => get('/dashboard/summary'),
};

// OAUTH connections (correct routes)
export const integrationsApi = {
  google: {
    status: () => get('/drive/status'),
    start: () => get('/oauth/google/start'),
    disconnect: () => post('/drive/disconnect'),
    files: () => get('/drive/files'),
  },
  microsoft: {
    status: () => get('/onedrive/connect'), // status endpoint
    start: () => get('/oauth/microsoft/start'),
    disconnect: () => post('/onedrive/disconnect'),
    files: () => get('/onedrive/files'),
  },
};

// PAYMENTS
export const paymentsApi = {
  plans: () => get('/payments/plans'),
  billing: () => get('/payments/billing'),
  checkout: (plan) => post('/payments/checkout', { plan }),
  subscribe: (data) => post('/payments/subscribe', data),
};

// FINANCE / PILOTAGE
export const financeApi = {
  overview: (period) => get('/finance/overview', period ? { period } : undefined),
  budget: () => get('/finance/budget'),
  forecast: () => get('/finance/forecast'),
  serenity: () => get('/finance/serenity'),
  addEntry: (data) => post('/finance/entry', data),
};

// WELLNESS / BIEN-ETRE
export const wellnessApi = {
  today: () => get('/wellness/today'),
  checkin: (data) => post('/wellness/checkin', data),
  history: () => get('/wellness/history'),
  weeklyReport: () => get('/wellness/weekly-report'),
};

// ESPACE DE TRAVAIL / PROCESSES
export const processesApi = {
  list: () => get('/processes'),
  create: (data) => post('/processes', data),
};

// PROJETS / MISSIONS (Espace de travail)
export const projectsApi = {
  list: () => get('/projects'),
  create: (data) => post('/projects', data),
  start: (id) => post(`/projects/${id}/start`),
  stop: (id) => post(`/projects/${id}/stop`),
  remove: (id) => del(`/projects/${id}`),
};

// PROFILE
export const profileApi = {
  organization: () => get('/profile/organization'),
  customPrompts: () => get('/profile/custom-prompts'),
};

// LICENSE
export const licenseApi = {
  my: () => get('/license/my'),
  activate: (code) => post('/license/activate', { code }),
};

// ONBOARDING
export const onboardingApi = {
  status: () => get('/features/onboarding/status'),
  complete: () => post('/features/onboarding/complete'),
};

// WORDPRESS
export const wpApi = {
  status: () => get('/wp/site-settings'),
  posts: () => get('/wp/posts'),
  products: () => get('/wp/products'),
  pages: () => get('/wp/pages'),
};

// NOTIFICATIONS
export const notificationsApi = {
  list: () => get('/notifications'),
};

// EXPORT
export default apiClient;
export const api = apiClient;
