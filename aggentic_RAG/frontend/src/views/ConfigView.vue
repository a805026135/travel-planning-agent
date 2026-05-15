<script setup>
import { ref, onMounted } from "vue";
import api from "../services/api.js";
import EmptyState from "../components/EmptyState.vue";

const config = ref(null);
const loading = ref(true);
const error = ref("");

onMounted(async () => {
  try { const { data } = await api.get("/api/config"); config.value = data; }
  catch (e) { error.value = e.message || "获取配置失败"; }
  finally { loading.value = false; }
});
</script>

<template>
  <div class="page">
    <h2 style="font-size:1.3rem;font-weight:700;margin-bottom:var(--s-2)">系统配置</h2>
    <p class="text-muted text-sm mb-3">当前系统运行参数（只读）</p>

    <div v-if="loading" class="text-center text-muted" style="padding:var(--s-12) 0">加载中…</div>
    <EmptyState v-else-if="error" icon="⚠️" title="获取配置失败" :description="error" />

    <template v-else-if="config">
      <div class="card mb-2">
        <h3 class="card-title">LLM 模型</h3>
        <div class="kv"><span>主模型</span><code>{{ config.llm?.model }}</code></div>
        <div class="kv"><span>深度分析 (R1)</span><code>{{ config.llm?.r1_model }}</code></div>
      </div>
      <div class="card mb-2">
        <h3 class="card-title">RAG 知识库</h3>
        <div class="kv"><span>分块大小</span><code>{{ config.rag?.chunk_size }}</code></div>
        <div class="kv"><span>检索数量</span><code>{{ config.rag?.search_k }}</code></div>
        <div class="kv"><span>批处理</span><code>{{ config.rag?.batch_size }}</code></div>
        <div class="kv"><span>数据库路径</span><code style="font-size:.75rem">{{ config.rag?.persist_dir }}</code></div>
      </div>
      <div class="card">
        <h3 class="card-title">MCP 服务</h3>
        <div class="kv"><span>配置文件</span><code style="font-size:.75rem">{{ config.mcp?.config_path }}</code></div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.kv {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 0; border-bottom: 1px solid var(--c-border-light);
  font-size: .875rem;
}
.kv:last-child { border-bottom: none; }
.kv span { color: var(--c-text-secondary); }
.kv code {
  font-size: .8rem; background: var(--c-bg); padding: 2px 8px;
  border-radius: 4px; color: var(--c-primary); font-family: var(--font-mono);
}
</style>
