import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const API_BASE = 'http://localhost:8000'; // Change to your machine's IP for physical device

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// Attach JWT token to every request automatically
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Types ─────────────────────────────────────────────────────────────────────

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  quote_preference: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  response: string;
  was_crisis_flagged: boolean;
  memory_context_used: boolean;
  daily_quote: string | null;
}

export interface DocumentOut {
  id: string;
  filename: string;
  document_type: string;
  notes: string | null;
  is_processed: boolean;
  created_at: string;
}

export interface HealthQuote {
  quote: string;
  author: string | null;
  category: string;
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  register: (data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
  }) => api.post<UserResponse>('/api/users/register', data),

  // OAuth2PasswordRequestForm requires application/x-www-form-urlencoded
  login: (username: string, password: string) => {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    return api.post<TokenResponse>('/api/users/login', form.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },

  me: () => api.get<UserResponse>('/api/users/me'),

  updateQuotePreference: (preference: string) =>
    api.patch<UserResponse>('/api/users/me/quote-preference', {
      quote_preference: preference,
    }),

  googleAuthUrl: () => api.get<{ auth_url: string }>('/api/auth/google'),
};

// ── Chat ──────────────────────────────────────────────────────────────────────

export const chatApi = {
  sendMessage: (message: string, conversationId?: string) =>
    api.post<ChatResponse>('/api/chat/message', {
      message,
      conversation_id: conversationId ?? null,
      include_daily_quote: false,
    }),
};

// ── Documents ─────────────────────────────────────────────────────────────────

export const documentsApi = {
  list: () => api.get<DocumentOut[]>('/api/documents/'),

  upload: (
    fileUri: string,
    filename: string,
    mimeType: string,
    documentType: string,
    notes: string
  ) => {
    const form = new FormData();
    form.append('file', { uri: fileUri, name: filename, type: mimeType } as any);
    form.append('document_type', documentType);
    form.append('notes', notes);
    return api.post('/api/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// ── Quotes ────────────────────────────────────────────────────────────────────

export const quotesApi = {
  daily: (category?: string) =>
    api.get<HealthQuote>('/api/quotes/daily', { params: category ? { category } : {} }),

  random: () => api.get<HealthQuote>('/api/quotes/random'),
};

// ── Health check ──────────────────────────────────────────────────────────────

export const ping = () => api.get('/api/ping');
