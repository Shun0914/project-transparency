import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

const TOKEN_KEY = 'access_token';

// トークン管理
export const setToken = (token: string): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
  }
};

export const getToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
};

export const removeToken = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
  }
};

export const isAuthenticated = (): boolean => {
  return getToken() !== null;
};

// 認証API

export interface User {
  id: number;
  email: string;
  name: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export const login = async (credentials: LoginRequest): Promise<AuthResponse> => {
  console.log('[AUTH] Logging in...');
  const response = await axios.post<AuthResponse>(
    `${API_BASE_URL}/auth/login`,
    credentials
  );
  console.log('[AUTH] Login successful, token:', response.data.access_token.substring(0, 20) + '...');
  setToken(response.data.access_token);
  console.log('[AUTH] Token saved to localStorage');
  const savedToken = getToken();
  console.log('[AUTH] Verified token in localStorage:', savedToken ? 'YES' : 'NO');
  return response.data;
};

export const register = async (userData: RegisterRequest): Promise<AuthResponse> => {
  console.log('[AUTH] Registering...');
  const response = await axios.post<AuthResponse>(
    `${API_BASE_URL}/auth/register`,
    userData
  );
  console.log('[AUTH] Registration successful, token:', response.data.access_token.substring(0, 20) + '...');
  setToken(response.data.access_token);
  console.log('[AUTH] Token saved to localStorage');
  const savedToken = getToken();
  console.log('[AUTH] Verified token in localStorage:', savedToken ? 'YES' : 'NO');
  return response.data;
};

export const logout = (): void => {
  removeToken();
  if (typeof window !== 'undefined') {
    window.location.href = '/auth/login';
  }
};

export const getCurrentUser = async (): Promise<User> => {
  const token = getToken();
  if (!token) {
    throw new Error('No token found');
  }

  const response = await axios.get<User>(
    `${API_BASE_URL}/auth/me`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  return response.data;
};
