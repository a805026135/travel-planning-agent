<script setup>
defineProps({
  icon: { type: String, default: "📭" },
  title: { type: String, default: "暂无数据" },
  description: { type: String, default: "" },
});
</script>

<template>
  <div class="empty-state">
    <div class="empty-icon">{{ icon }}</div>
    <h3 class="empty-title">{{ title }}</h3>
    <p v-if="description" class="empty-desc">{{ description }}</p>
    <slot />
  </div>
</template>

<style scoped>
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: var(--s-12) var(--s-6); text-align: center; }
.empty-icon { font-size: 3rem; margin-bottom: var(--s-4); opacity: .8; }
.empty-title { font-size: 1.05rem; font-weight: 600; color: var(--c-text); margin-bottom: var(--s-2); }
.empty-desc { font-size: .875rem; color: var(--c-text-secondary); max-width: 320px; }
</style>
