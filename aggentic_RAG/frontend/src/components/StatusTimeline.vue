<script setup>
defineProps({ events: { type: Array, default: () => [] } });

const stepIcons = {
  planner: "🤖", react_step: "🔍", r1_strategy: "🧠", r1_optimization: "⚡",
  synthesizer: "✨", train_query: "🚆", gaode_weather: "☀️", gaode_hotel_search: "🏨",
  lucky_day: "📅", flight_query: "✈️", rag_search: "📚", final_answer: "✅",
  error: "❌", agent: "🔄", profile: "👤",
};
function iconFor(step) {
  if (!step) return "⚙️";
  for (const [k, v] of Object.entries(stepIcons)) if (step.startsWith(k) || step.includes(k)) return v;
  return "⚙️";
}
function fmtTime(ts) {
  try { return new Date(ts).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }); } catch { return ""; }
}
</script>

<template>
  <div v-if="events.length" class="timeline-card card">
    <h3 class="tl-title">执行进度</h3>
    <div class="tl-track">
      <div v-for="(ev, i) in events" :key="i" class="tl-item"
        :class="{ active: ev.type === 'progress', done: ev.type === 'complete', failed: ev.type === 'error' || ev.degraded }">
        <div class="tl-dot-wrap">
          <span class="tl-dot">{{ ev.type === 'error' ? '❌' : ev.degraded ? '⚠️' : ev.type === 'complete' ? '✅' : iconFor(ev.step) }}</span>
          <div v-if="i < events.length - 1" class="tl-line" />
        </div>
        <div class="tl-body">
          <span class="tl-step">{{ ev.step || ev.type }}</span>
          <span class="tl-status">{{ ev.status }}</span>
          <span v-if="ev.degraded" class="badge badge-warning" style="margin-top:2px">降级处理</span>
          <span class="tl-time">{{ fmtTime(ev.timestamp) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline-card { margin-bottom: var(--s-4); }
.tl-title { font-size: .9rem; font-weight: 600; margin-bottom: var(--s-4); }
.tl-track { display: flex; flex-direction: column; gap: var(--s-1); }
.tl-item { display: flex; gap: var(--s-3); }
.tl-dot-wrap { display: flex; flex-direction: column; align-items: center; width: 28px; flex-shrink: 0; }
.tl-dot { font-size: 1rem; line-height: 1; }
.tl-line { width: 2px; flex: 1; min-height: 12px; background: var(--c-border); margin-top: 4px; }
.tl-body { display: flex; flex-direction: column; gap: 1px; padding-bottom: var(--s-2); }
.tl-step { font-weight: 600; font-size: .82rem; }
.tl-status { font-size: .78rem; color: var(--c-text-secondary); }
.tl-time { font-size: .7rem; color: var(--c-text-muted); }
.tl-item.failed .tl-step { color: var(--c-error); }
.tl-item.done .tl-step { color: var(--c-success); }
</style>
