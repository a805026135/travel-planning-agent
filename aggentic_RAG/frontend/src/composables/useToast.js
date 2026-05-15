import { ref } from "vue";

const toasts = ref([]);
let _id = 0;

export function useToast() {
  function add(msg, type = "info", duration = 4000) {
    const id = ++_id;
    toasts.value.push({ id, msg, type, timer: null });
    if (duration > 0) {
      const timer = setTimeout(() => remove(id), duration);
      const t = toasts.value.find((x) => x.id === id);
      if (t) t.timer = timer;
    }
  }

  function remove(id) {
    const idx = toasts.value.findIndex((x) => x.id === id);
    if (idx < 0) return;
    const t = toasts.value[idx];
    if (t.timer) clearTimeout(t.timer);
    toasts.value.splice(idx, 1);
  }

  function success(msg) { add(msg, "success"); }
  function error(msg) { add(msg, "error"); }
  function warn(msg) { add(msg, "warning"); }

  return { toasts, add, remove, success, error, warn };
}
