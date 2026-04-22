import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { authApi, UserResponse } from '../api/client';

interface AuthState {
  token: string | null;
  user: UserResponse | null;
  isLoading: boolean;

  login: (username: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  loadToken: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  isLoading: true,

  loadToken: async () => {
    try {
      const token = await SecureStore.getItemAsync('auth_token');
      if (token) {
        set({ token });
        await get().refreshUser();
      }
    } catch {
      // token missing or expired — stay logged out
    } finally {
      set({ isLoading: false });
    }
  },

  login: async (username, password) => {
    const res = await authApi.login(username, password);
    const token = res.data.access_token;
    await SecureStore.setItemAsync('auth_token', token);
    set({ token });
    await get().refreshUser();
  },

  register: async (data) => {
    await authApi.register(data);
    // Auto-login after register
    await get().login(data.username, data.password);
  },

  logout: async () => {
    await SecureStore.deleteItemAsync('auth_token');
    set({ token: null, user: null });
  },

  refreshUser: async () => {
    try {
      const res = await authApi.me();
      set({ user: res.data });
    } catch {
      // Token invalid — clear everything
      await SecureStore.deleteItemAsync('auth_token');
      set({ token: null, user: null });
    }
  },
}));
