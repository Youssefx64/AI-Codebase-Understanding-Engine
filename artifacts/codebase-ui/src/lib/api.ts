import axios from "axios";

const BASE = "/engine";

export const api = axios.create({ baseURL: BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface AuthUser {
  user_id: string;
  email: string;
  username: string;
  access_token: string;
}

export const authApi = {
  register: (data: { email: string; username: string; password: string }) =>
    api.post<AuthUser>("/auth/register", data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    api.post<AuthUser>("/auth/login", data).then((r) => r.data),

  me: () =>
    api
      .get<{ user_id: string; email: string; username: string; created_at: string }>("/auth/me")
      .then((r) => r.data),
};

// ── Repos ─────────────────────────────────────────────────────────────────────

export interface RepoListItem {
  repo_id: string;
  github_url: string;
  owner: string;
  name: string;
  branch: string;
  status: string;
  file_count: number;
  total_lines: number;
  languages: string[];
  created_at: string;
  completed_at: string | null;
}

export interface RepoSummary {
  repo_id: string;
  github_url: string;
  status: string;
  languages: string[];
  file_count: number;
  total_lines: number;
  architecture_summary: string | null;
  created_at: string;
  completed_at: string | null;
}

export const repoApi = {
  list: () => api.get<RepoListItem[]>("/my-repos").then((r) => r.data),

  listAll: (limit = 20, offset = 0) =>
    api.get<RepoSummary[]>("/repo-summary", { params: { limit, offset } }).then((r) => r.data),

  analyze: (github_url: string, branch = "main", force_reanalysis = false) =>
    api
      .post<{ repo_id: string; status: string; message: string }>("/analyze-repo", {
        github_url,
        branch,
        force_reanalysis,
      })
      .then((r) => r.data),

  summary: (id: string) => api.get<RepoSummary>(`/repo-summary/${id}`).then((r) => r.data),

  delete: (id: string) => api.delete(`/repo/${id}`),
};

// ── Analysis ──────────────────────────────────────────────────────────────────

export interface CodeIssue {
  issue_id: string;
  repo_id: string;
  file_path: string;
  line: number | null;
  issue_type: string;
  severity: string;
  message: string;
  suggestion: string | null;
}

export interface RefactorSuggestion {
  suggestion_id: string;
  repo_id: string;
  file_path: string;
  title: string;
  description: string;
  pattern: string | null;
  original_code: string | null;
  suggested_code: string | null;
  effort: string;
}

export interface GraphData {
  repo_id: string;
  nodes: { node_id: string; node_type: string; name: string; file_path?: string }[];
  edges: { source_id: string; target_id: string; edge_type: string }[];
}

export interface AskResponse {
  repo_id: string;
  question: string;
  answer: string;
  source_chunks: { file_path: string; content: string; start_line: number; end_line: number }[];
}

export const analysisApi = {
  issues: (id: string, severity?: string) =>
    api
      .get<CodeIssue[]>(`/issues/${id}`, { params: severity ? { severity } : {} })
      .then((r) => r.data),

  refactor: (id: string) =>
    api.get<RefactorSuggestion[]>(`/refactor/${id}`).then((r) => r.data),

  graph: (id: string, node_type?: string) =>
    api
      .get<GraphData>(`/dependency-graph/${id}`, { params: node_type ? { node_type } : {} })
      .then((r) => r.data),

  ask: (repo_id: string, question: string, max_chunks = 5) =>
    api
      .post<AskResponse>("/ask", { repo_id, question, max_chunks })
      .then((r) => r.data),
};

// ── WebSocket progress ────────────────────────────────────────────────────────

export function createProgressSocket(
  repoId: string,
  onMessage: (data: {
    repo_id: string;
    status: string;
    file_count: number;
    total_lines: number;
    error_message: string | null;
  }) => void,
  onClose?: () => void
): WebSocket {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/engine/ws/progress/${repoId}`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  ws.onclose = () => onClose?.();
  return ws;
}
