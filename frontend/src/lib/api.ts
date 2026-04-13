import axios from "axios";
import type { ChallanSection } from "@/types";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
  timeout: 120_000,
});

function isCredentialAuthPath(url: string | undefined): boolean {
  if (!url) return false;
  return url.includes("/auth/login") || url.includes("/auth/register");
}

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined" && !isCredentialAuthPath(config.url)) {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !isCredentialAuthPath(error.config?.url)) {
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post("/api/v1/auth/refresh", {
            refresh_token: refreshToken,
          });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          error.config.headers.Authorization = `Bearer ${data.access_token}`;
          return api(error.config);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  register: (data: { email: string; password: string; full_name: string; state?: string }) =>
    api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
  me: () => api.get("/auth/me"),
};

// Legal
export const legalApi = {
  query: (data: {
    query: string;
    state?: string;
    city?: string;
    language?: string;
    language_explicit?: boolean;
    vehicle_type?: string;
    case_id?: string;
    thread_id?: string;
  }) => api.post("/legal/query", data),
};

// Challan
export interface ChallanValidatePayload {
  challan_number?: string;
  state: string;
  sections: ChallanSection[];
  location?: string;
  issuing_officer?: string;
  officer_badge_number?: string;
  issued_at?: string;
  raw_text?: string;
  case_id?: string;
}

export interface ScheduleSectionItem {
  section: string;
  offense: string;
  max_fine: number;
}

export const challanApi = {
  validate: (data: ChallanValidatePayload) => api.post("/challan/validate", data),
  get: (id: string) => api.get(`/challan/${id}`),
  scheduleSections: (state: string) =>
    api.get<ScheduleSectionItem[]>("/challan/schedule-sections", { params: { state } }),
};

// Cases
export interface CaseCreatePayload {
  case_type: "traffic_stop" | "challan" | "misconduct";
  title: string;
  description?: string;
  state?: string;
  city?: string;
  location?: string;
}

export interface CaseListParams {
  status?: string;
  case_type?: string;
  skip?: number;
  limit?: number;
}

export const casesApi = {
  create: (data: CaseCreatePayload) => api.post("/cases", data),
  list: (params?: CaseListParams) => api.get("/cases", { params }),
  get: (id: string) => api.get(`/cases/${id}`),
  update: (id: string, data: Partial<CaseCreatePayload>) => api.patch(`/cases/${id}`, data),
};

// Evidence
export const evidenceApi = {
  upload: (caseId: string, file: File) => {
    const form = new FormData();
    form.append("case_id", caseId);
    form.append("file", file);
    return api.post("/evidence/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  get: (id: string) => api.get(`/evidence/${id}`),
  analyze: (id: string) => api.post(`/evidence/${id}/analyze`),
  listByCase: (caseId: string) => api.get(`/evidence/case/${caseId}`),
};

// Complaints
export const complaintsApi = {
  draft: (data: { case_id?: string; complaint_type: string; description?: string; language?: string }) =>
    api.post("/complaints/draft", data),
  edit: (id: string, data: { final_text: string }) =>
    api.put(`/complaints/${id}`, data),
  submit: (id: string, data: { user_consent: boolean; portal_name?: string }) =>
    api.post(`/complaints/${id}/submit`, data),
  get: (id: string) => api.get(`/complaints/${id}`),
  getActions: (id: string) => api.get(`/complaints/${id}/actions`),
  escalate: (id: string) => api.post(`/complaints/${id}/escalate`),
  portalInfo: (state: string) => api.get(`/complaints/portal-info/${state}`),
  downloadPdf: (id: string) =>
    api.get(`/complaints/${id}/download-pdf`, { responseType: "blob" }),
};

// Analytics (public, no auth)
export const analyticsApi = {
  overcharges: (state?: string) =>
    api.get("/analytics/overcharges", { params: { state } }),
  heatmap: (state?: string) =>
    api.get("/analytics/heatmap", { params: { state } }),
  resolutionRates: () => api.get("/analytics/resolution-rates"),
  stateStats: (stateCode: string) =>
    api.get(`/analytics/state/${stateCode}`),
};

export default api;
