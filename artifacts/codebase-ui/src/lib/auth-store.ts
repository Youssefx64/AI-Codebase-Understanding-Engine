import { create } from "zustand";
import type { AuthUser } from "./api";

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  setUser: (user: AuthUser) => void;
  logout: () => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,

  setUser: (user) => {
    localStorage.setItem("auth_token", user.access_token);
    localStorage.setItem("auth_user", JSON.stringify(user));
    set({ user, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    set({ user: null, isAuthenticated: false });
  },

  loadFromStorage: () => {
    try {
      const raw = localStorage.getItem("auth_user");
      const token = localStorage.getItem("auth_token");
      if (raw && token) {
        const user = JSON.parse(raw) as AuthUser;
        set({ user: { ...user, access_token: token }, isAuthenticated: true });
      }
    } catch {
      localStorage.clear();
    }
  },
}));
