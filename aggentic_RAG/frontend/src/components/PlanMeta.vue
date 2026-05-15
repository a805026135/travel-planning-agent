<script setup>
const props = defineProps({
  meta: { type: Object, default: null },
});
</script>

<template>
  <div v-if="meta" class="card">
    <h3 class="section-title">行程摘要</h3>
    <ul class="meta-list">
      <li v-if="meta.origin"><strong>出发地</strong>：{{ meta.origin }}</li>
      <li v-if="meta.destination"><strong>目的地</strong>：{{ meta.destination }}</li>
      <li v-if="meta.travel_days != null"><strong>天数</strong>：{{ meta.travel_days }}</li>
      <li v-if="meta.budget != null"><strong>预算</strong>：{{ meta.budget }}</li>
      <li v-if="meta.travel_date"><strong>出发日期</strong>：{{ meta.travel_date }}</li>
      <li v-if="meta.query_mode"><strong>模式</strong>：{{ meta.query_mode === 'simple' ? '简单查询' : '完整规划' }}</li>
    </ul>
  </div>
</template>

<style scoped>
.section-title {
  margin: 0 0 0.75rem;
  font-size: 1rem;
}
.meta-list {
  margin: 0;
  padding-left: 1.1rem;
  color: var(--color-text-secondary);
}
.meta-list li {
  margin-bottom: 0.25rem;
}
</style>
