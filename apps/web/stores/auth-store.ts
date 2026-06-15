import { create } from "zustand";

interface AuthState {
  token: string | null;
  user: { id: string; email: string; role: string; orgId: string } | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: AuthState["user"]) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  setAuth: (token, user) => set({ token, user, isAuthenticated: true }),
  logout: () => set({ token: null, user: null, isAuthenticated: false }),
}));
