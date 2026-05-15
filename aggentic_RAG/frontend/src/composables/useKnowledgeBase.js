import { ref } from "vue";
import api from "../services/api.js";

/**
 * 知识库管理 composable
 */
export function useKnowledgeBase() {
  const stats = ref({ total: 0, sources: [] });
  const loading = ref(false);

  async function fetchStats() {
    loading.value = true;
    try {
      const { data } = await api.get("/api/knowledge/stats");
      stats.value = data;
    } catch {
      stats.value = { total: 0, sources: [] };
    } finally {
      loading.value = false;
    }
  }

  async function uploadFile(file) {
    const form = new FormData();
    form.append("file", file);
    const { data } = await api.post("/api/knowledge/upload", form);
    await fetchStats();
    return data;
  }

  async function deleteSource(source) {
    const { data } = await api.delete("/api/knowledge/source", {
      data: { source },
      headers: { "Content-Type": "application/json" },
    });
    await fetchStats();
    return data;
  }

  async function buildKnowledgeBase(sourcePath, forceRecreate = false) {
    loading.value = true;
    try {
      const { data } = await api.post("/api/knowledge/build", {
        source_path: sourcePath,
        force_recreate: forceRecreate,
      });
      await fetchStats();
      return data;
    } finally {
      loading.value = false;
    }
  }

  return { stats, loading, fetchStats, uploadFile, deleteSource, buildKnowledgeBase };
}
