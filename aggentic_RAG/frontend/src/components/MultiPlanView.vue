<script setup>
import { ref } from "vue";
import { marked } from "marked";
import api from "../services/api.js";

const emit = defineEmits(["close"]);

const plans = ref([]);
const loading = ref(false);
const activeTab = ref(0);

async function generate(destination, startDate, endDate, budget, notes) {
  loading.value = true;
  try {
    const { data } = await api.post("/api/plan/multi-plan", {
      destination, start_date: startDate, end_date: endDate,
      budget, notes, num_plans: 3,
    });
    plans.value = data.plans || [];
  } catch (e) {
    plans.value = [{ style: "错误", travel_plan: "生成失败: " + (e.response?.data?.detail || e.message) }];
  } finally {
    loading.value = false;
  }
}

function renderMd(text) {
  return marked.parse(text || "");
}

defineExpose({ generate });
</script>

<template>
  <div v-if="plans.length > 0 || loading" class="multi-plan card">
    <h3>方案对比</h3>
    <div v-if="loading" class="hint">正在生成多个方案...</div>
    <template v-else>
      <div class="tabs">
        <button v-for="(p, i) in plans" :key="i" :class="['tab', { active: activeTab === i }]"
          @click="activeTab = i">
          {{ p.style }}
        </button>
      </div>
      <div v-if="plans[activeTab]" class="plan-content">
        <article class="markdown-body" v-html="renderMd(plans[activeTab].travel_plan)" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.multi-plan { margin-top: 1rem; }
.tabs { display: flex; gap: 0; margin-bottom: 1rem; border: 1px solid var(--color-border); border-radius: 8px; overflow: hidden; }
.tab { flex: 1; padding: 0.4rem 0.8rem; border: none; background: #fff; font-size: 0.85rem; cursor: pointer; }
.tab:not(:last-child) { border-right: 1px solid var(--color-border); }
.tab.active { background: var(--color-primary); color: #fff; }
.plan-content { max-height: 600px; overflow-y: auto; }
</style>
