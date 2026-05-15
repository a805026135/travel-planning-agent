<template>
  <div class="spinner-wrap">
    <span class="spinner" />
    <span class="spinner-text"><slot>加载中...</slot></span>
  </div>
</template>

<style scoped>
.spinner-wrap {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}
</style>
