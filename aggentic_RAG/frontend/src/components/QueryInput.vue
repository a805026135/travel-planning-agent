<script setup>
import { ref, computed, watch } from "vue";
import CityPicker from "./CityPicker.vue";

const props = defineProps({
  disabled: { type: Boolean, default: false },
  initialValues: { type: Object, default: () => ({}) },
});

const emit = defineEmits(["submit"]);

const todayStr = new Date().toISOString().split("T")[0];
const today = todayStr;

function applyInitials(iv) {
  origin.value = iv.origin || "";
  destination.value = iv.destination || "";
  startDate.value = iv.startDate || todayStr;
  endDate.value = iv.endDate || todayStr;
  budget.value = iv.budget || null;
  notes.value = iv.notes || "";
}

const origin = ref("");
const destination = ref("");
const startDate = ref(todayStr);
const endDate = ref(todayStr);
const budget = ref(null);
const notes = ref("");

// 首次加载时应用 initialValues
applyInitials(props.initialValues);

// 监听 initialValues 变化（切换到新会话时）
watch(() => props.initialValues, (iv) => {
  applyInitials(iv || {});
}, { deep: true });

const travelDays = computed(() => {
  if (!startDate.value || !endDate.value) return null;
  try {
    const s = new Date(startDate.value);
    const e = new Date(endDate.value);
    const diff = (e - s) / (1000 * 60 * 60 * 24) + 1;
    return diff > 0 ? diff : null;
  } catch { return null; }
});

function onStartChange() {
  if (endDate.value && startDate.value && endDate.value < startDate.value) {
    endDate.value = startDate.value;
  }
}
function onEndChange() {
  if (endDate.value && startDate.value && endDate.value < startDate.value) {
    startDate.value = endDate.value;
  }
}

function onSubmit() {
  emit("submit", {
    origin: origin.value.trim(),
    destination: destination.value.trim(),
    startDate: startDate.value,
    endDate: endDate.value,
    budget: budget.value ? Number(budget.value) : null,
    notes: notes.value.trim(),
  });
}
</script>

<template>
  <div class="card">
    <h3 class="form-title">出行信息</h3>

    <div class="form-grid">
      <div class="field">
        <label class="label">出发地</label>
        <CityPicker v-model="origin" placeholder="选择出发城市" :disabled="disabled" :exclude="destination" />
      </div>
      <div class="field">
        <label class="label">目的地 <span class="required">*</span></label>
        <CityPicker v-model="destination" placeholder="选择目的城市" :disabled="disabled" :exclude="origin" />
      </div>
      <div class="field">
        <label class="label" for="start">出发日期</label>
        <input id="start" v-model="startDate" type="date" class="input-text" :min="today" :disabled="disabled" @change="onStartChange" />
      </div>
      <div class="field">
        <label class="label" for="end">结束日期</label>
        <input id="end" v-model="endDate" type="date" class="input-text" :min="startDate || today" :disabled="disabled" @change="onEndChange" />
        <span v-if="travelDays" class="days-hint">{{ travelDays }} 天</span>
      </div>
      <div class="field">
        <label class="label" for="budget">预算 (元)</label>
        <input id="budget" v-model.number="budget" type="number" class="input-text" placeholder="如：3000" min="0" step="100" :disabled="disabled" />
      </div>
      <div class="field field-wide">
        <label class="label" for="notes">备注 / 偏好</label>
        <textarea id="notes" v-model="notes" class="input-text input-area" rows="2" placeholder="如：带孩子、老人同行、想省钱…" :disabled="disabled" />
      </div>
    </div>

    <div class="actions">
      <button type="button" class="btn primary" :disabled="disabled || !destination.trim()" @click="onSubmit">
        <span v-if="disabled" class="spinner" style="margin-right:6px;vertical-align:middle" />
        {{ disabled ? "规划中…" : "生成旅行方案" }}
      </button>
    </div>
    <p v-if="disabled" class="hint">调用模型与 MCP 服务需要 1～3 分钟，请勿关闭页面。</p>
  </div>
</template>

<style scoped>
.form-title { margin: 0 0 1rem; font-size: 1rem; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field-wide { grid-column: 1 / -1; }
.label { font-weight: 600; font-size: 0.85rem; }
.required { color: var(--color-error); }
.input-text {
  padding: 0.55rem 0.7rem; border: 1px solid var(--color-border); border-radius: 8px;
  font-size: 0.95rem; font-family: inherit; box-sizing: border-box; width: 100%;
}
.input-text:focus { outline: 2px solid var(--color-primary); border-color: var(--color-primary); }
.input-area { resize: vertical; line-height: 1.4; }
.days-hint { margin-top: 0.15rem; font-size: 0.8rem; color: var(--color-primary); font-weight: 600; }
.actions { margin-top: 1rem; }
</style>
