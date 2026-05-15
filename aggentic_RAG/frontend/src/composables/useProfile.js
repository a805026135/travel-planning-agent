import { ref } from "vue";
import api from "../services/api.js";

export function useProfile() {
  const profile = ref(null);
  const loading = ref(false);

  async function fetchProfile() {
    loading.value = true;
    try {
      const { data } = await api.get("/api/profile");
      profile.value = data;
    } catch {
      profile.value = null;
    } finally {
      loading.value = false;
    }
  }

  async function updateProfile(updates) {
    const { data } = await api.put("/api/profile", updates);
    profile.value = data.profile;
  }

  function buildHint() {
    const p = profile.value;
    if (!p) return "";
    const tags = [];
    if (p.preferred_transport) tags.push(p.preferred_transport === "train" ? "高铁" : p.preferred_transport === "car" ? "自驾" : p.preferred_transport);
    if (p.preferred_hotel_level) tags.push({ economic: "经济型", comfort: "舒适型", luxury: "豪华型" }[p.preferred_hotel_level] || "");
    if (p.common_departure_city) tags.push("常住" + p.common_departure_city);
    const styles = (p.travel_style_tags || []).slice(0, 3);
    tags.push(...styles);
    const filtered = tags.filter(Boolean);
    if (!filtered.length) return "";
    return "已根据您的偏好预填：" + filtered.join("、");
  }

  return { profile, loading, fetchProfile, updateProfile, buildHint };
}
