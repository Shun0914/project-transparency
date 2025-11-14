import axios from 'axios';
import { getToken, removeToken } from './auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// リクエストインターセプター: Authorizationヘッダーを自動追加
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    console.log('[API] Request interceptor - Token:', token ? `${token.substring(0, 20)}...` : 'NONE');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('[API] Authorization header added');
    } else {
      console.log('[API] No token found, skipping Authorization header');
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// レスポンスインターセプター: 401エラー時にログイン画面にリダイレクト
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      removeToken();
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login';
      }
    }
    return Promise.reject(error);
  }
);

// Types
export interface Project {
  id: number;
  name: string;
  document_url: string;
  created_at: string;
}

export interface Member {
  id: number;
  project_id: number;
  name: string;
  role: 'Member' | 'PM' | 'PL';
  email?: string;
  created_at: string;
}

export interface MemberWithScore extends Omit<Member, 'project_id' | 'created_at'> {
  latest_score?: number;
  latest_score_at?: string;
}

export interface Score {
  id: number;
  member_id: number;
  score: number;
  comment?: string;
  created_at: string;
}

export interface MemberSummary {
  id: number;
  name: string;
  role: 'Member' | 'PM' | 'PL';
  weight: number;
  latest_score?: number;
  latest_comment?: string;
  latest_score_at?: string;
}

export interface TimelinePoint {
  date: string;
  weighted_average: number;
}

export interface DashboardData {
  project: {
    id: number;
    name: string;
    document_url: string;
  };
  weighted_average?: number;
  last_updated?: string;
  members_summary: MemberSummary[];
  timeline: TimelinePoint[];
}

// API Functions

// Projects
export const getProjects = async (): Promise<Project[]> => {
  const response = await api.get<{ projects: Project[] }>('/projects');
  return response.data.projects;
};

export const createProject = async (data: { name: string; document_url: string }): Promise<Project> => {
  const response = await api.post<Project>('/projects', data);
  return response.data;
};

export const getProject = async (projectId: number): Promise<Project & { members: Member[] }> => {
  const response = await api.get<Project & { members: Member[] }>(`/projects/${projectId}`);
  return response.data;
};

// Members
export const getMembers = async (projectId: number): Promise<MemberWithScore[]> => {
  const response = await api.get<{ members: MemberWithScore[] }>(`/projects/${projectId}/members`);
  return response.data.members;
};

export const createMember = async (
  projectId: number,
  data: { name: string; role: 'Member' | 'PM' | 'PL'; email?: string }
): Promise<Member> => {
  const response = await api.post<Member>(`/projects/${projectId}/members`, data);
  return response.data;
};

// Scores
export const createScore = async (
  memberId: number,
  data: { score: number; comment?: string }
): Promise<Score> => {
  const response = await api.post<Score>(`/members/${memberId}/scores`, data);
  return response.data;
};

export const getScores = async (
  memberId: number
): Promise<{ member: { id: number; name: string; role: string }; scores: Score[] }> => {
  const response = await api.get<{ member: { id: number; name: string; role: string }; scores: Score[] }>(
    `/members/${memberId}/scores`
  );
  return response.data;
};

// Dashboard
export const getDashboard = async (projectId: number): Promise<DashboardData> => {
  const response = await api.get<DashboardData>(`/projects/${projectId}/dashboard`);
  return response.data;
};

export default api;
