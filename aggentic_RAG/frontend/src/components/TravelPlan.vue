<script setup>
const props = defineProps({
  html: { type: String, default: "" },
});
</script>

<template>
  <div v-if="html" class="card">
    <h3 class="section-title">旅行方案</h3>
    <article class="markdown-body" v-html="html" />
  </div>
</template>

<style scoped>
.section-title {
  margin: 0 0 0.75rem;
  font-size: 1rem;
}
</style>
