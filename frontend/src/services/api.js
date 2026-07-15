import { useAuthStore } from "@/stores/auth";

// Base URL of the backend API server. When the frontend and backend run as
// separate servers, set VITE_API_BASE_URL (e.g. http://localhost:5000) so calls
// go cross-origin directly to Flask. If unset, paths stay relative ("/api/..."),
// which works with the Vite dev proxy or when Flask serves the SPA same-origin.
const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

// Fetch wrapper: attaches the JWT, parses JSON, normalizes errors, handles 401.
export const api = {
  async request(method, path, { body, isForm } = {}) {
    const store = useAuthStore();
    const headers = {};
    if (store.token) headers["Authorization"] = `Bearer ${store.token}`;
    if (!isForm) headers["Content-Type"] = "application/json";

    const res = await fetch(`${API_BASE}/api${path}`, {
      method,
      headers,
      body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
    });

    if (res.status === 401) {
      store.clearAuth();
      window.location.hash = "#/login";
      const err = new Error("Session expired");
      err.status = 401;
      throw err;
    }

    let data = null;
    const text = await res.text();
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (e) {
        data = null;
      }
    }

    if (!res.ok) {
      const err = new Error((data && data.message) || "Request failed");
      err.status = res.status;
      err.errors = (data && data.errors) || null;
      throw err;
    }

    return data;
  },

  get(path) {
    return this.request("GET", path);
  },
  post(path, body) {
    return this.request("POST", path, { body });
  },
  put(path, body) {
    return this.request("PUT", path, { body });
  },
  postForm(path, formData) {
    return this.request("POST", path, { body: formData, isForm: true });
  },

  // File downloads need the Authorization header too, which a plain <a href> can't send.
  async getBlob(path) {
    const store = useAuthStore();
    const headers = {};
    if (store.token) headers["Authorization"] = `Bearer ${store.token}`;
    const res = await fetch(`${API_BASE}/api${path}`, { headers });
    if (res.status === 401) {
      store.clearAuth();
      window.location.hash = "#/login";
      throw new Error("Session expired");
    }
    if (!res.ok) {
      const err = new Error("Download failed");
      err.status = res.status;
      throw err;
    }
    return res.blob();
  },

  async downloadBlob(path, filename) {
    const blob = await this.getBlob(path);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};
