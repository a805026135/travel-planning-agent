import { ref, onUnmounted } from "vue";
import { subscribeSSE } from "../services/api.js";

/**
 * SSE 进度流管理 composable
 */
export function useSSE() {
  const events = ref([]);
  const isRunning = ref(false);
  const error = ref("");
  const result = ref(null);
  let subscription = null;

  function start(taskId) {
    events.value = [];
    error.value = "";
    result.value = null;
    isRunning.value = true;

    subscription = subscribeSSE(taskId, {
      onProgress: (data) => {
        events.value.push({ ...data, id: events.value.length + 1 });
      },
      onComplete: (data) => {
        result.value = data;
        isRunning.value = false;
      },
      onError: (msg) => {
        error.value = msg;
        isRunning.value = false;
      },
    });
  }

  function stop() {
    if (subscription) {
      subscription.close();
      subscription = null;
    }
    isRunning.value = false;
  }

  onUnmounted(stop);

  return { events, isRunning, error, result, start, stop };
}
