<script setup>
import { ref, computed } from "vue";
import { marked } from "marked";

const props = defineProps({
  travelPlan: { type: String, default: "" },
});
const emit = defineEmits(["modify"]);

const modifyDay = ref(null);
const modifyMsg = ref("");

// 解析 Markdown 中的日行程段
const segments = computed(() => {
  const raw = props.travelPlan;
  if (!raw) return [];

  // 按日切割: Day N / 第N天 / 【第N天】 / N天
  const dayRe = /(?:^|\n)(?:#{1,4}\s*)?(?:【?\s*第\s*(\d+)\s*天[^\n]*|\*\*Day\s*(\d+)\*\*|##\s*Day\s*(\d+))/gi;
  const parts = [];
  let lastIdx = 0;

  // 简单策略: 按 ## 标题分割
  const sections = raw.split(/\n(?=#{2,3}\s)/);
  for (const sec of sections) {
    const m = sec.match(/第\s*(\d+)\s*天|Day\s*(\d+)/i);
    const day = m ? (parseInt(m[1] || m[2]) || null) : null;
    parts.push({ day, html: marked.parse(sec), raw: sec });
  }

  if (parts.length === 0 && raw.trim()) {
    // 无分天结构 → 整体作为一个卡片
    return [{ day: null, html: marked.parse(raw), raw, isOverview: true }];
  }
  return parts;
});

function openModify(day) {
  modifyDay.value = day;
  modifyMsg.value = "";
}
function submitModify() {
  if (!modifyMsg.value.trim()) return;
  emit("modify", { day: modifyDay.value, message: modifyMsg.value.trim() });
  modifyDay.value = null;
  modifyMsg.value = "";
}
</script>

<template>
  <div v-if="segments.length" class="plan-days">
    <div v-for="(seg, i) in segments" :key="i" class="day-card card">
      <div class="day-header flex items-center justify-between" @click="seg.expanded = !seg.expanded">
        <span class="day-title">
          {{ seg.isOverview ? '📋 概览' : seg.day ? `📍 第 ${seg.day} 天` : '📌 详情' }}
        </span>
        <span class="day-toggle">{{ seg.expanded ? '▾' : '▸' }}</span>
      </div>
      <div v-show="seg.expanded !== false" class="day-body">
        <article class="markdown-body" v-html="seg.html" />
        <button v-if="seg.day" class="btn btn-sm mt-1" @click="openModify(seg.day)">✏️ 修改该天</button>
      </div>
    </div>

    <!-- 修改弹窗 -->
    <div v-if="modifyDay" class="modify-overlay" @click.self="modifyDay = null">
      <div class="modify-dialog card">
        <h4>修改第 {{ modifyDay }} 天</h4>
        <input v-model="modifyMsg" class="input mt-1" placeholder="如：少安排一个景点，太累了" @keyup.enter="submitModify" />
        <div class="flex gap-1 mt-1">
          <button class="btn btn-primary btn-sm" @click="submitModify">提交</button>
          <button class="btn btn-sm" @click="modifyDay = null">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.plan-days { display: flex; flex-direction: column; gap: var(--s-2); }
.day-card { padding: 0; overflow: hidden; }
.day-header { padding: var(--s-3) var(--s-5); cursor: pointer; user-select: none; transition: background var(--t-fast); }
.day-header:hover { background: var(--c-bg); }
.day-title { font-weight: 600; font-size: .95rem; }
.day-toggle { font-size: .8rem; color: var(--c-text-muted); }
.day-body { padding: 0 var(--s-5) var(--s-5); animation: fadeIn .25s ease; }
.modify-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.3); display: flex; align-items: center; justify-content: center; z-index: 200; }
.modify-dialog { width: 400px; max-width: 90vw; }
</style>
