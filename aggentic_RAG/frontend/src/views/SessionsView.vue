<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth.js";
import { useToast } from "../composables/useToast.js";
import api from "../services/api.js";
import EmptyState from "../components/EmptyState.vue";

const router = useRouter();
const { isLoggedIn } = useAuth();
const toast = useToast();

const sessions = ref([]);
const loading = ref(true);
const search = ref("");
const sortBy = ref("updated"); // updated | title | created
const deleteId = ref(null);
const collapsed = ref({});

const filtered = computed(() => {
  let list = [...sessions.value];
  if (search.value.trim()) {
    const kw = search.value.trim().toLowerCase();
    list = list.filter((s) => s.title.toLowerCase().includes(kw));
  }
  list.sort((a, b) => {
    if (sortBy.value === "title") return (a.title || "").localeCompare(b.title || "");
    return (b.updated_at || "").localeCompare(a.updated_at || "");
  });
  return list;
});

onMounted(async () => {
  if (!isLoggedIn.value) { router.push("/login"); return; }
  await loadSessions();
});

async function loadSessions() {
  loading.value = true;
  try { const { data } = await api.get("/api/sessions"); sessions.value = data; } catch { sessions.value = []; }
  finally { loading.value = false; }
}

function openSession(id) { router.push({ path: "/", query: { session: id } }); }
async function delSession(id) {
  try { await api.delete(`/api/sessions/${id}`); sessions.value = sessions.value.filter((s) => s.id !== id); deleteId.value = null; toast.success("已删除"); }
  catch { toast.error("删除失败"); }
}
function newSession() { router.push("/"); }
function fmtDate(ts) { if (!ts) return ""; return ts.replace("T", " ").substring(0, 16); }

// 提取目的地（从标题推断）
function destFromTitle(title) {
  const m = (title || "").match(/(北京|上海|广州|深圳|成都|杭州|南京|重庆|武汉|西安|苏州|厦门|长沙|青岛|天津|昆明|三亚|大理|丽江|桂林|哈尔滨|海口|拉萨|贵阳|乌鲁木齐|呼和浩特|南宁|银川|西宁|兰州|大连|郑州|济南|沈阳|福州|南昌|合肥|太原|长春|石家庄|洛阳|开封|敦煌|黄山|婺源|香格里拉|银川|北海|桂林|三亚)/);
  return m ? m[1] : title?.replace("规划", "").trim() || "旅行";
}
function bgColor(title) {
  const colors = ["#e0f2fe", "#fce7f3", "#f0fdf4", "#fef3c7", "#ede9fe", "#fce4ec", "#e0f7fa"];
  let hash = 0; for (let i = 0; i < (title || "").length; i++) hash = ((hash << 5) - hash) + title.charCodeAt(i);
  return colors[Math.abs(hash) % colors.length];
}
</script>

<template>
  <div class="page">
    <div class="flex items-center justify-between mb-3">
      <h2 style="font-size:1.3rem;font-weight:700">我的规划</h2>
      <button class="btn btn-primary" @click="newSession">+ 新建规划</button>
    </div>

    <!-- 搜索/排序栏 -->
    <div class="flex gap-2 mb-3 flex-wrap">
      <input v-model="search" class="input" style="max-width:280px" placeholder="搜索会话…" />
      <select v-model="sortBy" class="input" style="max-width:160px">
        <option value="updated">最近更新</option>
        <option value="title">按标题</option>
        <option value="created">按创建</option>
      </select>
    </div>

    <div v-if="loading" style="padding:var(--s-12) 0;text-align:center;color:var(--c-text-muted)">加载中…</div>

    <EmptyState v-else-if="filtered.length===0" icon="📋" title="还没有规划记录"
      description="开始你的第一次旅行规划">
      <button class="btn btn-primary mt-2" @click="newSession">开始规划</button>
    </EmptyState>

    <!-- 卡片网格 -->
    <div v-else class="session-grid">
      <div v-for="s in filtered" :key="s.id" class="session-card" :style="{ '--bg': bgColor(s.title) }"
        @click="openSession(s.id)">
        <div class="sc-cover">
          <span class="sc-letter">{{ destFromTitle(s.title)[0] }}</span>
        </div>
        <div class="sc-body">
          <h4 class="sc-title">{{ s.title }}</h4>
          <span class="sc-meta">{{ s.message_count || 0 }} 条消息 · {{ fmtDate(s.updated_at) }}</span>
        </div>
        <div class="sc-actions" @click.stop>
          <button class="btn btn-sm" @click="openSession(s.id)">继续</button>
          <button class="btn btn-sm btn-danger" @click="deleteId === s.id ? delSession(s.id) : (deleteId = s.id)">
            {{ deleteId === s.id ? '确认?' : '删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.session-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--s-4); }
.session-card {
  background: var(--c-surface); border: 1px solid var(--c-border); border-radius: var(--r-md);
  padding: var(--s-5); cursor: pointer; transition: all var(--t-normal); display: flex; flex-direction: column; gap: var(--s-3);
}
.session-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.sc-cover {
  width: 48px; height: 48px; border-radius: var(--r-md); background: var(--bg, #e0f2fe);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.sc-letter { font-size: 1.3rem; font-weight: 800; color: var(--c-primary-dark); }
.sc-body { flex: 1; min-width: 0; }
.sc-title { font-size: .95rem; font-weight: 600; margin: 0 0 2px; }
.sc-meta { font-size: .78rem; color: var(--c-text-secondary); }
.sc-actions { display: flex; gap: var(--s-2); padding-top: var(--s-2); border-top: 1px solid var(--c-border-light); }
</style>
