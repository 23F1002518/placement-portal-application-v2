import { defineStore } from "pinia";

// Auth store: token + user, persisted to localStorage. `role` is derived from user.
export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: null,
    user: null,
  }),

  getters: {
    role: (state) => (state.user ? state.user.role : null),
  },

  actions: {
    loadFromStorage() {
      const token = localStorage.getItem("token");
      const userJson = localStorage.getItem("user");
      if (token && userJson) {
        this.token = token;
        try {
          this.user = JSON.parse(userJson);
        } catch (e) {
          this.user = null;
        }
      }
    },

    setAuth(token, user) {
      this.token = token;
      this.user = user;
      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));
    },

    clearAuth() {
      this.token = null;
      this.user = null;
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    },
  },
});
