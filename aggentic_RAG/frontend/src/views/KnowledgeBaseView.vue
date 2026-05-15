<script setup>
import { ref, computed, onMounted } from "vue";
import { useAuth } from "../composables/useAuth.js";
import { useToast } from "../composables/useToast.js";
import api from "../services/api.js";
import EmptyState from "../components/EmptyState.vue";

const { isLoggedIn, isAdmin } = useAuth();
const toast = useToast();
const tab = ref("system");
const stats = ref({ total: 0, sources: [] });
const loading = ref(false);
const uploadProgress = ref(0);
const uploading = ref(false);
const deleteTarget = ref(null);
const previewSrc = ref(null);

onMounted(() => { fetchStats(); });

async function fetchStats() {
  loading.value = true;
  try {
    const prefix = tab.value === "personal" ? "/api/user/knowledge" : "/api/knowledge";
    const { data } = await api.get(`${prefix}/stats`);
    stats.value = data;
  } catch { stats.value = { total: 0, sources: [] }; }
  finally { loading.value = false; }
}

function switchTab(t) { tab.value = t; fetchStats(); }

async function handleFiles(e) {
  const files = e.dataTransfer ? e.dataTransfer.files : e.target.files;
  if (!files?.length) return;
  uploading.value = true; uploadProgress.value = 0;
  const prefix = tab.value === "personal" ? "/api/user/knowledge" : "/api/knowledge";
  for (let i = 0; i < files.length; i++) {
    const form = new FormData(); form.append("file", files[i]);
    try { await api.post(`${prefix}/upload`, form); }
    catch (err) { toast.error(err.response?.data?.detail || "上传失败"); }
    uploadProgress.value = Math.round(((i + 1) / files.length) * 100);
  }
  uploading.value = false; toast.success("上传完成"); fetchStats();
}

async function handleDelete(src) {
  const prefix = tab.value === "personal" ? "/api/user/knowledge" : "/api/knowledge";
  try {
    await api.delete(`${prefix}/source`, { data: { source: src }, headers: { "Content-Type": "application/json" } });
    toast.success("已删除"); deleteTarget.value = null; fetchStats();
  } catch { toast.error("删除失败"); }
}

function formatSrc(src) {
  const parts = (src || "").replace(/\\/g, "/").split("/");
  return parts[parts.length - 1] || src;
}

const canUpload = computed(() => tab.value === "personal" ? isLoggedIn.value : isAdmin.value);
const fileInput = ref(null);

function triggerUpload() { fileInput.value?.click(); }
</script>

<template>
  <div class="page">
    <h2 style="font-size:1.3rem;font-weight:700;margin-bottom:var(--s-2)">知识库管理</h2>

    <!-- 胶囊标签 -->
    <div class="pill-tabs mb-3">
      <button :class="['pill', { active: tab === 'system' }]" @click="switchTab('system')">📚 系统知识库</button>
      <button :class="['pill', { active: tab === 'personal' }]" @click="switchTab('personal')" :disabled="!isLoggedIn">
        🔒 个人知识库{{ !isLoggedIn ? '（请登录）' : '' }}
      </button>
    </div>

    <!-- 统计 -->
    <div class="card mb-2">
      <div class="flex items-center justify-between">
        <span class="font-weight:600">共 <strong>{{ stats.total }}</strong> 个文档块，<strong>{{ (stats.sources || []).length }}</strong> 个来源</span>
      </div>
    </div>

    <!-- 拖拽上传区域 -->
    <div class="card" v-if="canUpload !== false">
      <div class="drop-zone" :class="{ dragging: uploading }" @dragover.prevent @drop.prevent="handleFiles" @click="triggerUpload">
        <span style="font-size:2rem">📁</span>
        <p v-if="uploading">上传中… {{ uploadProgress }}%</p>
        <p v-else>拖拽文件到此处，或<u>点击选择</u> (TXT/MD/PDF/CSV)</p>
        <div v-if="uploading" class="progress-bar"><div class="progress-fill" :style="{ width: uploadProgress + '%' }" /></div>
      </div>
      <input type="file" ref="fileInput" accept=".txt,.md,.pdf,.csv" multiple hidden @change="handleFiles" />
    </div>
    <div v-else class="card mb-2">
      <p class="text-muted text-sm text-center" style="padding:var(--s-6) 0">
        {{ tab === 'system' ? '仅管理员可上传系统知识库文件' : '请先登录以使用个人知识库' }}
      </p>
    </div>

    <!-- 来源列表 -->
    <div class="card" v-if="(stats.sources || []).length > 0">
      <h3 class="card-title mb-2">数据源</h3>
      <div class="source-list">
        <div v-for="src in stats.sources" :key="src" class="source-row">
          <span class="src-icon">{{ src.endsWith('.pdf') ? '📕' : src.endsWith('.csv') ? '📊' : src.endsWith('.md') ? '📝' : '📄' }}</span>
          <span class="src-name">{{ formatSrc(src) }}</span>
          <span class="src-path text-xs text-muted">{{ src }}</span>
          <button class="btn btn-sm btn-ghost" @click="previewSrc = previewSrc === src ? null : src">👁</button>
          <button class="btn btn-sm btn-danger" v-if="canUpload !== false" @click="deleteTarget === src ? handleDelete(src) : (deleteTarget = src)">
            {{ deleteTarget === src ? '确认删除?' : '🗑' }}
          </button>
        </div>
      </div>
      <!-- 预览 -->
      <div v-if="previewSrc" class="preview-box mt-2">
        <div class="flex items-center justify-between mb-1"><strong>{{ formatSrc(previewSrc) }}</strong><button class="btn btn-sm btn-ghost" @click="previewSrc = null">✕</button></div>
        <p class="text-sm text-muted">点击右上角 ✕ 关闭预览</p>
      </div>
    </div>

    <EmptyState v-if="!loading && (!stats.sources || stats.sources.length === 0)" icon="📚"
      title="知识库为空" description="上传旅行攻略文档来丰富知识库" />
  </div>
</template>

<style scoped>
.pill-tabs { display: inline-flex; border: 1px solid var(--c-border); border-radius: 99px; overflow: hidden; }
.pill {
  padding: var(--s-2) var(--s-5); border: none; background: var(--c-surface); font-size: .875rem;
  font-family: var(--font); cursor: pointer; transition: all var(--t-fast); white-space: nowrap;
}
.pill:not(:last-child) { border-right: 1px solid var(--c-border); }
.pill.active { background: var(--c-primary); color: #fff; font-weight: 600; }
.pill:disabled { opacity: .5; cursor: not-allowed; }
.drop-zone {
  border: 2px dashed var(--c-border); border-radius: var(--r-md); padding: var(--s-8);
  text-align: center; cursor: pointer; transition: all var(--t-normal); color: var(--c-text-secondary);
}
.drop-zone:hover { border-color: var(--c-primary); background: var(--c-primary-bg); }
.progress-bar { width: 100%; height: 6px; background: var(--c-border-light); border-radius: 99px; margin-top: var(--s-3); overflow: hidden; }
.progress-fill { height: 100%; background: var(--c-primary); border-radius: 99px; transition: width .3s ease; }
.source-list { display: flex; flex-direction: column; gap: var(--s-2); }
.source-row { display: flex; align-items: center; gap: var(--s-3); padding: var(--s-2) var(--s-3); border-radius: var(--r-sm); transition: background var(--t-fast); }
.source-row:hover { background: var(--c-bg); }
.src-icon { font-size: 1.2rem; flex-shrink: 0; }
.src-name { font-size: .875rem; font-weight: 500; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.src-path { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex-shrink: 0; }
.preview-box { padding: var(--s-4); background: var(--c-bg); border-radius: var(--r-sm); border: 1px solid var(--c-border); }
</style>
