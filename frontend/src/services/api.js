import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Error]', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// ─── Interaction API ────────────────────────────────────────────────────────────

export const interactionAPI = {
  getAll: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.skip !== undefined) queryParams.append('skip', params.skip);
    if (params.limit !== undefined) queryParams.append('limit', params.limit);
    if (params.interaction_type) queryParams.append('interaction_type', params.interaction_type);
    if (params.sentiment) queryParams.append('sentiment', params.sentiment);
    if (params.hcp_id) queryParams.append('hcp_id', params.hcp_id);
    if (params.search) queryParams.append('search', params.search);
    if (params.date_from) queryParams.append('date_from', params.date_from);
    if (params.date_to) queryParams.append('date_to', params.date_to);
    const qs = queryParams.toString();
    return api.get(`/interactions${qs ? `?${qs}` : ''}`);
  },

  getById: (id) => api.get(`/interactions/${id}`),

  create: (data) => api.post('/interactions', data),

  update: (id, data) => api.put(`/interactions/${id}`, data),

  delete: (id) => api.delete(`/interactions/${id}`),

  processNotes: (notes) =>
    api.post('/interactions/process-notes', { raw_notes: notes }),
};

// ─── HCP API ────────────────────────────────────────────────────────────────────

export const hcpAPI = {
  getAll: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.skip !== undefined) queryParams.append('skip', params.skip);
    if (params.limit !== undefined) queryParams.append('limit', params.limit);
    if (params.specialty) queryParams.append('specialty', params.specialty);
    if (params.tier) queryParams.append('tier', params.tier);
    if (params.search) queryParams.append('search', params.search);
    const qs = queryParams.toString();
    return api.get(`/hcps${qs ? `?${qs}` : ''}`);
  },

  getById: (id) => api.get(`/hcps/${id}`),

  create: (data) => api.post('/hcps', data),
};

// ─── Agent / AI API ─────────────────────────────────────────────────────────────

export const agentAPI = {
  chat: (message) => api.post('/agent/chat', { message }),

  processNotes: (notes) =>
    api.post('/agent/process-notes', { raw_notes: notes }),

  getTools: () => api.get('/agent/tools'),
};

export default api;
