<script setup>
import { ref, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { marked } from "marked";
import api from "../services/api.js";
import { useSSE } from "../composables/useSSE.js";
import { useProfile } from "../composables/useProfile.js";
import { useAuth } from "../composables/useAuth.js";
import { useToast } from "../composables/useToast.js";
import QueryInput from "../components/QueryInput.vue";
import StatusTimeline from "../components/StatusTimeline.vue";
import PlanMeta from "../components/PlanMeta.vue";
import PlanDayCards from "../components/PlanDayCards.vue";
import MultiPlanView from "../components/MultiPlanView.vue";
import EmptyState from "../components/EmptyState.vue";

marked.setOptions({ breaks: true, gfm: true });

const route = useRoute();
const router = useRouter();
const { isLoggedIn } = useAuth();
const { buildHint, fetchProfile } = useProfile();
const toast = useToast();

const loading = ref(false);
const apiError = ref("");
const travelPlanRaw = ref("");
const travelPlanHtml = ref("");
const planMeta = ref(null);
const currentSessionId = ref(null);
const sessionTitle = ref("");
const historyMessages = ref([]);
const initialValues = ref({});
const profileHint = ref("");
const modifyMsg = ref("");
const modLoading = ref(false);
const multiLoading = ref(false);
const multiPlanRef = ref(null);
const showMultiPlan = ref(false);

const { events, isRunning, error: sseError, result, start: startSSE } = useSSE();

onMounted(async () => {
  if (isLoggedIn.value) { await fetchProfile(); profileHint.value = buildHint(); }
  const sid = route.query.session;
  if (sid) await loadSession(Number(sid));
});

function parseUserMeta(lastMsg) {
  if (!lastMsg) return {};
  try {
    const meta = lastMsg.meta ? JSON.parse(lastMsg.meta) : {};
    const content = lastMsg.content || "";
    const m = content.match(/从(\S+?)到(\S+?)(?:旅游|玩|规划)/);
    let origin = meta.origin || "";
    let destination = meta.destination || "";
    if (m) { origin = origin || m[1]; destination = destination || m[2]; }
    return { origin, destination, startDate: meta.travel_date || "", endDate: meta.end_date || "", budget: meta.budget || null, notes: meta.preferences?.[0] || "" };
  } catch { return {}; }
}

async function loadSession(sid) {
  try {
    const { data } = await api.get(`/api/sessions/${sid}`);
    currentSessionId.value = data.id; sessionTitle.value = data.title || "";
    historyMessages.value = data.messages || [];
    const lastUser = [...data.messages].reverse().find((m) => m.role === "user");
    if (lastUser) initialValues.value = parseUserMeta(lastUser);
    const lastAssistant = [...data.messages].reverse().find((m) => m.role === "assistant");
    if (lastAssistant) {
      travelPlanRaw.value = lastAssistant.content;
      travelPlanHtml.value = marked.parse(lastAssistant.content);
      try { planMeta.value = JSON.parse(lastAssistant.meta || "{}"); } catch { planMeta.value = null; }
    }
  } catch { router.replace({ path: "/" }); }
}

function startNew() {
  currentSessionId.value = null; sessionTitle.value = ""; historyMessages.value = [];
  initialValues.value = {}; travelPlanHtml.value = ""; travelPlanRaw.value = ""; planMeta.value = null;
  showMultiPlan.value = false; router.replace({ path: "/" });
}

watch(result, (val) => {
  if (val) {
    const plan = val.travel_plan || "";
    travelPlanRaw.value = plan;
    travelPlanHtml.value = plan ? marked.parse(plan) : "_未生成方案。_";
    planMeta.value = val.meta || null;
    if (val.session_id) { currentSessionId.value = val.session_id; router.replace({ query: { session: val.session_id } }); }
    loading.value = false;
    toast.success("方案生成完成");
  }
});

watch(sseError, (val) => { if (val) { apiError.value = val; loading.value = false; toast.error(val); } });

async function onFormSubmit(formData) {
  loading.value = true; apiError.value = ""; travelPlanHtml.value = ""; travelPlanRaw.value = ""; planMeta.value = null;

  // 继续会话时：如果用户没有修改表单，把输入当作文本追加
  let queryOverride = "";
  if (currentSessionId.value && formData.notes && !formData.destination && !formData.budget && !formData.startDate) {
    queryOverride = formData.notes;  // 把备注当作纯文本消息（如"预算添加500"）
  }

  const body = {
    query: queryOverride,
    origin: formData.origin || null, destination: formData.destination || null,
    start_date: formData.startDate || null, end_date: formData.endDate || null,
    budget: formData.budget || null, notes: formData.notes || null,
    session_id: currentSessionId.value || null,
    history: historyMessages.value.length > 0
      ? historyMessages.value.map(m => ({ role: m.role, content: m.content }))
      : null,
  };
  try {
    const { data } = await api.post("/api/plan/stream", body);
    currentSessionId.value = data.session_id;
    startSSE(data.task_id);
  } catch {
    try {
      const { data } = await api.post("/api/plan", body);
      if (data.success) {
        travelPlanRaw.value = data.travel_plan || "";
        travelPlanHtml.value = data.travel_plan ? marked.parse(data.travel_plan) : "";
        planMeta.value = data.meta || null;
        if (data.meta?.session_id) { currentSessionId.value = data.meta.session_id; router.replace({ query: { session: data.meta.session_id } }); }
        toast.success("方案生成完成");
      } else { apiError.value = data.error || "规划失败"; }
    } catch (e) { apiError.value = e.response?.data?.detail || e.message || "请求失败"; toast.error(apiError.value); }
    finally { loading.value = false; }
  }
}

async function onModify() {
  if (!modifyMsg.value.trim() || !currentSessionId.value) return;
  modLoading.value = true;
  try {
    const { data } = await api.post(`/api/plan/modify?session_id=${currentSessionId.value}`, { message: modifyMsg.value.trim(), modify_target: "" });
    if (data.success) { travelPlanRaw.value = data.travel_plan || ""; travelPlanHtml.value = marked.parse(data.travel_plan || ""); modifyMsg.value = ""; toast.success("已修改"); }
  } catch (e) { toast.error(e.response?.data?.detail || "修改失败"); }
  finally { modLoading.value = false; }
}

async function onDayModify({ day, message }) {
  modLoading.value = true;
  try {
    const msg = `第${day}天：${message}`;
    const { data } = await api.post(`/api/plan/modify?session_id=${currentSessionId.value}`, { message: msg, modify_target: `day_${day}` });
    if (data.success) { travelPlanRaw.value = data.travel_plan || ""; travelPlanHtml.value = marked.parse(data.travel_plan || ""); toast.success("已修改第" + day + "天"); }
  } catch (e) { toast.error(e.response?.data?.detail || "修改失败"); }
  finally { modLoading.value = false; }
}

async function onMultiPlan() {
  multiLoading.value = true;
  try {
    await multiPlanRef.value?.generate(planMeta.value?.destination || "", null, null, planMeta.value?.budget || null, "");
    showMultiPlan.value = true;
  }
  finally { multiLoading.value = false; }
}
</script>

<template>
  <div class="page">
    <!-- 继续会话横幅 -->
    <div v-if="currentSessionId" class="session-banner">
      <span>📋 继续规划：<strong>{{ sessionTitle }}</strong> · {{ historyMessages.length }} 条记录</span>
      <button class="btn btn-sm" @click="startNew">+ 新建规划</button>
    </div>

    <!-- 画像提示 -->
    <div v-if="profileHint && !currentSessionId" class="profile-hint">{{ profileHint }}</div>

    <!-- 输入表单 -->
    <QueryInput :disabled="loading" :initial-values="initialValues" @submit="onFormSubmit" />

    <p v-if="apiError" class="text-error text-sm mt-2">{{ apiError }}</p>
    <StatusTimeline :events="events" />

    <!-- 无结果空状态 -->
    <EmptyState v-if="!travelPlanHtml && !loading && !apiError" icon="✈️" title="开始规划你的旅程"
      description="填写出发地、目的地和日期，AI 将为你生成完整的旅行方案" />

    <!-- 结构化结果 -->
    <template v-if="travelPlanRaw">
      <PlanMeta :meta="planMeta" />
      <PlanDayCards :travel-plan="travelPlanRaw" @modify="onDayModify" />

      <!-- 修改/多方案工具栏 -->
      <div class="card mt-2">
        <div class="flex gap-2 items-center flex-wrap">
          <input v-model="modifyMsg" class="input" style="flex:1;min-width:200px" placeholder="全局修改建议，如：预算改为5000…" @keyup.enter="onModify" />
          <button class="btn btn-primary btn-sm" :disabled="!modifyMsg.trim() || modLoading" @click="onModify">{{ modLoading ? "…" : "修改" }}</button>
          <button class="btn btn-sm" :disabled="multiLoading" @click="onMultiPlan">方案对比</button>
        </div>
      </div>
    </template>

    <MultiPlanView ref="multiPlanRef" />
  </div>
</template>

<style scoped>
.session-banner {
  display: flex; align-items: center; justify-content: space-between; gap: var(--s-4);
  padding: var(--s-3) var(--s-5); border-radius: var(--r-md);
  background: var(--c-primary-bg); border: 1px solid #bfdbfe; font-size: .875rem; margin-bottom: var(--s-4);
}
.profile-hint {
  padding: var(--s-2) var(--s-4); border-radius: var(--r-sm);
  background: var(--c-success-bg); border: 1px solid #bbf7d0; font-size: .85rem; color: var(--c-success); margin-bottom: var(--s-3);
}
</style>
