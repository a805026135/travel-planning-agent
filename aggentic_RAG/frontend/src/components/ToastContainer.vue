<script setup>
import { useToast } from "../composables/useToast.js";

const { toasts, remove } = useToast();  // shared singleton

const icons = { success: "✅", error: "❌", warning: "⚠️", info: "ℹ️" };
</script>

<template>
  <Teleport to="body">
    <div class="toast-stack" v-if="toasts.length">
      <transition-group name="toast">
        <div v-for="t in toasts" :key="t.id" :class="['toast', `toast-${t.type}`]" @click="remove(t.id)">
          <span class="toast-icon">{{ icons[t.type] }}</span>
          <span class="toast-msg">{{ t.msg }}</span>
        </div>
      </transition-group>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-stack { position: fixed; top: 72px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; max-width: 380px; }
.toast { display: flex; align-items: center; gap: 8px; padding: 10px 16px; border-radius: 10px; font-size: .875rem; cursor: pointer; box-shadow: var(--shadow-lg); animation: slideInRight .3s ease; }
.toast-success { background: var(--c-success-bg); border: 1px solid #bbf7d0; color: var(--c-success); }
.toast-error { background: var(--c-error-bg); border: 1px solid #fecaca; color: var(--c-error); }
.toast-warning { background: var(--c-warning-bg); border: 1px solid #fde68a; color: var(--c-warning); }
.toast-info { background: var(--c-info-bg); border: 1px solid #a5f3fc; color: var(--c-info); }
.toast-enter-active { animation: slideInRight .3s ease; }
.toast-leave-active { animation: fadeIn .2s ease reverse; }
.toast-icon { font-size: 1rem; flex-shrink: 0; }
</style>
