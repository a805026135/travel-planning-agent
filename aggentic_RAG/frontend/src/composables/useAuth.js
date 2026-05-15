import { ref, computed } from "vue";
import api from "../services/api.js";

const token = ref(localStorage.getItem("token") || "");
const username = ref(localStorage.getItem("username") || "");
const userId = ref(Number(localStorage.getItem("userId")) || 0);
const isAdmin = ref(false);

export function useAuth() {
  const isLoggedIn = computed(() => !!token.value);

  function saveAuth(data) {
    token.value = data.token;
    username.value = data.username;
    userId.value = data.user_id;
    localStorage.setItem("token", data.token);
    localStorage.setItem("username", data.username);
    localStorage.setItem("userId", String(data.user_id));
    checkAdmin();
  }

  function clearAuth() {
    token.value = "";
    username.value = "";
    userId.value = 0;
    isAdmin.value = false;
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("userId");
  }

  async function checkAdmin() {
    if (!token.value) { isAdmin.value = false; return; }
    try {
      const { data } = await api.get("/api/auth/admin/check");
      isAdmin.value = !!data.is_admin;
    } catch {
      isAdmin.value = false;
    }
  }

  async function login(u, p) {
    const { data } = await api.post("/api/auth/login", { username: u, password: p });
    if (data.success) {
      saveAuth(data);
    }
    return data;
  }

  async function register(u, p) {
    const { data } = await api.post("/api/auth/register", { username: u, password: p });
    if (data.success) {
      saveAuth(data);
    }
    return data;
  }

  function logout() {
    clearAuth();
  }

  return { token, username, userId, isAdmin, isLoggedIn, login, register, logout, checkAdmin };
}
